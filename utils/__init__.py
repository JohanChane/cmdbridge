# utils/__init__.py

"""
CmdBridge 工具模块

提供配置管理和补全功能。
"""

from .config import ConfigUtils
from .completion import CompletionUtils

__all__ = [
    'ConfigUtils',
    'CompletionUtils',
]

# 模块版本信息
__version__ = "1.0.0"
__author__ = "CmdBridge Utils Team"