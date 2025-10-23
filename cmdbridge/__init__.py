# cmdbridge/__init__.py

"""CmdBridge - Universal Command Mapping Program"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

# 导入主要模块以便可以直接从包级别访问
from .cli import main, cli
from .core.cmd_mapping import CmdMapping
from .config.cmd_mapping_mgr import CmdMappingMgr
from .cmdbridge import CmdBridge  # 新增：导出 CmdBridge 类

# utils.config 不在 cmdbridge 包内，所以不能在这里导入
# from utils.config import ConfigUtils

# 定义公开的API
__all__ = [
    'main',
    'cli', 
    'CmdMapping',
    'CmdMappingMgr',
    'CmdBridge',
    '__version__',
    '__author__',
]