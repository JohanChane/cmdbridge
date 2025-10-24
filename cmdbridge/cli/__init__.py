# cmdbridge/cli/__init__.py

"""CmdBridge CLI Module"""

from .cli import cli, main
from .cli_helper import CmdBridgeCLIHelper, create_cli_helper, CustomCommand
from .completion import DOMAIN_TYPE, PROGRAM_GROUP_TYPE, SOURCE_GROUP_TYPE, DynamicCompleter  # 新增导出

__all__ = [
    'cli',
    'main', 
    'CmdBridgeCLIHelper',
    'create_cli_helper',
    'CustomCommand',
    'DOMAIN_TYPE',           # 新增
    'PROGRAM_GROUP_TYPE',    # 新增
    'SOURCE_GROUP_TYPE',     # 新增
    'DynamicCompleter'       # 新增
]