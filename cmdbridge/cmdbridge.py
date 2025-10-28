# cmdbridge/cmdbridge.py

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import tomli

from .config.path_manager import PathManager
from cmdbridge.cache.cache_mgr import CacheMgr
from cmdbridge.config.config_mgr import ConfigMgr
from .cache.cmd_mapping_mgr import CmdMappingMgr
from .core.cmd_mapping import CmdMapping
from .core.operation_mapping import OperationMapping
from log import debug, info, warning, error


class CmdBridge:
    """CmdBridge 核心功能类"""
    
    def __init__(self):
        # 初始化路径管理器
        self.path_manager = PathManager()
        
        # 初始化配置工具
        self.cache_mgr = CacheMgr.get_instance()
        self.config_mgr = ConfigMgr()

        # 初始化命令映射器
        self.command_mapper = CmdMapping({})
        
        # 初始化操作映射器 - 简化构造函数
        self.operation_mapper = OperationMapping()
        
        # 初始化映射配置缓存
        self._mapping_config_cache = {}
        
        # 加载全局配置
        self.global_config = self._load_global_config()

    def _load_global_config(self) -> dict:
        """加载全局配置"""
        config_file = self.path_manager.get_global_config_path()
        if config_file.exists():
            try:
                with open(config_file, 'rb') as f:
                    return tomli.load(f)
            except Exception as e:
                warning(f"无法读取全局配置文件: {e}")
        return {}

    def _get_default_domain(self) -> str:
        """获取默认领域"""
        return self.global_config.get('global_settings', {}).get('default_operation_domain', 'package')
    
    def _get_default_group(self) -> str:
        """获取默认程序组"""
        return self.global_config.get('global_settings', {}).get('default_operation_group', 'pacman')
    
    def _auto_detect_source_group(self, command: str, domain: str) -> Optional[str]:
        """自动识别源命令所属的组"""
        if not command.strip():
            return None
        
        # 获取命令的第一个单词（程序名）
        program_name = command.strip().split()[0]
        debug(f"自动识别源操作组，命令: '{command}', 程序名: '{program_name}', 领域: '{domain}'")
        
        # 使用 cmd_to_operation.toml 查找程序所属的操作组
        cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path(domain)
        if not cmd_to_operation_file.exists():
            debug(f"cmd_to_operation 文件不存在: {cmd_to_operation_file}")
            return None
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            # 在所有操作组中查找包含该程序的操作组
            for op_group, group_data in cmd_to_operation_data.get("cmd_to_operation", {}).items():
                if program_name in group_data.get("programs", []):
                    debug(f"自动识别成功: 程序 '{program_name}' 属于操作组 '{op_group}'")
                    return op_group
                    
            debug(f"自动识别失败: 未找到程序 '{program_name}' 所属的操作组")
            return None
            
        except Exception as e:
            error(f"读取 cmd_to_operation 文件失败: {e}")
            return None

    def _get_mapping_config(self, domain: str, group_name: str) -> Dict[str, Any]:
        """获取指定领域和程序组的映射配置"""
        cache_key = f"{domain}.{group_name}"
        if cache_key not in self._mapping_config_cache:
            # 从缓存文件加载该程序组的映射配置
            cache_file = self.path_manager.get_cmd_mappings_domain_dir_of_cache(domain) / f"{group_name}.toml"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._mapping_config_cache[cache_key] = tomli.load(f)
                except Exception as e:
                    warning(f"加载 {cache_key} 映射配置失败: {e}")
                    self._mapping_config_cache[cache_key] = {}
            else:
                self._mapping_config_cache[cache_key] = {}
        
        return self._mapping_config_cache[cache_key]

    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                    dest_group: Optional[str], command_args: List[str]) -> Optional[str]:
        """映射完整命令"""
        try:
            # 将参数列表合并为命令字符串
            command_str = ' '.join(command_args)
            if not command_str:
                return None
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 自动识别源组（如果未指定）
            if not src_group:
                src_group = self._auto_detect_source_group(command_str, domain)
                if not src_group:
                    return None
            
            # 从命令中提取实际程序名
            actual_program_name = command_args[0] if command_args else None
            if not actual_program_name:
                return None
            
            # 🔧 修复：使用跨操作组查找加载映射配置
            self.command_mapper = CmdMapping.load_from_cache(domain, actual_program_name)
            
            # 加载源程序的解析器配置
            parser_config_file = self.path_manager.get_program_parser_config_path(actual_program_name)
            if not parser_config_file.exists():
                error(f"找不到 {actual_program_name} 的解析器配置")
                return None
            
            from parsers.config_loader import load_parser_config_from_file
            source_parser_config = load_parser_config_from_file(str(parser_config_file), actual_program_name)
            
            # 使用正确的 map_to_operation 方法
            operation_result = self.command_mapper.map_to_operation(
                source_cmdline=command_args,
                source_parser_config=source_parser_config,
                dst_operation_group=dest_group
            )
            
            if not operation_result:
                return None
            
            # 使用 OperationMapping 生成最终命令
            result_cmd = self.operation_mapper.generate_command(
                operation_name=operation_result["operation_name"],
                params=operation_result["params"],
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group,
            )
            
            return result_cmd
            
        except Exception as e:
            error(f"命令映射失败: {e}")
            return None
        
    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> Optional[str]:
        """映射操作和参数"""
        try:
            # 将参数列表合并为操作字符串
            operation_str = ' '.join(operation_args)
            if not operation_str:
                return None
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 解析操作字符串，提取操作名和参数
            parts = operation_str.split()
            if not parts:
                return None
            
            # 第一个参数是操作名，其余是包名
            operation_name = parts[0]
            params = {}
            
            # 简单参数解析：假设后续参数都是包名
            if len(parts) > 1:
                params = {"pkgs": " ".join(parts[1:])}
            
            # 调用 OperationMapping 生成命令
            result = self.operation_mapper.generate_command(
                operation_name=operation_name,
                params=params,
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group
            )
            
            return result
                
        except Exception as e:
            error(f"操作映射失败: {e}")
            return None

    def refresh_cmd_mappings(self) -> bool:
        """刷新所有命令映射缓存"""
        try:
            success = self.cache_mgr.remove_cmd_mapping()
            if success:
                # 先合并所有领域配置到缓存目录
                info("合并领域配置到缓存...")
                merge_success = self.cache_mgr.merge_all_domain_configs()
                if not merge_success:
                    warning("合并领域配置失败")
                
                # 为每个领域生成映射数据
                domains = self.path_manager.get_domains_from_config()
                for domain in domains:
                    # 确保缓存目录存在
                    self.path_manager.get_cmd_mappings_domain_of_cache(domain).mkdir(parents=True, exist_ok=True)
                    self.path_manager.get_operation_mappings_domain_dir_of_cache(domain).mkdir(parents=True, exist_ok=True)
                    
                    # 获取领域配置目录
                    domain_config_dir = self.path_manager.get_operation_domain_dir_of_config(domain)
                    parser_configs_dir = self.path_manager.program_parser_config_dir
                    
                    if domain_config_dir.exists() and parser_configs_dir.exists():
                        # 获取该领域的所有程序组
                        groups = self.path_manager.get_operation_groups_from_config(domain)
                        
                        for group_name in groups:
                            try:
                                # 为每个程序组创建 CmdMappingCreator 实例
                                group_creator = CmdMappingMgr(domain, group_name)
                                
                                # 生成映射数据
                                mapping_data = group_creator.create_mappings()
                                
                                if mapping_data:  # 如果有映射数据才写入
                                    # 写入映射文件
                                    group_creator.write_to()
                                    info(f"✅ 已生成 {domain}.{group_name} 的命令映射")
                                else:
                                    warning(f"⚠️ {domain}.{group_name} 没有生成映射数据")
                                    
                            except Exception as e:
                                error(f"❌ 生成 {domain}.{group_name} 的命令映射失败: {e}")
                                continue
                        
                        # 使用 OperationMappingCreator 生成操作映射文件
                        from .cache.operation_mapping_mgr import create_operation_mappings_for_domain
                        op_mapping_success = create_operation_mappings_for_domain(domain)
                        if op_mapping_success:
                            info(f"✅ 已完成 {domain} 领域的操作映射生成")
                        else:
                            warning(f"⚠️ {domain} 领域的操作映射生成失败")
                        
                        info(f"✅ 已完成 {domain} 领域所有程序组的命令映射生成")
                    else:
                        warning(f"⚠️  跳过 {domain} 领域：配置目录不存在")
                
                return True
            return False
        except Exception as e:
            error(f"刷新命令映射失败: {e}")
            return False

    def init_config(self) -> bool:
        """初始化用户配置"""
        return self.config_mgr.init_config()