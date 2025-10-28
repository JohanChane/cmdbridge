import sys
import click
from .completor_helper import CommonCompletorHelper
from log import get_out, set_out
from cmdbridge.config.path_manager import PathManager


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

        domain = ctx.params.get("domain")
        source_group = ctx.params.get("source_group")
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

        domain = ctx.params.get("domain")
        dest_group = ctx.params.get("dest_group")
        
        if dest_group:
            operations = CommonCompletorHelper.get_operation_names(domain, dest_group)
        else:
            operations = CommonCompletorHelper.get_all_operation_names(domain)

        # 获取带参数的操作字符串
        operation_items = []
        for op in operations:
            if dest_group:
                # 确保 domain 不为 None
                actual_domain = domain
                if not actual_domain:
                    # 如果没有指定 domain，使用默认 domain
                    path_manager = PathManager.get_instance()
                    domains = path_manager.get_domains_from_config()
                    if domains:
                        actual_domain = domains[0]
                
                if actual_domain:
                    # 获取带参数的操作字符串
                    op_with_params = CommonCompletorHelper.get_operation_with_params(actual_domain, op, dest_group)
                    operation_items.append(
                        click.shell_completion.CompletionItem(op_with_params)
                    )
                else:
                    # 如果还是没有 domain，使用原始操作名
                    operation_items.append(
                        click.shell_completion.CompletionItem(op)
                    )
            else:
                operation_items.append(
                    click.shell_completion.CompletionItem(op)
                )

        return [
            item for item in operation_items
            if item.value.startswith(incomplete)
        ]