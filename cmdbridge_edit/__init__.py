# cmdbridge_edit/__init__.py

"""CmdBridge Edit - Line Editor Integration"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

from .cli import main, cli
from .cli_helper import CmdBridgeEditCLIHelper, create_edit_cli_helper  # 新增

__all__ = [
    'main',
    'cli',
    'CmdBridgeEditCLIHelper',  # 新增
    'create_edit_cli_helper',  # 新增
    '__version__',
    '__author__',
]