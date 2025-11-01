"""
argparse style command line parser
"""

from typing import List, Dict, Any, Optional, Tuple
from .types import CommandToken, TokenType, CommandNode, CommandArg, ArgType, ParserConfig, ArgumentConfig, SubCommandConfig
from .base import BaseParser

from log import debug, info, warning, error
from .utils import Utils

class ArgparseParser(BaseParser):
    def __init__(self, parser_config: ParserConfig):
        """
        Initialize argparse parser
        
        Args:
            parser_config: Parser configuration
        """
        super().__init__(parser_config)

    def parse(self, args: List[str]) -> CommandNode:
        """
        Parse argparse style command line
        
        Args:
            args: Command line argument list
            
        Returns:
            CommandNode: Parsed command tree
        """

        if args is None:
            raise ValueError("args is None")

        debug(f"Starting command line parsing: {args}")
        
        # 🔧 Use unified command line preprocessing
        normalized_args = Utils.normalize_command_line(args)
        debug(f"Command line after preprocessing: {normalized_args}")
        
        debug(f"parser_config: {self.parser_config}")

        tokens = self._tokenize(normalized_args)
        debug(f"Generated tokens: {[str(t) for t in tokens]}")

        cmd_tree = self._build_command_tree(tokens)
        debug(f"Built command tree: {cmd_tree.name}, argument count: {len(cmd_tree.arguments)}")
        Utils.print_command_tree(cmd_tree)
        return cmd_tree
    
    def _build_command_tree(self, tokens: List[CommandToken]) -> CommandNode:
        """
        Build command node (unified handling of main command and subcommands)
        
        Args:
            tokens: Tokens for this node
            config_arguments: Argument configuration corresponding to this node
        """
        
        if not tokens:
            raise ValueError("No tokens")
        
        if tokens[0].token_type != TokenType.PROGRAM:
            raise ValueError("First token is not program name")
        
        # Node name from first token
        program_name = tokens[0].get_first_value()
        cmd_node = CommandNode(name=program_name)
        debug(f"Created command node: {program_name}")

        self._build_arguments_command_node(cmd_node, tokens[1:])

        return cmd_node

    def _build_arguments_command_node(self, cmd_node: CommandNode, tokens: List[CommandToken]):
        """Build CommandNode.arguments and CommandNode.subcommand"""
        argument_tokens, subcmd_token, subcmd_tokens = self._split_tokens_by_subcommand(tokens)
        debug(f"_split_tokens_by_subcommand. argument_tokens: {argument_tokens}, subcmd_token: {subcmd_token}, subcmd_tokens: {subcmd_tokens}")
        self._build_arguments_for_command_node(cmd_node, argument_tokens)

        if subcmd_token:
            cmd_node.subcommand = CommandNode(name=subcmd_token.get_first_value())
            self._build_arguments_command_node(cmd_node.subcommand, subcmd_tokens)
    
    def _build_arguments_for_command_node(self, cmd_node: CommandNode, tokens: List[CommandToken]):
        """Only build CommandNode.arguments"""
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
        Split tokens using list slicing
        """
        for i, token in enumerate(tokens):
            if token.token_type == TokenType.SUBCOMMAND:
                main_tokens = tokens[:i]
                subcommand_token = token
                subcommand_tokens = tokens[i + 1:]
                return main_tokens, subcommand_token, subcommand_tokens
        
        # No subcommand found
        return tokens, None, []

    def _tokenize(self, args: List[str]) -> List[CommandToken]:
        """Convert command line arguments to token list"""
        tokens = []

        # First argument is program name
        if args:
            tokens.append(CommandToken(
                token_type=TokenType.PROGRAM,
                values=[args[0]]
            ))
            debug(f"Identified program name: {args[0]}")

        arguments_tokens = ArgparseParser._tokenize_arguments(args[1:], self.parser_config.arguments, self.parser_config.sub_commands)
        # debug(f"arguments_tokens: {arguments_tokens}")
        tokens.extend(arguments_tokens)

        return tokens

    @staticmethod
    def _tokenize_arguments(args: List[str], arguments_config: List[ArgumentConfig], subcmds_config: List[SubCommandConfig]) -> List[CommandToken]:
        """
        args: Arguments after main command or subcommand
        arguments_config: Argument configuration for current command
        subcmd_config: Subcommand configuration for current command
        """

        tokens = []
        arg_idx = 0
        arg_cnt = len(args)

        after_separator = False
        current_option_argconfig = None
        current_option_value_num = 0
        current_positional_value_num = 0
        current_exact_option_value_num = 0      # Indicates option requires exactly n arguments
        
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
                    raise ValueError("option_value should not start with `-`")
                
                option_config = ArgparseParser._find_argument_config(arg, arguments_config)
                if option_config is not None:
                    current_positional_value_num  = 0       # Arguments starting with `-` prove positional argument calculation has ended
                    
                    if option_config.is_flag():
                        tokens.append(CommandToken(
                            token_type=TokenType.FLAG,
                            values=[option_config.get_primary_option_name()]            # For subsequent node judgment, must unify option_name
                        ))
                    elif option_config.is_option():
                        tokens.append(CommandToken(
                            token_type=TokenType.OPTION_NAME,
                            values=[option_config.get_primary_option_name()]            # For subsequent node judgment, must unify option_name
                        ))

                        current_option_argconfig = option_config
                        current_option_value_num = 0

                        # If exact number of option values needed is known or narg="+", add directly (this handles cases where option value and subcommand have same name, and can prioritize subcommand check in next loop)
                        option_value_count = option_config.nargs.get_exact_count()
                        debug(f"option_value_count: {option_value_count}")
                        if option_value_count:
                            # Record state
                            current_exact_option_value_num = option_value_count
                        elif option_config.nargs == "+":        # Just add one option_value (next loop will prioritize subcommand check)
                            # Record state
                            current_exact_option_value_num = 1
                    else:
                        raise ValueError(f"Cannot handle arg: {arg}")

                else:
                    raise ValueError(f"Argument configuration does not have this option: {arg}")
            # TokenType (OPTION_VALUE)
            elif current_exact_option_value_num > 0:
                if arg.startswith("-"):
                    raise ValueError(f"option value should not start with `-`: {arg}")
                
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
                # First check if arg is a subcommand
                # subcmd_config.sub_commands
                nested_subcmd_config = ArgparseParser._find_subcmd_config(arg, subcmds_config)
                if nested_subcmd_config is not None:
                    tokens.append(CommandToken(
                        token_type=TokenType.SUBCOMMAND,
                        values=[nested_subcmd_config.name]        # Use configuration name because of aliases
                    ))
                    subcmd_tokens = ArgparseParser._tokenize_arguments(args[arg_idx + 1:], nested_subcmd_config.arguments, nested_subcmd_config.sub_commands)
                    tokens.extend(subcmd_tokens)
                    return tokens

                # Then check if arg is OPTION_VALUE (if not subcommand and has current_option_argconfig)
                elif current_option_argconfig:
                    if not current_option_argconfig.nargs.validate_count(current_option_value_num + 1):
                        raise ValueError("current_option_argconfig state error, should not enter this branch")
                    
                    tokens.append(CommandToken(
                        token_type=TokenType.OPTION_VALUE,
                        values=[arg]
                    ))

                    current_option_value_num += 1

                # Not subcommand and not option_value, so must be positional value (if positional value exists).
                else:
                    positional_value_config = ArgparseParser._get_positional_arg_config(arguments_config)
                    if positional_value_config is None:
                        raise ValueError(f"No positional argument configuration. arguments_config: {arguments_config}")
                    
                    if positional_value_config.nargs.validate_count(current_positional_value_num + 1):
                        tokens.append(CommandToken(
                            token_type=TokenType.POSITIONAL_ARG,
                            values=[arg]
                        ))

                        current_positional_value_num += 1
                    else:
                        raise ValueError(f"Too many positional arguments. positional_value_config.nargs: {positional_value_config.nargs}, current_positional_value_num: {current_positional_value_num}")

                    # Since there's positional value, no subcommand, handle in next loop

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
            if subcmd.matches_subcmd_name(sub_cmd_name):
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
        Validate if parsing result conforms to configuration
        
        Args:
            command_node: Parsed command tree
            
        Returns:
            bool: Whether validation passed
        """

        # Already validated during _tokenize and build_command_tree
        return True