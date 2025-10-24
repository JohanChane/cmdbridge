# cmdbridge_edit/__init__.py

"""CmdBridge Edit - Line Editor Integration"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

from .cli.cli import main, cli  # 更新导入路径
from .cli.cli_helper import CmdBridgeEditCLIHelper, create_edit_cli_helper  # 更新导入路径

__all__ = [
    'main',
    'cli',
    'CmdBridgeEditCLIHelper',
    'create_edit_cli_helper',
    '__version__',
    '__author__',
]