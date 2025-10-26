import sys
from typing import List, Optional
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from cmdbridge.config.path_manager import PathManager
from cmdbridge.cache.cache_mgr import CacheMgr
from log import debug, warning, error


class CompletorHelper:
    """提供动态补全数据，从缓存中获取实时配置"""

    @staticmethod
    def get_domains() -> List[str]:
        """从配置中返回支持的领域"""
        try:
            path_manager = PathManager.get_instance()
            domains = path_manager.get_domains_from_config()
            debug(f"获取领域列表: {domains}")
            return domains
        except Exception as e:
            warning(f"获取领域列表失败: {e}")
            return []  # 默认回退值

    @staticmethod
    def get_operation_groups(domain: str) -> List[str]:
        """根据领域从配置中返回程序组"""
        try:
            path_manager = PathManager.get_instance()
            groups = path_manager.get_operation_groups_from_config(domain)
            debug(f"获取领域 '{domain}' 的程序组: {groups}")
            return groups
        except Exception as e:
            warning(f"获取领域 '{domain}' 的程序组失败: {e}")
            return []

    @staticmethod
    def get_all_operation_groups() -> List[str]:
        """返回所有支持的程序组"""
        try:
            path_manager = PathManager.get_instance()
            all_groups = path_manager.get_all_operation_groups_from_config()
            debug(f"获取所有程序组: {all_groups}")
            return all_groups
        except Exception as e:
            warning(f"获取所有程序组失败: {e}")
            return []

    @staticmethod
    def get_commands(domain: Optional[str], source_group: str) -> List[str]:
        """从缓存中获取指定领域和源程序组的命令列表"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            # 如果没有指定领域，尝试自动检测
            if not domain:
                domains = CompletorHelper.get_domains()
                for dom in domains:
                    if source_group in CompletorHelper.get_operation_groups(dom):
                        domain = dom
                        break
            
            if not domain:
                warning(f"无法确定源程序组 '{source_group}' 所属的领域")
                return []
            
            # 从缓存中获取命令映射
            cmd_mappings = cache_mgr.get_cmd_mappings(domain, source_group)
            if not cmd_mappings or source_group not in cmd_mappings:
                debug(f"未找到 {domain}.{source_group} 的命令映射")
                return []
            
            commands = []
            for mapping in cmd_mappings[source_group].get("command_mappings", []):
                cmd_format = mapping.get("cmd_format", "")
                if cmd_format:
                    commands.append(cmd_format)
            
            debug(f"获取 {domain}.{source_group} 的命令列表: {len(commands)} 个命令")
            return commands
            
        except Exception as e:
            warning(f"获取命令列表失败 (domain={domain}, group={source_group}): {e}")
            return []

    @staticmethod
    def get_all_commands(domain: Optional[str]) -> List[str]:
        """获取指定领域的所有命令"""
        try:
            if not domain:
                # 如果没有指定领域，获取所有领域的命令
                all_commands = []
                domains = CompletorHelper.get_domains()
                for dom in domains:
                    groups = CompletorHelper.get_operation_groups(dom)
                    for group in groups:
                        commands = CompletorHelper.get_commands(dom, group)
                        all_commands.extend(commands)
                return list(set(all_commands))
            else:
                # 获取指定领域的所有命令
                all_commands = []
                groups = CompletorHelper.get_operation_groups(domain)
                for group in groups:
                    commands = CompletorHelper.get_commands(domain, group)
                    all_commands.extend(commands)
                return list(set(all_commands))
                
        except Exception as e:
            warning(f"获取所有命令失败 (domain={domain}): {e}")
            return []

    @staticmethod
    def get_operation_names(domain: Optional[str], dest_group: Optional[str]) -> List[str]:
        """从缓存中获取操作名称列表"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            if domain and dest_group:
                # 获取特定程序组支持的操作
                supported_ops = cache_mgr.get_supported_operations(domain, dest_group)
                debug(f"获取 {domain}.{dest_group} 支持的操作: {supported_ops}")
                return supported_ops
            elif domain:
                # 获取指定领域的所有操作
                all_ops = cache_mgr.get_all_operations(domain)
                debug(f"获取领域 '{domain}' 的所有操作: {all_ops}")
                return all_ops
            else:
                # 获取所有操作
                all_ops = []
                domains = CompletorHelper.get_domains()
                for dom in domains:
                    ops = cache_mgr.get_all_operations(dom)
                    all_ops.extend(ops)
                return list(set(all_ops))
                
        except Exception as e:
            warning(f"获取操作名称失败 (domain={domain}, group={dest_group}): {e}")
            return []

    @staticmethod
    def get_all_operation_names(domain: Optional[str] = None) -> List[str]:
        """获取所有操作名称（兼容性方法）"""
        return CompletorHelper.get_operation_names(domain, None)

    @staticmethod
    def get_operation_with_params(domain: str, operation_name: str, dest_group: str) -> str:
        """获取带参数信息的操作字符串"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            # 获取操作的参数
            params = cache_mgr.get_operation_parameters(domain, operation_name, dest_group)
            
            if params:
                # 格式化显示：操作名 {参数1} {参数2} ...
                params_display = " ".join([f"{{{param}}}" for param in params])
                return f"{operation_name} {params_display}"
            else:
                # 没有参数的操作
                return operation_name
                
        except Exception as e:
            warning(f"获取带参数的操作信息失败: {e}")
            return operation_name