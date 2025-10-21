"""解析器工厂"""

from typing import List, Dict, Any
from .base import BaseParser
from .getopt_parser import GetoptParser
from .argparse_parser import ArgparseParser
from .types import ParserConfig, ArgType
from log import debug


class ParserFactory:
    """解析器工厂"""
    
    @staticmethod
    def create_parser(parser_type: str, arg_parse_config: List[Dict[str, Any]]) -> BaseParser:
        """创建解析器"""
        debug(f"Creating parser of type: {parser_type}")
        
        # 转换配置格式
        configs = ParserFactory._convert_configs(arg_parse_config)
        
        if parser_type == "getopt":
            return GetoptParser(configs)
        elif parser_type == "argparse":
            return ArgparseParser(configs)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")
    
    @staticmethod
    def _convert_configs(raw_configs: List[Dict[str, Any]]) -> List[ParserConfig]:
        """转换原始配置到 ParserConfig 对象"""
        configs = []
        for raw_config in raw_configs:
            # 确定参数类型
            arg_type = ArgType.FLAG  # 默认是 FLAG
            
            if isinstance(raw_config, dict):
                if raw_config.get('is_sub_cmd', False):
                    arg_type = ArgType.SUB_CMD
                elif raw_config.get('is_cmd_arg', False):
                    arg_type = ArgType.VALUE
                elif not raw_config.get('is_flag', True):  # 不是 flag 就是 ARG
                    arg_type = ArgType.OPTION_NEEDS_VALUE
                
                # 转换子参数
                sub_args = []
                if 'sub_args' in raw_config:
                    sub_args = ParserFactory._convert_configs(raw_config['sub_args'])
                
                config = ParserConfig(
                    name=raw_config.get('name', ''),
                    arg_name=raw_config.get('arg', ''),
                    type=arg_type,
                    nargs=raw_config.get('nargs'),
                    short_opt=raw_config.get('short_opt'),
                    long_opt=raw_config.get('long_opt'),
                    aliases=raw_config.get('aliases', []),
                    sub_args=sub_args
                )
                configs.append(config)
            else:
                # 如果已经是 ParserConfig 对象，直接添加
                configs.append(raw_config)
        
        debug(f"Converted {len(configs)} parser configs")
        return configs