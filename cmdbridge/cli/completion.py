# cmdbridge/cli/completion.py

import sys
import click
from typing import List, Optional
from ..config.path_manager import PathManager

from log import set_out, get_out, debug

# 自定义 Click 参数类型
class DomainType(click.ParamType):
    """领域名称参数类型，支持自动补全"""
    name = "domain"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        original_out = get_out()
        if bool(ctx and ctx.resilient_parsing):
            set_out(sys.stderr)
        try:
            from ..click_ext.completor import DynamicCompleter
            completions = DynamicCompleter.get_domains(ctx, param, incomplete)
            # 使用兼容的方式返回补全项
            return [click.CompletionItem(domain) if hasattr(click, 'CompletionItem') 
                    else click.completion.CompletionItem(domain) 
                    for domain in completions]
        finally:
            set_out(original_out)

class ProgramGroupType(click.ParamType):
    """程序组参数类型，支持自动补全"""
    name = "program_group"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        original_out = get_out()
        if bool(ctx and ctx.resilient_parsing):
            set_out(sys.stderr)
        try:
            from ..click_ext.completor import DynamicCompleter
            completions = DynamicCompleter.get_program_groups(ctx, param, incomplete)
            # 使用兼容的方式返回补全项
            return [click.CompletionItem(group) if hasattr(click, 'CompletionItem')
                    else click.completion.CompletionItem(group)
                    for group in completions]
        finally:
            set_out(original_out)
        

class SourceGroupType(click.ParamType):
    """源程序组参数类型，支持自动补全"""
    name = "source_group"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        original_out = get_out()
        if bool(ctx and ctx.resilient_parsing):
            set_out(sys.stderr)
        try:
            from ..click_ext.completor import DynamicCompleter
            completions = DynamicCompleter.get_source_groups(ctx, param, incomplete)
            # 使用兼容的方式返回补全项
            return [click.CompletionItem(group) if hasattr(click, 'CompletionItem')
                    else click.completion.CompletionItem(group)
                    for group in completions]
        finally:
            set_out(original_out)


# 创建类型实例
DOMAIN_TYPE = DomainType()
PROGRAM_GROUP_TYPE = ProgramGroupType()
SOURCE_GROUP_TYPE = SourceGroupType()