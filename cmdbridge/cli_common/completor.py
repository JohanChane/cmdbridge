import sys
from typing import Optional
import click
from .completor_helper import CommonCompletorHelper
from log import get_out, set_out
from cmdbridge.config.path_manager import PathManager
from .cli_helper import CommonCliHelper

def completion_handler(func):
    """装饰器：在补全模式下正确处理输出流"""
    def wrapper(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        original_out = get_out()
        if bool(ctx and ctx.resilient_parsing):
            set_out(sys.stderr)
        try:
            return func(self, ctx, param, incomplete)
        finally:
            set_out(original_out)
    return wrapper


class DomainType(click.ParamType):
    name = "domain"

    @completion_handler
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        domains = CommonCompletorHelper.get_domains()
        return [
            click.shell_completion.CompletionItem(d)
            for d in domains
            if d.startswith(incomplete)
        ]


class SourceGroupType(click.ParamType):
    name = "source_group"
    
    @completion_handler
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        groups = []

        domain = ctx.params.get("domain")
        if domain:
            groups = CommonCompletorHelper.get_operation_groups(domain)
        else:
            groups = CommonCompletorHelper.get_all_operation_groups()

        return [
            click.shell_completion.CompletionItem(g)
            for g in groups
            if g.startswith(incomplete)
        ]


class DestGroupType(click.ParamType):
    name = "dest_group"
    
    @completion_handler
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        groups = []

        domain = ctx.params.get("domain")
        if domain:
            groups = CommonCompletorHelper.get_operation_groups(domain)
        else:
            groups = CommonCompletorHelper.get_all_operation_groups()
            
        return [
            click.shell_completion.CompletionItem(g)
            for g in groups
            if g.startswith(incomplete)
        ]
    
class CommandType(click.ParamType):
    name = "command"
    
    @completion_handler
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        commands = []

        dest_group = ctx.params.get("dest_group")
        source_group = ctx.params.get("source_group")
        domain = ctx.params.get("domain")

        if dest_group and not domain:
            domain = CommonCompletorHelper.get_domain_for_group(dest_group)

        if source_group:
            commands = CommonCompletorHelper.get_commands(domain, source_group)
        else:
            commands = CommonCompletorHelper.get_all_commands(domain)

        return [
            click.shell_completion.CompletionItem(g)
            for g in commands
            if g.startswith(incomplete)
        ]
    
class OperationType(click.ParamType):
    name = "operation"
    
    @completion_handler
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        operations = []

        dest_group = ctx.params.get("dest_group")
        domain = ctx.params.get("domain")

        if dest_group and not domain:
            domain = CommonCompletorHelper.get_domain_for_group(dest_group)

        if dest_group:
            operations = CommonCompletorHelper.get_operation_names(domain, dest_group)
        else:
            operations = CommonCompletorHelper.get_all_operation_names(domain)

        # 获取带参数的操作字符串
        operation_items = []
        for op in operations:
            # 无论是否指定 domain，都尝试获取带参数的操作字符串
            op_with_params = self._get_operation_with_params(domain, op, dest_group)
            operation_items.append(
                click.shell_completion.CompletionItem(op_with_params)
            )

        return [
            item for item in operation_items
            if item.value.startswith(incomplete)
        ]
    
    def _get_operation_with_params(self, domain: Optional[str], operation_name: str, dest_group: Optional[str]) -> str:
        """获取带参数的操作字符串"""
        # 如果没有指定 domain，尝试获取默认的 domain
        actual_domain = domain
        if not actual_domain:
            path_manager = PathManager.get_instance()
            domains = path_manager.get_domains_from_config()
            if domains:
                actual_domain = domains[0]
        
        # 如果没有指定 dest_group，尝试获取默认的 dest_group
        target_group = dest_group
        if not target_group and actual_domain:
            groups = path_manager.get_operation_groups_from_config(actual_domain)
            if groups:
                target_group = groups[0]
        
        # 如果有 domain 和 dest_group，获取带参数的操作字符串
        if actual_domain and target_group:
            return CommonCompletorHelper.get_operation_with_params(actual_domain, operation_name, target_group)
        else:
            # 回退到原始操作名
            return operation_name