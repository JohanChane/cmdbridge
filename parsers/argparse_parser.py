"""
argparse 风格命令行解析器
"""

from typing import List, Dict, Any, Optional, Tuple
from .types import CommandToken, TokenType, CommandNode, CommandArg, ArgType, ParserConfig, ArgumentConfig, SubCommandConfig
from .base import BaseParser

from log import debug, info, warning, error
from .utils import Utils

class ArgparseParser(BaseParser):
    def __init__(self, parser_config: ParserConfig):
        """
        初始化 argparse 解析器
        
        Args:
            parser_config: 解析器配置
        """
        super().__init__(parser_config)

    def parse(self, args: List[str]) -> CommandNode:
        """
        解析 argparse 风格命令行
        
        Args:
            args: 命令行参数列表
            
        Returns:
            CommandNode: 解析后的命令树
        """

        if args is None:
            raise ValueError("args is None")

        debug(f"开始解析命令行: {args}")
        
        # 🔧 使用统一的命令行预处理
        normalized_args = Utils.normalize_command_line(args)
        debug(f"预处理后命令行: {normalized_args}")
        
        debug(f"parser_config: {self.parser_config}")

        tokens = self._tokenize(normalized_args)
        debug(f"生成的 tokens: {[str(t) for t in tokens]}")

        cmd_tree = self._build_command_tree(tokens)
        debug(f"构建的命令树: {cmd_tree.name}, 参数数量: {len(cmd_tree.arguments)}")
        Utils.print_command_tree(cmd_tree)
        return cmd_tree
    
    def _build_command_tree(self, tokens: List[CommandToken]) -> CommandNode:
        """
        构建命令节点（统一处理主命令和子命令）
        
        Args:
            tokens: 该节点的 tokens
            config_arguments: 该节点对应的参数配置
        """
        
        if not tokens:
            raise ValueError("没有 tokens")
        
        if tokens[0].token_type != TokenType.PROGRAM:
            raise ValueError("第一个 token 不是程序名")
        
        # 节点名称从第一个 token 获取
        program_name = tokens[0].get_first_value()
        cmd_node = CommandNode(name=program_name)
        debug(f"创建命令节点: {program_name}")

        self._build_arguments_command_node(cmd_node, tokens[1:])

        return cmd_node

    def _build_arguments_command_node(self, cmd_node: CommandNode, tokens: List[CommandToken]):
        """构建 CommandNode.arguments 和 CommandNode.subcommand"""
        argument_tokens, subcmd_token, subcmd_tokens = self._split_tokens_by_subcommand(tokens)
        debug(f"_split_tokens_by_subcommand. argument_tokens: {argument_tokens}, subcmd_token: {subcmd_token}, subcmd_tokens: {subcmd_tokens}")
        self._build_arguments_for_command_node(cmd_node, argument_tokens)

        if subcmd_token:
            cmd_node.subcommand = CommandNode(name=subcmd_token.get_first_value())
            self._build_arguments_command_node(cmd_node.subcommand, subcmd_tokens)
    
    def _build_arguments_for_command_node(self, cmd_node: CommandNode, tokens: List[CommandToken]):
        """只构建 CommandNode.arguments"""
        def find_flag_cmdarg(token: CommandToken, arguments: List[CommandArg]) -> Optional[CommandArg]:
            for arg in arguments:
                if arg.node_type == ArgType.FLAG:
                    if arg.option_name in token.values:
                        return arg
            return None

        def find_opt_cmdarg(token: CommandToken, arguments: List[CommandArg]) -> Optional[CommandArg]:
            for arg in arguments:
                if arg.node_type == ArgType.OPTION:
                    if arg.option_name in token.values:
                        return arg
            return None

        token_cnt = len(tokens)
        token_idx = 0

        arguments: List[CommandArg] = []
        current_positional_cmdarg: CommandArg = None
        current_extra_cmdarg: CommandArg = None
        current_opt_cmdarg = None
        while token_idx < token_cnt:
            token = tokens[token_idx]

            if token.is_flag():
                flag_cmdarg = find_flag_cmdarg(token, arguments)
                if flag_cmdarg:
                    flag_cmdarg.repeat += 1
                else:
                    arguments.append(CommandArg(
                        node_type = ArgType.FLAG,
                        option_name = token.get_first_value(),
                        repeat = 1
                    ))
            elif token.is_option_name():
                debug(f"token.option_name: {token.get_first_value()}")
                opt_cmdarg = find_opt_cmdarg(token, arguments)
                if not opt_cmdarg:
                    arguments.append(CommandArg(
                        node_type = ArgType.OPTION,
                        option_name = token.get_first_value(),
                    ))
                    current_opt_cmdarg = arguments[-1]
                    debug(f"New CommandArg (ArgType.OPTION) option_name: {token.get_first_value()}")
                else:
                    debug(f"Find the existent CommandArg (ArgType.OPTION) option_name: {current_opt_cmdarg}")
                    current_opt_cmdarg = opt_cmdarg
            elif token.is_option_value():
                if not current_opt_cmdarg:
                    raise ValueError(f"current_opt_cmdarg is None")
                
                current_opt_cmdarg.values.extend(token.values)
            elif token.is_positional_arg():
                if current_positional_cmdarg:
                    current_positional_cmdarg.values.extend(token.values)
                else:
                    arguments.append(CommandArg(
                        node_type = ArgType.POSITIONAL,
                        values = token.values,
                    ))
                    current_positional_cmdarg = arguments[-1]
            elif token.is_extra_arg():
                if current_extra_cmdarg:
                    current_extra_cmdarg.values.extend(token.values)
                else:
                    arguments.append(CommandArg(
                        node_type = ArgType.EXTRA,
                        values = token.values,
                    ))
                    current_extra_cmdarg = arguments[-1]

            token_idx += 1

        cmd_node.arguments = arguments

    def _split_tokens_by_subcommand(self, tokens: List[CommandToken]) -> Tuple[List[CommandToken], Optional[CommandToken], List[CommandToken]]:
        """
        使用列表切片分割 tokens
        """
        for i, token in enumerate(tokens):
            if token.token_type == TokenType.SUBCOMMAND:
                main_tokens = tokens[:i]
                subcommand_token = token
                subcommand_tokens = tokens[i + 1:]
                return main_tokens, subcommand_token, subcommand_tokens
        
        # 没有找到子命令
        return tokens, None, []

    def _tokenize(self, args: List[str]) -> List[CommandToken]:
        """将命令行参数转换为 token 列表"""
        tokens = []

        # 第一个参数是程序名
        if args:
            tokens.append(CommandToken(
                token_type=TokenType.PROGRAM,
                values=[args[0]]
            ))
            debug(f"识别程序名: {args[0]}")

        arguments_tokens = ArgparseParser._tokenize_arguments(args[1:], self.parser_config.arguments, self.parser_config.sub_commands)
        # debug(f"arguments_tokens: {arguments_tokens}")
        tokens.extend(arguments_tokens)

        return tokens

    @staticmethod
    def _tokenize_arguments(args: List[str], arguments_config: List[ArgumentConfig], subcmds_config: List[SubCommandConfig]) -> List[CommandToken]:
        """
        args: 主命令或子命令之后的参数
        arguments_config: 为当前命令的参数配置
        subcmd_config: 当前命令的子命令配置
        """

        tokens = []
        arg_idx = 0
        arg_cnt = len(args)

        after_separator = False
        current_option_argconfig = None
        current_option_value_num = 0
        current_positional_value_num = 0
        current_exact_option_value_num = 0      # 表示 option 必须要 n 个参数
        
        while arg_idx < arg_cnt:
            arg = args[arg_idx]

            # TokenType (SEPARATOR)
            if arg == "--":
                tokens.append(CommandToken(
                    token_type=TokenType.SEPARATOR,
                    values=["--"]
                ))
                after_separator = True
                arg_idx += 1
                continue

            # TokenType (EXTRA_ARG)
            if after_separator:
                tokens.append(CommandToken(
                    token_type=TokenType.EXTRA_ARG,
                    values=[arg]
                ))
                arg_idx += 1
                continue

            # TokenType (OPTION_NAME, FLAG)
            if arg.startswith("-"):
                if current_option_argconfig:
                    debug(f"current_option_argconfig: {current_option_argconfig}")
                    raise ValueError("option_value 不应该以 `-` 开头")
                
                option_config = ArgparseParser._find_argument_config(arg, arguments_config)
                if option_config is not None:
                    current_positional_value_num  = 0       # 有 `-` 开头的参数, 证明位置参数的计算终止了
                    
                    if option_config.is_flag():
                        tokens.append(CommandToken(
                            token_type=TokenType.FLAG,
                            values=[option_config.get_primary_option_name()]            # 为了后续的节点判断, 必须统一 option_name
                        ))
                    elif option_config.is_option():
                        tokens.append(CommandToken(
                            token_type=TokenType.OPTION_NAME,
                            values=[option_config.get_primary_option_name()]            # 为了后续的节点判断, 必须统一 option_name
                        ))

                        current_option_argconfig = option_config
                        current_option_value_num = 0

                        # 如果知道 option value 需要的准确的数量或 narg="+", 则直接添加 (这样能处理 option value 和子命令同名的情况, 同时就可以在下次循环时, 直接优先判断是否是子命令)
                        option_value_count = option_config.nargs.get_exact_count()
                        debug(f"option_value_count: {option_value_count}")
                        if option_value_count:
                            # 记录状态
                            current_exact_option_value_num = option_value_count
                        elif option_config.nargs == "+":        # 加一个 optoin_value 就行了 (下次循环时, 直接优先判断是否是子命令)
                            # 记录状态
                            current_exact_option_value_num = 1
                    else:
                        raise ValueError(f"无法处理 arg: {arg}")

                else:
                    raise ValueError(f"参数配置没有该选项: {arg}")
            # TokenType (OPTION_VALUE)
            elif current_exact_option_value_num > 0:
                if arg.startswith("-"):
                    raise ValueError(f"option value 不应该以 `-` 开头: {arg}")
                
                tokens.append(CommandToken(
                    token_type=TokenType.OPTION_VALUE,
                    values=[arg]
                ))
                
                current_option_value_num += 1
                current_exact_option_value_num -= 1

                if not current_option_argconfig.nargs.validate_count(current_option_value_num + 1):
                    current_option_argconfig = None
                    current_option_value_num = 0
                    current_exact_option_value_num = 0
            # TokenType (SUBCOMMAND, OPTION_VALUE, POSITIONAL)
            else:
                # 优先判断 arg 是否是子命令
                # subcmd_config.sub_commands
                nested_subcmd_config = ArgparseParser._find_subcmd_config(arg, subcmds_config)
                if nested_subcmd_config is not None:
                    tokens.append(CommandToken(
                        token_type=TokenType.SUBCOMMAND,
                        values=[arg]
                    ))
                    subcmd_tokens = ArgparseParser._tokenize_arguments(args[arg_idx + 1:], nested_subcmd_config.arguments, nested_subcmd_config.sub_commands)
                    tokens.extend(subcmd_tokens)
                    return tokens

                # 再判断 arg 是否是 OPTION_VALUE (如果不是子命且有 current_option_argconfig)
                elif current_option_argconfig:
                    if not current_option_argconfig.nargs.validate_count(current_option_value_num + 1):
                        raise ValueError("current_option_argconfig 状态有误, 不应该进入该分支")
                    
                    tokens.append(CommandToken(
                        token_type=TokenType.OPTION_VALUE,
                        values=[arg]
                    ))

                    current_option_value_num += 1

                # 不是子命令又不是 option_value, 所以一定是 positional value (有 positional value 的前提下)。
                else:
                    positional_value_config = ArgparseParser._get_positional_arg_config(arguments_config)
                    if positional_value_config is None:
                        raise ValueError(f"没有位置参数的参数配置. arguments_config: {arguments_config}")
                    
                    if positional_value_config.nargs.validate_count(current_positional_value_num + 1):
                        tokens.append(CommandToken(
                            token_type=TokenType.POSITIONAL_ARG,
                            values=[arg]
                        ))

                        current_positional_value_num += 1
                    else:
                        raise ValueError(f"有过多的位置参数. positional_value_config.nargs: {positional_value_config.nargs}, current_positional_value_num: {current_positional_value_num}")

                    # 因为有 positional value 则没有子命令, 到下次循环再处理即可

            arg_idx += 1

        return tokens

    @staticmethod
    def _find_argument_config(option_name: str, arguments: List[ArgumentConfig]) -> Optional[ArgumentConfig]:
        for arg in arguments:
            if arg.matches_option(option_name):
                return arg
        return None
            

    @staticmethod
    def _find_subcmd_config(sub_cmd_name: str, sub_commands: List[SubCommandConfig]) -> Optional[SubCommandConfig]:
        for subcmd in sub_commands:
            if sub_cmd_name == subcmd.name:
                return subcmd
        return None

    @staticmethod
    def _get_positional_arg_config(arguments: List[ArgumentConfig]) -> Optional[ArgumentConfig]:
        for arg_config in arguments:
            if arg_config.is_positional():
                return arg_config
        return None
    
    def validate(self, command_node: CommandNode) -> bool:
        """
        验证解析结果是否符合配置
        
        Args:
            command_node: 解析后的命令树
            
        Returns:
            bool: 是否验证通过
        """

        # _tokenize 和 build_command_tree 时已经判断了
        return True