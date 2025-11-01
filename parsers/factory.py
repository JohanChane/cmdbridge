from typing import Optional
from .types import ParserConfig, ParserType
from .argparse_parser import ArgparseParser
from .base import BaseParser
from log import error


class ParserFactory:
    """Parser Factory - Create corresponding parser instances based on configuration"""
    
    @staticmethod
    def create_parser(parser_config: ParserConfig) -> Optional[BaseParser]:
        """
        Create corresponding parser instance based on parser configuration
        
        Args:
            parser_config: Parser configuration object
            
        Returns:
            Optional[BaseParser]: Parser instance, returns None if type is not supported
        """
        try:
            if parser_config.parser_type == ParserType.ARGPARSE:
                return ArgparseParser(parser_config)
            elif parser_config.parser_type == ParserType.GETOPT:
                return ArgparseParser(parser_config)
            else:
                error(f"Unsupported parser type: {parser_config.parser_type}")
                return None
        except Exception as e:
            error(f"Failed to create parser: {e}")
            return None