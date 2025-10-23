# utils/completion.py

from typing import List
from ..cmdbridge.config.config_mgr import ConfigMgr
from cmdbridge.config.path_manager import PathManager
from log import debug


class CompletionUtils:
    """补全工具类 - 包装 ConfigUtils 的补全功能"""
    
    def __init__(self):
        """
        初始化补全工具
        """
        # 直接使用 PathManager 单例
        self.path_manager = PathManager.get_instance()
        self.config_utils = ConfigMgr()
        debug("初始化 CompletionUtils")
    
    def list_domains(self) -> List[str]:
        """列出所有领域名称"""
        return self.path_manager.list_domains()
    
    def list_groups_in_domain(self, domain_name: str) -> List[str]:
        """列出指定领域中的所有程序组名称"""
        return self.path_manager.list_operation_groups(domain_name)
    
    def list_all_operation_groups(self) -> List[str]:
        """列出所有操作组名称"""
        return self.path_manager.list_all_operation_groups()
    
    def list_program_parser_configs(self) -> List[str]:
        """列出所有程序解析器配置"""
        return self.path_manager.list_program_parser_configs()
    
    def list_commands_in_domain_group(self, domain_name: str, group_name: str = None) -> List[str]:
        """列出指定领域和程序组中的所有命令名称"""
        return self.config_utils.list_commands_in_domain_group(domain_name, group_name)
    
    def get_available_completions(self, context: str = None) -> List[str]:
        """
        根据上下文获取可用的补全选项
        
        Args:
            context: 上下文信息，如 "package.apt." 或 "process."
            
        Returns:
            List[str]: 可用的补全选项列表
        """
        if context is None:
            # 返回所有领域
            domains = self.list_domains()
            debug(f"无上下文，返回所有领域: {domains}")
            return domains
        
        if '.' in context:
            parts = context.split('.')
            if len(parts) == 2 and parts[1] == '':
                # 格式: "package." - 返回该领域的所有操作组
                domain = parts[0]
                groups = self.list_groups_in_domain(domain)
                debug(f"上下文 '{context}'，返回领域 '{domain}' 的操作组: {groups}")
                return groups
            elif len(parts) == 3 and parts[2] == '':
                # 格式: "package.apt." - 返回该操作组的所有命令
                domain = parts[0]
                group = parts[1]
                commands = self.list_commands_in_domain_group(domain, group)
                debug(f"上下文 '{context}'，返回操作组 '{domain}.{group}' 的命令: {commands}")
                return commands
        
        # 默认返回所有领域
        domains = self.list_domains()
        debug(f"未知上下文 '{context}'，返回所有领域: {domains}")
        return domains
    
    def validate_domain(self, domain_name: str) -> bool:
        """验证领域名称是否有效"""
        valid = self.path_manager.domain_exists(domain_name)
        debug(f"验证领域 '{domain_name}': {valid}")
        return valid
    
    def validate_operation_group(self, domain_name: str, group_name: str) -> bool:
        """验证操作组是否有效"""
        valid = self.path_manager.operation_group_exists(domain_name, group_name)
        debug(f"验证操作组 '{domain_name}.{group_name}': {valid}")
        return valid
    
    def validate_program_parser(self, program_name: str) -> bool:
        """验证程序解析器配置是否存在"""
        valid = self.path_manager.program_parser_config_exists(program_name)
        debug(f"验证程序解析器 '{program_name}': {valid}")
        return valid
    
    def get_domain_completions(self) -> List[str]:
        """获取领域补全列表"""
        domains = self.list_domains()
        debug(f"领域补全列表: {domains}")
        return domains
    
    def get_group_completions(self, domain: str) -> List[str]:
        """获取指定领域的操作组补全列表"""
        groups = self.list_groups_in_domain(domain)
        debug(f"领域 '{domain}' 的操作组补全列表: {groups}")
        return groups
    
    def get_command_completions(self, domain: str, group: str) -> List[str]:
        """获取指定领域和操作组的命令补全列表"""
        commands = self.list_commands_in_domain_group(domain, group)
        debug(f"操作组 '{domain}.{group}' 的命令补全列表: {commands}")
        return commands
    
    def get_program_completions(self) -> List[str]:
        """获取程序解析器补全列表"""
        programs = self.list_program_parser_configs()
        debug(f"程序解析器补全列表: {programs}")
        return programs


# 便捷函数
def create_completion_utils() -> CompletionUtils:
    """
    创建补全工具实例
    
    Returns:
        CompletionUtils: 补全工具实例
    """
    return CompletionUtils()


def get_completions(context: str = None) -> List[str]:
    """
    便捷函数：根据上下文获取补全选项
    
    Args:
        context: 上下文信息
        
    Returns:
        List[str]: 补全选项列表
    """
    utils = CompletionUtils()
    return utils.get_available_completions(context)