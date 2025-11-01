"""
CmdBridge Core Module - Core Functionality Module

Provides core functionality for command mapping and operation mapping.
"""

from .cmd_mapping import CmdMapping, create_cmd_mapping
from .operation_mapping import OperationMapping, create_operation_mapping, generate_command_from_operation

__all__ = [
    # Command mapping
    'CmdMapping',
    'create_cmd_mapping',
    
    # Operation mapping  
    'OperationMapping',
    'create_operation_mapping',
    'generate_command_from_operation',
]