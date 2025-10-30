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


class CommonCompletorHelper:
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
            # 如果没有指定领域，尝试自动检测
            if not domain:
                domains = CommonCompletorHelper.get_domains()
                for dom in domains:
                    if source_group in CommonCompletorHelper.get_operation_groups(dom):
                        domain = dom
                        break
            
            if not domain:
                warning(f"无法确定源程序组 '{source_group}' 所属的领域")
                return []
            
            # 使用新的缓存结构获取命令
            path_manager = PathManager.get_instance()
            cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain)
            
            if not cmd_to_operation_file.exists():
                return []
            
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            # 获取该操作组的所有程序
            programs = cmd_to_operation_data.get("cmd_to_operation", {}).get(source_group, {}).get("programs", [])
            if not programs:
                return []
            
            # 收集所有程序的命令格式
            commands = []
            for program_name in programs:
                program_file = path_manager.get_cmd_mappings_group_program_path_of_cache(
                    domain, source_group, program_name
                )
                
                if program_file.exists():
                    try:
                        with open(program_file, 'rb') as f:
                            program_data = tomli.load(f)
                        
                        # 提取该程序的所有命令格式
                        for mapping in program_data.get("command_mappings", []):
                            cmd_format = mapping.get("cmd_format", "")
                            if cmd_format:
                                commands.append(cmd_format)
                                
                    except Exception as e:
                        warning(f"读取程序命令文件失败 {program_file}: {e}")
            
            return commands
            
        except Exception as e:
            warning(f"获取命令列表失败 (domain={domain}, group={source_group}): {e}")
            return []
        
    @staticmethod
    def get_all_commands(domain: Optional[str]) -> List[str]:
        """获取指定领域的所有命令"""
        try:
            all_commands = []
            
            # 确定要处理的领域列表
            domains = [domain] if domain else CommonCompletorHelper.get_domains()
            
            # 收集所有领域的命令
            for dom in domains:
                groups = CommonCompletorHelper.get_operation_groups(dom)
                for group in groups:
                    commands = CommonCompletorHelper.get_commands(dom, group)
                    all_commands.extend(commands)
            
            # 去重并返回
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
                domains = CommonCompletorHelper.get_domains()
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
        return CommonCompletorHelper.get_operation_names(domain, None)

    @staticmethod
    def get_operation_with_params(domain: str, operation_name: str, dest_group: str) -> str:
        """获取带参数信息的操作字符串"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            # 直接调用 cache_mgr 的方法，让它处理 domain 为 None 的情况
            params = cache_mgr.get_operation_parameters(domain, operation_name, dest_group)
            
            if params:
                # 格式化显示：操作名 {参数1} {参数2} ...
                params_display = " ".join([f"{{{param}}}" for param in params])
                return f"{operation_name} {params_display}"
            else:
                # 没有参数的操作
                return operation_name
                
        except Exception as e:
            # 如果出错，返回原始操作名
            warning(f"获取操作参数失败: {e}")
            return operation_name
      
    @staticmethod
    def get_domain_for_group(group_name: str) -> Optional[str]:
        return PathManager.get_instance().get_domain_for_group(group_name)