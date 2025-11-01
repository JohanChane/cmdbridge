"""
CmdBridge 解析器模块

提供命令行解析功能，支持 getopt 和 argparse 两种风格的命令行解析。
"""

from .types import (
    ParserConfig,
    ParserType, 
    ArgumentConfig,
    ArgumentCount,
    SubCommandConfig,
    CommandToken,
    TokenType,
    CommandNode,
    CommandArg,
    ArgType,
)

from .config_loader import ConfigLoader, load_parser_config_from_data, load_parser_config_from_file
from .factory import ParserFactory

__all__ = [
    # 配置加载
    'ConfigLoader',
    'load_parser_config_from_data',
    'load_parser_config_from_file',
    
    # 核心配置类型
    'ParserConfig', 
    'ParserType',
    
    # 参数配置
    'ArgumentConfig',
    'ArgumentCount',
    
    # 子命令配置
    'SubCommandConfig',
    
    # 解析结果类型
    'CommandToken',
    'TokenType',
    'CommandNode', 
    'CommandArg',
    'ArgType',

    'ParserFactory',
]

# 模块版本信息
__version__ = "0.1.0"
__author__ = "CmdBridge Parser Team"