from typing import Optional
from .types import ParserConfig, ParserType
from .argparse_parser import ArgparseParser
from .base import BaseParser
from log import error


class ParserFactory:
    """解析器工厂 - 根据配置创建对应的解析器实例"""
    
    @staticmethod
    def create_parser(parser_config: ParserConfig) -> Optional[BaseParser]:
        """
        根据解析器配置创建对应的解析器实例
        
        Args:
            parser_config: 解析器配置对象
            
        Returns:
            Optional[BaseParser]: 解析器实例，如果类型不支持则返回 None
        """
        try:
            if parser_config.parser_type == ParserType.ARGPARSE:
                return ArgparseParser(parser_config)
            elif parser_config.parser_type == ParserType.GETOPT:
                return ArgparseParser(parser_config)
            else:
                error(f"不支持的解析器类型: {parser_config.parser_type}")
                return None
        except Exception as e:
            error(f"创建解析器失败: {e}")
            return None