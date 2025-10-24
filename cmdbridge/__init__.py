# cmdbridge/__init__.py

"""CmdBridge - Universal Command Mapping Program"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

# 导入主要模块以便可以直接从包级别访问
from .cli.cli import main, cli  # 更新导入路径
from .cli.cli_helper import CmdBridgeCLIHelper, create_cli_helper  # 更新导入路径
from .core.cmd_mapping import CmdMapping
from .config.cmd_mapping_mgr import CmdMappingMgr
from .cmdbridge import CmdBridge

# 定义公开的API
__all__ = [
    'main',
    'cli', 
    'CmdMapping',
    'CmdMappingMgr',
    'CmdBridge',
    'CmdBridgeCLIHelper',
    'create_cli_helper',
    '__version__',
    '__author__',
]