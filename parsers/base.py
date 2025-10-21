"""解析器基础类"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .types import SyntaxTree, ParserConfig, ArgNode
from log import debug

class BaseParser(ABC):
    """基础解析器接口"""
    
    def __init__(self, configs: List[ParserConfig]):
        self.configs = configs
        debug(f"{self.__class__.__name__} initialized with {len(configs)} configs")
    
    @abstractmethod
    def parse(self, cmd_args: List[str]) -> SyntaxTree:
        """解析命令行参数"""
        pass
    
    def _find_config_by_name(self, name: str) -> Optional[ParserConfig]:
        """根据名称查找配置"""
        for config in self.configs:
            if (config.name == name or 
                config.short_opt == name or 
                config.long_opt == name or
                name in config.aliases):
                return config
        return None
    
    def _find_config_by_option(self, option: str) -> Optional[ParserConfig]:
        """根据选项查找配置"""
        for config in self.configs:
            if config.short_opt == option or config.long_opt == option:
                return config
        return None
    
    def _handle_extra_args(self, args: List[str]) -> tuple[List[str], Optional[str]]:
        """处理 -- 分隔符"""
        if '--' in args:
            idx = args.index('--')
            main_args = args[:idx]
            extra_args = ' '.join(args[idx+1:]) if idx + 1 < len(args) else ""
            return main_args, extra_args
        return args, None
    
    def _validate_arg_node(self, arg_node: ArgNode, config: ParserConfig) -> bool:
        """验证参数节点"""
        # 这里可以添加参数验证逻辑
        return True