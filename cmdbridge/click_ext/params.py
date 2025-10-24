# cmdbridge/click_ext/params.py

"""自定义 Click 参数"""

import click
from typing import List, Optional, Any, Callable
from .completor import completer, COMMAND_COMPLETION_TYPE  # 更新导入路径


def domain_option(**kwargs):
    """领域名称选项"""
    return click.option(
        '-d', '--domain',
        type=completer.get_domain_type(),
        help='领域名称',
        **kwargs
    )


def dest_group_option(**kwargs):
    """目标程序组选项（上下文感知）"""
    return click.option(
        '-t', '--dest-group',
        type=completer.get_program_group_type(),
        help='目标程序组（基于 -d 选项的值进行补全）',
        **kwargs
    )


def source_group_option(**kwargs):
    """源程序组选项（上下文感知）"""
    return click.option(
        '-s', '--source-group', 
        type=completer.get_source_group_type(),
        help='源程序组（基于 -d 选项的值进行补全）',
        **kwargs
    )


def command_argument(**kwargs):
    """命令参数，支持动态补全"""
    return click.argument(
        'command_parts',
        nargs=-1,
        type=COMMAND_COMPLETION_TYPE,
        **kwargs
    )