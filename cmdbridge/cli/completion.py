import click
from typing import List, Optional
from ..config.path_manager import PathManager


class DynamicCompleter:
    """动态补全工具类"""
    
    @staticmethod
    def get_domains(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
        """获取领域名称列表用于补全"""
        try:
            path_manager = PathManager.get_instance()
            domains = path_manager.list_domains()
            return [domain for domain in domains if domain.startswith(incomplete)]
        except Exception:
            return []
    
    @staticmethod
    def get_program_groups(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
        """获取程序组列表用于补全"""
        try:
            path_manager = PathManager.get_instance()
            
            # 从上下文中获取领域名称
            domain = None
            if ctx.params and 'domain' in ctx.params and ctx.params['domain']:
                domain = ctx.params['domain']
            
            if domain:
                # 获取指定领域的程序组
                groups = path_manager.list_operation_groups(domain)
            else:
                # 获取所有程序组
                groups = path_manager.list_all_operation_groups()
            
            return [group for group in groups if group.startswith(incomplete)]
        except Exception:
            return []
    
    @staticmethod
    def get_source_groups(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
        """获取源程序组列表用于补全"""
        # 源程序组的补全逻辑与目标程序组相同
        return DynamicCompleter.get_program_groups(ctx, param, incomplete)


# 自定义 Click 参数类型
class DomainType(click.ParamType):
    """领域名称参数类型，支持自动补全"""
    name = "domain"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        completions = DynamicCompleter.get_domains(ctx, param, incomplete)
        # 使用兼容的方式返回补全项
        return [click.CompletionItem(domain) if hasattr(click, 'CompletionItem') 
                else click.completion.CompletionItem(domain) 
                for domain in completions]


class ProgramGroupType(click.ParamType):
    """程序组参数类型，支持自动补全"""
    name = "program_group"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        completions = DynamicCompleter.get_program_groups(ctx, param, incomplete)
        # 使用兼容的方式返回补全项
        return [click.CompletionItem(group) if hasattr(click, 'CompletionItem')
                else click.completion.CompletionItem(group)
                for group in completions]


class SourceGroupType(click.ParamType):
    """源程序组参数类型，支持自动补全"""
    name = "source_group"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        completions = DynamicCompleter.get_source_groups(ctx, param, incomplete)
        # 使用兼容的方式返回补全项
        return [click.CompletionItem(group) if hasattr(click, 'CompletionItem')
                else click.completion.CompletionItem(group)
                for group in completions]


# 创建类型实例
DOMAIN_TYPE = DomainType()
PROGRAM_GROUP_TYPE = ProgramGroupType()
SOURCE_GROUP_TYPE = SourceGroupType()