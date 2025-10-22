"""
解析器基类
"""

from abc import ABC, abstractmethod
from typing import List
from .types import CommandNode, ParserConfig


class BaseParser(ABC):
    """命令行解析器基类"""
    
    def __init__(self, parser_config: ParserConfig):
        """
        初始化解析器
        
        Args:
            parser_config: 解析器配置
        """
        self.parser_config = parser_config
    
    @abstractmethod
    def parse(self, args: List[str]) -> CommandNode:
        """
        解析命令行参数
        
        Args:
            args: 命令行参数列表
            
        Returns:
            CommandNode: 解析后的命令树
        """
        pass
    
    @abstractmethod
    def validate(self, command_node: CommandNode) -> bool:
        """
        验证解析结果是否符合配置
        
        Args:
            command_node: 解析后的命令树
            
        Returns:
            bool: 是否验证通过
        """
        pass