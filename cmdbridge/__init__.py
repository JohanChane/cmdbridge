"""CmdBridge - Universal Command Mapping Program"""

__version__ = "0.1.0"
__author__ = "CmdBridge Developer"

from .cli.cli import main, cli
from .cli.cli_helper import CmdBridgeCLIHelper
from .core.cmd_mapping import CmdMapping
from .cache.cmd_mapping_mgr import CmdMappingMgr
from .cmdbridge import CmdBridge

__all__ = [
    'main',
    'cli', 
    'CmdMapping',
    'CmdMappingMgr',
    'CmdBridge',
    'CmdBridgeCLIHelper',
    '__version__',
    '__author__',
]