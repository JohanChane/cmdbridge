# utils/config.py

import os
from pathlib import Path
from typing import List
import tomli
import shutil


class ConfigUtils:
    """配置工具类 - 管理配置和缓存目录，包含所有功能实现"""
    
    def __init__(self, configs_dir: str = "configs", cache_dir: str = "output"):
        """
        初始化配置工具
        
        Args:
            configs_dir: 配置目录路径
            cache_dir: 缓存目录路径
        """
        self.configs_dir = Path(configs_dir)
        self.cache_dir = Path(cache_dir)
        self.cmd_mappings_cache_dir = self.cache_dir / "cmd_mappings"
    
    def refresh_cmd_mapping(self, domain_name: str = None) -> bool:
        """
        刷新命令映射缓存
        
        删除指定领域的缓存文件，然后重新生成
        
        Args:
            domain_name: 领域名称，如果为 None 则刷新所有领域
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if domain_name is None:
                # 刷新所有领域
                if self.cmd_mappings_cache_dir.exists():
                    shutil.rmtree(self.cmd_mappings_cache_dir)
                    self.cmd_mappings_cache_dir.mkdir(parents=True, exist_ok=True)
            else:
                # 刷新指定领域
                domain_cache_dir = self.cmd_mappings_cache_dir / domain_name
                if domain_cache_dir.exists():
                    shutil.rmtree(domain_cache_dir)
                    domain_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 重新生成命令映射
            # 这里需要调用 cmd_mapping_creator 的功能
            # 由于 cmd_mapping_creator 的具体实现不在当前文件中，
            # 这里返回 True 表示删除操作成功，生成操作由外部调用
            return True
            
        except Exception as e:
            print(f"刷新命令映射失败: {e}")
            return False
    
    def list_domains(self) -> List[str]:
        """
        列出所有可用的领域名称 (domains)
        
        Returns:
            List[str]: 领域名称列表，如 ["package", "process"]
        """
        domains = []
        
        if not self.configs_dir.exists():
            return domains
        
        # 查找所有 *.domain 目录
        for item in self.configs_dir.iterdir():
            if item.is_dir() and item.name.endswith('.domain'):
                domain_name = item.name[:-7]  # 移除 .domain 后缀
                domains.append(domain_name)
        
        return sorted(domains)
    
    def list_groups_in_domain(self, domain_name: str) -> List[str]:
        """
        列出指定领域中的所有程序组名称 (groups)
        
        Args:
            domain_name: 领域名称
            
        Returns:
            List[str]: 程序组名称列表，如 ["apt", "pacman", "brew"]
        """
        groups = []
        domain_dir = self.configs_dir / f"{domain_name}.domain"
        
        if not domain_dir.exists():
            return groups
        
        # 查找所有 .toml 配置文件
        for config_file in domain_dir.glob("*.toml"):
            group_name = config_file.stem
            groups.append(group_name)
        
        return sorted(groups)
    
    def _get_commands_from_cache(self, domain: str, group: str = None) -> List[str]:
        """从缓存获取命令"""
        cmds = []
        if self.cmd_mappings_cache_dir.exists():
            domain_cache_dir = self.cmd_mappings_cache_dir / domain
            mappings_file = domain_cache_dir / "cmd_mappings.toml"
            
            if mappings_file.exists():
                try:
                    with open(mappings_file, 'rb') as f:
                        mappings_data = tomli.load(f)
                    
                    if group is None:
                        # 获取所有组的命令
                        for grp in mappings_data.keys():
                            command_mappings = mappings_data[grp].get("command_mappings", [])
                            for mapping in command_mappings:
                                if "operation" in mapping:
                                    cmds.append(mapping["operation"])
                    else:
                        # 获取指定组的命令
                        if group in mappings_data:
                            command_mappings = mappings_data[group].get("command_mappings", [])
                            for mapping in command_mappings:
                                if "operation" in mapping:
                                    cmds.append(mapping["operation"])
                                
                except Exception:
                    pass
        return cmds
    
    def _get_commands_from_config(self, domain: str, group: str = None) -> List[str]:
        """从配置文件获取命令"""
        cmds = []
        if group is None:
            # 获取所有组的命令
            domain_dir = self.configs_dir / f"{domain}.domain"
            if domain_dir.exists():
                for config_file in domain_dir.glob("*.toml"):
                    try:
                        with open(config_file, 'rb') as f:
                            config_data = tomli.load(f)
                        
                        if 'operations' in config_data:
                            for operation_key in config_data['operations'].keys():
                                if '.' in operation_key:
                                    cmd_name, cmd_group = operation_key.split('.')
                                    cmds.append(cmd_name)
                                else:
                                    cmds.append(operation_key)
                                    
                    except Exception:
                        continue
        else:
            # 获取指定组的命令
            config_file = self.configs_dir / f"{domain}.domain" / f"{group}.toml"
            if config_file.exists():
                try:
                    with open(config_file, 'rb') as f:
                        config_data = tomli.load(f)
                    
                    if 'operations' in config_data:
                        for operation_key in config_data['operations'].keys():
                            if '.' in operation_key:
                                cmd_name, cmd_group = operation_key.split('.')
                                if cmd_group == group:
                                    cmds.append(cmd_name)
                            else:
                                cmds.append(operation_key)
                                
                except Exception:
                    pass
        return cmds
    
    def list_commands_in_domain_group(self, domain_name: str, group_name: str = None) -> List[str]:
        """
        列出指定领域和程序组中的所有命令名称
        
        如果 group_name 为 None，则列出整个 domain 下的所有命令
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称 (可选)
            
        Returns:
            List[str]: 命令名称列表
        """
        commands = []
        
        # 优先从缓存获取
        commands = self._get_commands_from_cache(domain_name, group_name)
        
        # 如果缓存中没有找到，回退到配置文件
        if not commands:
            commands = self._get_commands_from_config(domain_name, group_name)
        
        # 去重并排序
        return sorted(list(set(commands)))