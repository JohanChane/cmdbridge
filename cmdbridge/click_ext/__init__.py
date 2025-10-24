"""Click 扩展模块，提供动态补全支持"""

import click
from typing import List, Optional, Any, Callable
from ..config.path_manager import PathManager


class ContextAwareChoice(click.Choice):
    """上下文感知的动态选项类型"""
    
    def __init__(self, get_choices_callback: Callable[[Optional[str]], List[str]]):
        self.get_choices_callback = get_choices_callback
        super().__init__([])
    
    def get_choices(self, ctx: click.Context) -> List[str]:
        """根据上下文动态获取选项列表"""
        try:
            # 从上下文中获取 domain 参数
            domain = None
            if ctx and ctx.params:
                domain = ctx.params.get('domain')
            
            return self.get_choices_callback(domain)
        except Exception:
            return []
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        # 在转换时更新选项列表
        if ctx:
            self.choices = self.get_choices(ctx)
        return super().convert(value, param, ctx)
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        # 在补全时更新选项列表
        self.choices = self.get_choices(ctx)
        return super().shell_complete(ctx, param, incomplete)


class Completer:
    """补全工具类"""
    
    @staticmethod
    def get_domains(domain: Optional[str] = None) -> List[str]:
        """获取领域名称列表"""
        try:
            path_manager = PathManager.get_instance()
            domains = path_manager.list_domains()
            # 如果指定了 domain，只返回匹配的（用于过滤）
            if domain:
                return [d for d in domains if d == domain]
            return domains
        except Exception:
            return []
    
    @staticmethod
    def get_program_groups(domain: Optional[str] = None) -> List[str]:
        """根据领域获取程序组列表"""
        try:
            path_manager = PathManager.get_instance()
            if domain:
                # 获取指定领域的程序组
                return path_manager.list_operation_groups(domain)
            else:
                # 获取所有程序组
                return path_manager.list_all_operation_groups()
        except Exception:
            return []
    
    @staticmethod
    def get_domain_type() -> ContextAwareChoice:
        """创建领域类型"""
        return ContextAwareChoice(Completer.get_domains)
    
    @staticmethod
    def get_program_group_type() -> ContextAwareChoice:
        """创建程序组类型（用于 -t 选项）"""
        return ContextAwareChoice(Completer.get_program_groups)
    
    @staticmethod
    def get_source_group_type() -> ContextAwareChoice:
        """创建源程序组类型（用于 -s 选项）"""
        return ContextAwareChoice(Completer.get_program_groups)


# 创建全局实例
completer = Completer()