"""
Parser Base Class
"""

from abc import ABC, abstractmethod
from typing import List
from .types import CommandNode, ParserConfig


class BaseParser(ABC):
    """Command line parser base class"""
    
    def __init__(self, parser_config: ParserConfig):
        """
        Initialize parser
        
        Args:
            parser_config: Parser configuration
        """
        self.parser_config = parser_config
    
    @abstractmethod
    def parse(self, args: List[str]) -> CommandNode:
        """
        Parse command line arguments
        
        Args:
            args: Command line argument list
            
        Returns:
            CommandNode: Parsed command tree
        """
        pass
    
    @abstractmethod
    def validate(self, command_node: CommandNode) -> bool:
        """
        Validate if parsing result conforms to configuration
        
        Args:
            command_node: Parsed command tree
            
        Returns:
            bool: Whether validation passed
        """
        pass