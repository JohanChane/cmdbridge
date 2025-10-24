"""自定义 Click 参数"""

import click
from typing import List, Optional, Any, Callable
from . import completer


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