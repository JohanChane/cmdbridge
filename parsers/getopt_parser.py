# cmdbridge/core/parsers/getopt_parser.py
from typing import List
from .base import BaseParser
from .types import SyntaxTree, ArgNode, ArgType
from log import debug, error

# cmdbridge/core/parsers/getopt_parser.py
class GetoptParser(BaseParser):
    """Getopt 风格解析器 - 简化版本"""
    
    def parse(self, cmd_args: List[str]) -> SyntaxTree:
        debug(f"Getopt parsing: {cmd_args}")
        
        # 处理 -- 分隔符
        main_args, extra = self._handle_extra_args(cmd_args)
        
        if not main_args:
            return SyntaxTree(
                command_name="",
                argument_nodes=[],
                extra_content=extra
            )
        
        cmd_name = main_args[0]
        argument_nodes = []
        remaining_args = main_args[1:]
        
        # 展开组合参数 (-Syu -> -S -y -u)
        expanded_args = self._expand_combined_args(remaining_args)
        
        # 解析参数
        i = 0
        while i < len(expanded_args):
            arg = expanded_args[i]
            
            if arg.startswith('-'):
                # 选项参数 - 检查是否在配置中
                config = self._find_config_by_option(arg)
                if config:
                    # Getopt 解析器忽略 sub_args，所有选项都是同级
                    arg_node = ArgNode(
                        name=config.short_opt or config.long_opt or config.name,
                        type=config.type,
                        values=[],
                        args=[],  # Getopt 没有子参数概念
                        repeat=1,
                        original_opt=arg
                    )
                    argument_nodes.append(arg_node)
                    
                    # 如果选项需要参数值，处理下一个参数
                    if config.type == ArgType.OPTION_NEEDS_VALUE and i + 1 < len(expanded_args):
                        next_arg = expanded_args[i + 1]
                        if not next_arg.startswith('-'):
                            value_node = ArgNode(
                                name=config.arg_name,
                                type=ArgType.VALUE,
                                values=[next_arg],
                                args=[],
                                repeat=1,
                                original_opt=next_arg
                            )
                            argument_nodes.append(value_node)
                            i += 1  # 跳过值参数
                else:
                    # 未知选项 - 报错
                    raise ValueError(f"Unknown option: {arg}")
            else:
                # 值参数
                arg_node = ArgNode(
                    name=arg,
                    type=ArgType.VALUE,
                    values=[arg],
                    args=[],
                    repeat=1,
                    original_opt=arg
                )
                argument_nodes.append(arg_node)
            
            i += 1
        
        return SyntaxTree(
            command_name=cmd_name,
            argument_nodes=argument_nodes,
            extra_content=extra
        )
    
    def _expand_combined_args(self, args: List[str]) -> List[str]:
        """展开组合参数 (-Syu -> -S -y -u)"""
        expanded = []
        for arg in args:
            if (arg.startswith('-') and 
                len(arg) > 2 and 
                not arg.startswith('--') and
                arg[1] != '-'):
                # 展开组合选项
                for char in arg[1:]:
                    expanded.append(f'-{char}')
            else:
                expanded.append(arg)
        return expanded