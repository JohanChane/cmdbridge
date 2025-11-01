"""CmdBridge Edit - Line Editor Integration"""

__version__ = "0.1.0"
__author__ = "CmdBridge Developer"

from .cli.cli import main, cli
from .cli.cli_helper import CmdBridgeEditCLIHelper

__all__ = [
    'main',
    'cli',
    'CmdBridgeEditCLIHelper',
    '__version__',
    '__author__',
]