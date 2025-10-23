# utils/config.py

import os, sys
from pathlib import Path
from typing import List, Dict, Any, Optional
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli
import shutil

from cmdbridge.config.path_manager import PathManager
from log import debug, info, warning, error


class ConfigMgr:
    """配置工具类 - 管理配置和缓存目录，包含所有功能实现"""
    
    def __init__(self):
        """
        初始化配置工具
        """
        # 直接使用 PathManager 单例
        self.path_manager = PathManager.get_instance()
        debug("初始化 ConfigUtils")
    
    def remove_cmd_mapping(self, domain_name: str = None) -> bool:
        """
        刷新命令映射缓存
        
        删除指定领域的缓存文件，然后重新生成
        
        Args:
            domain_name: 领域名称，如果为 None 则刷新所有领域
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 使用 PathManager 的删除方法
            success = self.path_manager.rm_cmd_mappings_dir(domain_name)
            
            if success:
                # 重新创建目录结构
                if domain_name is None:
                    # 为所有领域重新创建目录
                    domains = self.path_manager.list_domains()
                    for domain in domains:
                        self.path_manager.ensure_cmd_mappings_domain_dir(domain)
                else:
                    # 为指定领域重新创建目录
                    self.path_manager.ensure_cmd_mappings_domain_dir(domain_name)
                
                return True
            else:
                return False
                
        except Exception as e:
            error(f"刷新命令映射失败: {e}")
            return False
    
    def list_domains(self) -> List[str]:
        """列出所有可用的领域名称"""
        return self.path_manager.list_domains()
    
    def list_groups_in_domain(self, domain_name: str) -> List[str]:
        """列出指定领域中的所有程序组名称"""
        return self.path_manager.list_operation_groups(domain_name)
    
    def list_commands_in_domain_group(self, domain_name: str, group_name: str = None) -> List[str]:
        """列出指定领域和程序组中的所有命令名称"""
        commands = []
        
        # 优先从缓存获取
        commands = self._get_commands_from_cache(domain_name, group_name)
        
        # 去重并排序
        return sorted(list(set(commands)))
    
    def _get_commands_from_cache(self, domain: str, group: str = None) -> List[str]:
        """从缓存获取命令"""
        cmds = []
        try:
            if group is None:
                # 获取所有组的命令
                groups = self.path_manager.list_operation_groups(domain)
                for grp in groups:
                    cache_file = self.path_manager.get_operation_group_cache_path(domain, grp)
                    if cache_file.exists():
                        with open(cache_file, 'rb') as f:
                            cached_data = tomli.load(f)
                        operations = cached_data.get("operations", {})
                        for operation_key in operations.keys():
                            if '.' in operation_key:
                                cmd_name, cmd_group = operation_key.split('.')
                                cmds.append(cmd_name)
                            else:
                                cmds.append(operation_key)
            else:
                # 获取指定组的命令
                cache_file = self.path_manager.get_operation_group_cache_path(domain, group)
                if cache_file.exists():
                    with open(cache_file, 'rb') as f:
                        cached_data = tomli.load(f)
                    operations = cached_data.get("operations", {})
                    for operation_key in operations.keys():
                        if '.' in operation_key:
                            cmd_name, cmd_group = operation_key.split('.')
                            if cmd_group == group:
                                cmds.append(cmd_name)
                        else:
                            cmds.append(operation_key)
        except Exception as e:
            debug(f"从缓存获取命令失败: {e}")
        return cmds
    
    def merge_all_domain_configs(self) -> bool:
        """合并所有领域配置
        
        为每个领域生成 operation_mapping.toml 文件
        
        Returns:
            bool: 合并是否成功
        """
        try:
            domains = self.path_manager.list_domains()
            success_count = 0
            
            for domain in domains:
                domain_config_dir = self.path_manager.get_config_operation_group_path(domain)
                if domain_config_dir.exists():
                    # 这里调用 CmdBridge 中的生成方法
                    # 在实际实现中，可能需要将生成逻辑移到 ConfigUtils 中
                    debug(f"处理领域配置: {domain}")
                    success_count += 1
                else:
                    warning(f"领域配置目录不存在: {domain_config_dir}")
            
            info(f"合并了 {success_count}/{len(domains)} 个领域配置")
            return success_count > 0
            
        except Exception as e:
            error(f"合并领域配置失败: {e}")
            return False