# cmdbridge/__init__.py

"""CmdBridge - Universal Command Mapping Program"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

# 导入主要模块以便可以直接从包级别访问
from .cli import main, cli
from .cli_helper import CmdBridgeCLIHelper, create_cli_helper  # 新增
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
    'CmdBridgeCLIHelper',  # 新增
    'create_cli_helper',   # 新增
    '__version__',
    '__author__',
]