"""
CmdBridge Core Module - 核心功能模块

提供命令映射和操作映射的核心功能。
"""

from .cmd_mapping import CmdMapping, create_cmd_mapping
from .operation_mapping import OperationMapping, create_operation_mapping, generate_command_from_operation

__all__ = [
    # 命令映射
    'CmdMapping',
    'create_cmd_mapping',
    
    # 操作映射  
    'OperationMapping',
    'create_operation_mapping',
    'generate_command_from_operation',
]