# cmdbridge/core/parsers/argparse_parser.py
from typing import List
from .base import BaseParser
from .types import SyntaxTree, ArgNode, ArgType
from log import debug

class ArgparseParser(BaseParser):
    """Argparse 风格解析器 - 简化版本"""
    
    def parse(self, cmd_args: List[str]) -> SyntaxTree:
        debug(f"Argparse parsing: {cmd_args}")
        
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
        
        # 查找子命令
        sub_cmd_config = self._find_sub_command(remaining_args)
        if sub_cmd_config:
            sub_node = self._parse_sub_command(remaining_args, sub_cmd_config)
            argument_nodes.append(sub_node)
        else:
            # 处理全局参数
            self._parse_global_args(remaining_args, argument_nodes)
        
        return SyntaxTree(
            command_name=cmd_name,
            argument_nodes=argument_nodes,
            extra_content=extra
        )
    
    def _find_sub_command(self, args: List[str]) -> any:
        """查找子命令配置"""
        if not args:
            return None
            
        first_arg = args[0]
        for config in self.configs:
            if config.is_sub_cmd and (config.name == first_arg or first_arg in config.aliases):
                return config
        return None
    
    def _parse_sub_command(self, args: List[str], config) -> ArgNode:
        """解析子命令 - 修复版本"""
        sub_node = ArgNode(
            name=config.name,
            type=ArgType.SUB_CMD,
            values=[],  # 子命令的值（包名等）
            args=[],    # 子命令的参数（如 --installed）
            repeat=1,
            original_opt=args[0]
        )
        
        i = 1  # 从子命令后面的参数开始
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                # 查找子命令的子参数配置
                sub_arg_config = self._find_config_by_option_in_list(config.sub_args, arg)
                if sub_arg_config:
                    sub_arg_node = ArgNode(
                        name=sub_arg_config.short_opt or sub_arg_config.long_opt or sub_arg_config.name,
                        type=sub_arg_config.type,
                        values=[],
                        args=[],
                        repeat=1,
                        original_opt=arg
                    )
                    sub_node.args.append(sub_arg_node)
                    i += 1
                else:
                    # 不是子命令参数，停止解析子命令
                    break
            else:
                # 值参数（包名等）添加到子命令的 values 中
                sub_node.values.append(arg)
                i += 1
        
        return sub_node

    def _find_config_by_option_in_list(self, configs: List, option: str):
        """在配置列表中查找选项"""
        for config in configs:
            if config.short_opt == option or config.long_opt == option:
                return config
        return None

    def _parse_global_args(self, args: List[str], argument_nodes: List[ArgNode]):
        """解析全局参数"""
        for arg in args:
            if arg.startswith('-'):
                # 选项参数
                config = self._find_config_by_option(arg)
                if config:
                    arg_node = ArgNode(
                        name=config.short_opt or config.long_opt or config.name,
                        type=config.type,
                        values=[],
                        args=[],
                        repeat=1,
                        original_opt=arg
                    )
                    argument_nodes.append(arg_node)
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