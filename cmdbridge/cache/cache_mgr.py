"""
缓存管理器 - 统一管理命令映射和操作映射的缓存数据
"""

import os
import tomli
from typing import List, Dict, Any, Optional
from pathlib import Path
from log import debug, info, warning, error
from ..config.path_manager import PathManager


class CacheMgr:
    """缓存管理器 - 提供统一的缓存数据访问接口"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheMgr, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化缓存管理器"""
        if self._initialized:
            return
            
        self.path_manager = PathManager.get_instance()
        self._cache_data = {}
        self._loaded_domains = set()
        self._initialized = True
        
        debug("初始化 CacheMgr")
    
    @classmethod
    def get_instance(cls) -> 'CacheMgr':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
    
    def get_domains(self) -> List[str]:
        """
        获取所有可用的领域名称
        
        Returns:
            List[str]: 领域名称列表
        """
        return self.path_manager.list_domains()
    
    def get_operation_groups(self, domain: str) -> List[str]:
        """
        获取指定领域的所有操作组名称
        
        Args:
            domain: 领域名称
            
        Returns:
            List[str]: 操作组名称列表
        """
        return self.path_manager.list_operation_groups(domain)
    
    def get_all_operation_groups(self, domain: Optional[str] = None) -> List[str]:
        """
        获取所有操作组名称
        
        Args:
            domain: 可选，指定领域名称
            
        Returns:
            List[str]: 操作组名称列表
        """
        if domain:
            return self.get_operation_groups(domain)
        else:
            return self.path_manager.list_all_operation_groups()
    
    def get_cmd_mappings(self, domain: str, group_name: str) -> Dict[str, Any]:
        """
        获取指定领域和程序组的命令映射配置
        
        Args:
            domain: 领域名称
            group_name: 程序组名称
            
        Returns:
            Dict[str, Any]: 命令映射配置数据
        """
        cache_key = f"{domain}.{group_name}"
        
        if cache_key not in self._cache_data:
            cache_file = self.path_manager.get_cmd_mappings_cache_path(domain, group_name)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._cache_data[cache_key] = tomli.load(f)
                    debug(f"加载命令映射缓存: {cache_key}")
                except Exception as e:
                    error(f"加载命令映射缓存失败 {cache_file}: {e}")
                    self._cache_data[cache_key] = {}
            else:
                self._cache_data[cache_key] = {}
        
        return self._cache_data[cache_key]
    
    def get_operation_mappings(self, domain: str) -> Dict[str, Any]:
        """
        获取指定领域的操作映射配置
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, Any]: 操作映射配置数据
        """
        cache_key = f"operation_mappings.{domain}"
        
        if cache_key not in self._cache_data:
            # 加载操作到程序映射
            op_to_program_file = self.path_manager.get_operation_mappings_cache_path(domain) / "operation_to_program.toml"
            operation_to_program = {}
            
            if op_to_program_file.exists():
                try:
                    with open(op_to_program_file, 'rb') as f:
                        data = tomli.load(f)
                    operation_to_program = data.get("operation_to_program", {})
                    debug(f"加载操作到程序映射: {domain}")
                except Exception as e:
                    error(f"加载操作到程序映射失败 {op_to_program_file}: {e}")
            
            # 加载所有程序的命令格式
            command_formats = {}
            cache_dir = self.path_manager.get_operation_mappings_cache_path(domain)
            
            for command_file in cache_dir.glob("*_commands.toml"):
                program_name = command_file.stem.replace("_commands", "")
                try:
                    with open(command_file, 'rb') as f:
                        data = tomli.load(f)
                    command_formats[program_name] = data.get("commands", {})
                    debug(f"加载 {program_name} 命令格式: {len(command_formats[program_name])} 个命令")
                except Exception as e:
                    error(f"加载命令格式文件失败 {command_file}: {e}")
            
            self._cache_data[cache_key] = {
                "operation_to_program": operation_to_program,
                "command_formats": command_formats
            }
        
        return self._cache_data[cache_key]
    
    def get_operation_to_program_mapping(self, domain: str) -> Dict[str, List[str]]:
        """
        获取操作到程序的映射关系
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, List[str]]: 操作名到支持的程序列表的映射
        """
        operation_mappings = self.get_operation_mappings(domain)
        return operation_mappings.get("operation_to_program", {})
    
    def get_command_formats(self, domain: str, program_name: str) -> Dict[str, str]:
        """
        获取指定程序的命令格式
        
        Args:
            domain: 领域名称
            program_name: 程序名称
            
        Returns:
            Dict[str, str]: 操作名到命令格式的映射
        """
        operation_mappings = self.get_operation_mappings(domain)
        command_formats = operation_mappings.get("command_formats", {})
        return command_formats.get(program_name, {})
    
    def get_supported_operations(self, domain: str, program_name: str) -> List[str]:
        """
        获取程序支持的所有操作
        
        Args:
            domain: 领域名称
            program_name: 程序名称
            
        Returns:
            List[str]: 支持的操作名称列表
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        supported_ops = []
        
        for op_name, programs in operation_to_program.items():
            if program_name in programs:
                supported_ops.append(op_name)
        
        return sorted(supported_ops)
    
    def get_supported_programs(self, domain: str, operation_name: str) -> List[str]:
        """
        获取操作支持的所有程序
        
        Args:
            domain: 领域名称
            operation_name: 操作名称
            
        Returns:
            List[str]: 支持的程序名称列表
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        return operation_to_program.get(operation_name, [])
    
    def is_operation_supported(self, domain: str, operation_name: str, program_name: str) -> bool:
        """
        检查操作是否支持指定程序
        
        Args:
            domain: 领域名称
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            bool: 是否支持
        """
        supported_programs = self.get_supported_programs(domain, operation_name)
        return program_name in supported_programs
    
    def get_command_format(self, domain: str, operation_name: str, program_name: str) -> Optional[str]:
        """
        获取指定操作和程序的命令格式
        
        Args:
            domain: 领域名称
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            Optional[str]: 命令格式字符串，如果不存在则返回 None
        """
        command_formats = self.get_command_formats(domain, program_name)
        return command_formats.get(operation_name)
    
    def get_final_command_format(self, domain: str, operation_name: str, program_name: str) -> Optional[str]:
        """
        获取最终命令格式（final_cmd_format）
        
        Args:
            domain: 领域名称
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            Optional[str]: final_cmd_format 字符串，如果不存在则返回 None
        """
        command_formats = self.get_command_formats(domain, program_name)
        return command_formats.get(f"{operation_name}_final")
    
    def get_all_operations(self, domain: str) -> List[str]:
        """
        获取所有可用的操作名称
        
        Args:
            domain: 领域名称
            
        Returns:
            List[str]: 所有操作名称列表
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        return sorted(list(operation_to_program.keys()))
    
    def get_all_programs(self, domain: str) -> List[str]:
        """
        获取所有可用的程序名称
        
        Args:
            domain: 领域名称
            
        Returns:
            List[str]: 所有程序名称列表
        """
        operation_mappings = self.get_operation_mappings(domain)
        command_formats = operation_mappings.get("command_formats", {})
        return sorted(list(command_formats.keys()))
    
    def get_operation_parameters(self, domain: str, operation_name: str, program_name: str) -> List[str]:
        """
        获取操作的参数列表
        
        Args:
            domain: 领域名称
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            List[str]: 参数名称列表
        """
        cmd_format = self.get_command_format(domain, operation_name, program_name)
        if not cmd_format:
            return []
        
        # 从命令格式中提取参数
        import re
        params = re.findall(r'\{(\w+)\}', cmd_format)
        return params
    
    def refresh_cache(self, domain: Optional[str] = None) -> bool:
        """
        刷新缓存数据
        
        Args:
            domain: 可选，指定领域名称，如果为 None 则刷新所有领域
            
        Returns:
            bool: 刷新是否成功
        """
        try:
            if domain:
                # 刷新指定领域的缓存
                if domain in self._cache_data:
                    del self._cache_data[domain]
                if f"operation_mappings.{domain}" in self._cache_data:
                    del self._cache_data[f"operation_mappings.{domain}"]
                debug(f"已刷新 {domain} 领域的缓存")
            else:
                # 刷新所有缓存
                self._cache_data.clear()
                debug("已刷新所有缓存数据")
            
            return True
        except Exception as e:
            error(f"刷新缓存失败: {e}")
            return False
    
    def cache_exists(self, domain: str, cache_type: str = "cmd_mappings") -> bool:
        """
        检查缓存是否存在
        
        Args:
            domain: 领域名称
            cache_type: 缓存类型，'cmd_mappings' 或 'operation_mappings'
            
        Returns:
            bool: 缓存是否存在
        """
        if cache_type == "cmd_mappings":
            # 检查是否有任何命令映射缓存文件
            cache_dir = self.path_manager.get_cmd_mappings_cache_path(domain)
            return cache_dir.exists() and any(cache_dir.glob("*.toml"))
        elif cache_type == "operation_mappings":
            # 检查操作映射缓存文件
            cache_dir = self.path_manager.get_operation_mappings_cache_path(domain)
            op_to_program_file = cache_dir / "operation_to_program.toml"
            return op_to_program_file.exists()
        else:
            return False
    
    def get_cache_stats(self, domain: str) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        stats = {
            "domain": domain,
            "cmd_mappings_exists": self.cache_exists(domain, "cmd_mappings"),
            "operation_mappings_exists": self.cache_exists(domain, "operation_mappings"),
            "operation_groups": [],
            "operations_count": 0,
            "programs_count": 0
        }
        
        if self.cache_exists(domain, "cmd_mappings"):
            groups = self.get_operation_groups(domain)
            stats["operation_groups"] = groups
            stats["groups_count"] = len(groups)
        
        if self.cache_exists(domain, "operation_mappings"):
            operations = self.get_all_operations(domain)
            programs = self.get_all_programs(domain)
            stats["operations_count"] = len(operations)
            stats["programs_count"] = len(programs)
        
        return stats

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
            
            debug(f"合并了 {success_count}/{len(domains)} 个领域配置")
            return success_count > 0
            
        except Exception as e:
            error(f"合并领域配置失败: {e}")
            return False