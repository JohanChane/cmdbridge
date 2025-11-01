"""
CmdBridge Parser Module

Provides command line parsing functionality, supporting both getopt and argparse style command line parsing.
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
    # Configuration loading
    'ConfigLoader',
    'load_parser_config_from_data',
    'load_parser_config_from_file',
    
    # Core configuration types
    'ParserConfig', 
    'ParserType',
    
    # Argument configuration
    'ArgumentConfig',
    'ArgumentCount',
    
    # Subcommand configuration
    'SubCommandConfig',
    
    # Parsing result types
    'CommandToken',
    'TokenType',
    'CommandNode', 
    'CommandArg',
    'ArgType',

    'ParserFactory',
]

__version__ = "0.1.0"
__author__ = "CmdBridge Parser Team"