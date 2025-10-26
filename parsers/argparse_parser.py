"""
argparse 风格命令行解析器
"""

from typing import List, Dict, Any, Optional, Tuple
from .types import CommandToken, TokenType, CommandNode, CommandArg, ArgType, ParserConfig, ArgumentConfig, SubCommandConfig
from .base import BaseParser

from log import debug, info, warning, error
from .utils import Utils

class ArgparseParser(BaseParser):
    """argparse 风格命令行解析器"""
    
    def __init__(self, parser_config: ParserConfig):
        """
        初始化 argparse 解析器
        
        Args:
            parser_config: 解析器配置
        """
        super().__init__(parser_config)
        debug(f"初始化 ArgparseParser，程序名: {parser_config.program_name}")
        debug(f"配置参数数量: {len(parser_config.arguments)}")
        debug(f"子命令数量: {len(parser_config.sub_commands)}")
        for arg in parser_config.arguments:
            debug(f"  全局参数: {arg.name}, 选项: {arg.opt}, nargs: {arg.nargs}")
        for sub_cmd in parser_config.sub_commands:
            debug(f"  子命令: {sub_cmd.name}, 参数数量: {len(sub_cmd.arguments)}")
    
    def parse(self, args: List[str]) -> CommandNode:
        """
        解析 argparse 风格命令行
        
        Args:
            args: 命令行参数列表
            
        Returns:
            CommandNode: 解析后的命令树
        """
        debug(f"开始解析命令行: {args}")
        tokens = self._tokenize(args)
        debug(f"生成的 tokens: {[str(t) for t in tokens]}")
        result = self._build_command_tree(tokens)
        debug(f"构建的命令树: {result.name}, 参数数量: {len(result.arguments)}")
        return result
    
    def _tokenize(self, args: List[str]) -> List[CommandToken]:
        """将命令行参数转换为 token 列表"""
        tokens = []
        i = 0
        n = len(args)
        
        # 第一个参数是程序名
        if args:
            tokens.append(CommandToken(
                token_type=TokenType.PROGRAM,
                values=[args[0]]
            ))
            debug(f"识别程序名: {args[0]}")
            i += 1
        
        in_options = True  # 是否在解析选项阶段
        current_option = None  # 当前正在解析的选项
        current_option_config = None  # 当前选项的配置
        found_subcommand = False  # 是否找到了子命令
        current_subcommand = None  # 当前子命令名称
        
        while i < n:
            arg = args[i]
            debug(f"处理参数 [{i}]: '{arg}', 当前选项: {current_option}, 在选项阶段: {in_options}, 找到子命令: {found_subcommand}")
            
            if arg == "--":
                # 分隔符，后面的都是额外参数
                tokens.append(CommandToken(
                    token_type=TokenType.SEPARATOR,
                    values=["--"]
                ))
                debug("遇到分隔符 '--'，切换到额外参数模式")
                in_options = False
                i += 1
                continue
            
            if in_options and arg.startswith("-"):
                # 查找选项配置 - 根据是否找到子命令决定查找范围
                option_config = None
                
                if found_subcommand and current_subcommand:
                    # 在子命令中查找选项配置
                    sub_cmd_config = self.parser_config.find_subcommand(current_subcommand)
                    if sub_cmd_config:
                        for arg_config in sub_cmd_config.arguments:
                            if arg in arg_config.opt:
                                option_config = arg_config
                                debug(f"在子命令 '{current_subcommand}' 中找到选项 '{arg}' 的配置: {arg_config.name}")
                                break
                
                # 如果没在子命令中找到，再在全局中查找
                if not option_config:
                    option_config = self._find_option_config(arg)
                    if option_config:
                        debug(f"在全局参数中找到选项 '{arg}' 的配置: {option_config.name}")
                
                debug(f"选项 '{arg}' 的配置: {option_config.name if option_config else '未找到'}")
                
                if current_option:
                    # 上一个选项缺少值，作为标志处理
                    debug(f"上一个选项 '{current_option}' 缺少值，作为标志处理")
                    tokens.append(CommandToken(
                        token_type=TokenType.FLAG,
                        values=[current_option]
                    ))
                    current_option = None
                    current_option_config = None
                
                if arg.startswith("--"):
                    # 长选项
                    current_option = arg
                    current_option_config = option_config
                    debug(f"设置当前长选项: {arg}")
                    
                    # 检查是否有等号形式的值
                    if "=" in arg:
                        opt_name, opt_value = arg.split("=", 1)
                        tokens.append(CommandToken(
                            token_type=TokenType.OPTION_NAME,
                            values=[opt_name]
                        ))
                        tokens.append(CommandToken(
                            token_type=TokenType.OPTION_VALUE,
                            values=[opt_value]
                        ))
                        current_option = None
                        current_option_config = None
                else:
                    # 短选项
                    current_option = arg
                    current_option_config = option_config
                    debug(f"设置当前短选项: {arg}")
            else:
                # 位置参数或选项值
                if current_option and current_option_config and current_option_config.accepts_values():
                    # 当前选项的值
                    debug(f"参数 '{arg}' 作为选项 '{current_option}' 的值")
                    tokens.append(CommandToken(
                        token_type=TokenType.OPTION_NAME,
                        values=[current_option]
                    ))
                    tokens.append(CommandToken(
                        token_type=TokenType.OPTION_VALUE,
                        values=[arg]
                    ))
                    current_option = None
                    current_option_config = None
                else:
                    # 检查是否是子命令
                    if not found_subcommand and self._is_subcommand(arg):
                        debug(f"参数 '{arg}' 识别为子命令")
                        tokens.append(CommandToken(
                            token_type=TokenType.SUBCOMMAND,
                            values=[arg]
                        ))
                        found_subcommand = True
                        current_subcommand = arg
                    else:
                        # 位置参数
                        token_type = (TokenType.EXTRA_ARG if not in_options 
                                    else TokenType.POSITIONAL_ARG)
                        debug(f"参数 '{arg}' 作为 {token_type.value}")
                        tokens.append(CommandToken(
                            token_type=token_type,
                            values=[arg]
                        ))
            
            i += 1
        
        # 处理最后一个选项
        if current_option:
            if current_option_config and current_option_config.accepts_values():
                # 选项需要值但没有提供
                debug(f"选项 '{current_option}' 需要值但未提供")
                tokens.append(CommandToken(
                    token_type=TokenType.OPTION_NAME,
                    values=[current_option]
                ))
            else:
                debug(f"处理最后一个选项 '{current_option}' 作为标志")
                tokens.append(CommandToken(
                    token_type=TokenType.FLAG,
                    values=[current_option]
                ))
        
        debug(f"tokenization 完成，生成 {len(tokens)} 个 tokens")
        return tokens
    
    def _is_subcommand(self, arg: str) -> bool:
        """检查参数是否是子命令"""
        for sub_cmd in self.parser_config.sub_commands:
            if sub_cmd.name == arg:
                return True
        return False
    
    def _find_option_config(self, option_name: str) -> Optional[ArgumentConfig]:
        """根据选项名称查找配置"""
        # 先检查全局参数（全局选项在任何位置都有效）
        for arg_config in self.parser_config.arguments:
            if option_name in arg_config.opt:
                debug(f"在全局参数中找到选项 '{option_name}' 的配置: {arg_config.name}")
                return arg_config
        
        # 再检查所有子命令的参数
        for sub_cmd in self.parser_config.sub_commands:
            for arg_config in sub_cmd.arguments:
                if option_name in arg_config.opt:
                    debug(f"在子命令 '{sub_cmd.name}' 中找到选项 '{option_name}' 的配置: {arg_config.name}")
                    return arg_config
        
        debug(f"未找到选项 '{option_name}' 的配置")
        return None
    
    def _build_command_tree(self, tokens: List[CommandToken]) -> CommandNode:
        if not tokens:
            error("没有命令行参数")
            raise ValueError("没有命令行参数")
        
        # 1. 分割 tokens
        main_tokens, subcommand_name, subcommand_tokens = self._split_tokens_by_subcommand(tokens)
        
        # 打印分割结果
        debug(f"🎯 tokens 分割结果:")
        debug(f"  主命令 tokens ({len(main_tokens)} 个):")
        for i, token in enumerate(main_tokens):
            debug(f"    [{i}] {token}")
        
        debug(f"  子命令名称: {subcommand_name}")
        debug(f"  子命令 tokens ({len(subcommand_tokens)} 个):")
        for i, token in enumerate(subcommand_tokens):
            debug(f"    [{i}] {token}")

        # 2. 构建根节点（使用全局参数配置）
        root_node = self._build_command_node(main_tokens, self.parser_config.arguments)
        
        # 3. 如果有子命令，构建子命令节点
        if subcommand_name and subcommand_tokens:
            # 查找子命令配置
            sub_cmd_config = self.parser_config.find_subcommand(subcommand_name)
            if sub_cmd_config:
                subcommand_node = self._build_command_node(
                    subcommand_tokens, 
                    sub_cmd_config.arguments
                )
                root_node.subcommand = subcommand_node
            else:
                warning(f"未找到子命令 '{subcommand_name}' 的配置")
        
        debug(f"命令树构建完成")
        # 添加命令树打印
        debug("\n🌳 命令树结构:")
        Utils.print_command_tree(root_node)
        debug("")

        return root_node
    
    def _split_tokens_by_subcommand(self, tokens: List[CommandToken]) -> Tuple[List[CommandToken], Optional[str], List[CommandToken]]:
        """
        根据子命令分割 tokens
        
        Returns:
            Tuple: (主命令tokens, 子命令名称, 子命令tokens)
        """
        main_tokens = []
        subcommand_name = None
        subcommand_tokens = []
        
        found_subcommand = False
        
        for token in tokens:
            if not found_subcommand:
                if token.token_type == TokenType.SUBCOMMAND:
                    # 找到子命令
                    subcommand_name = token.get_first_value()
                    found_subcommand = True
                    subcommand_tokens.append(token)
                else:
                    # 子命令之前的所有 token 都属于主命令
                    main_tokens.append(token)
            else:
                # 子命令之后的所有 token 都属于子命令
                subcommand_tokens.append(token)
        
        return main_tokens, subcommand_name, subcommand_tokens
    
    def _build_command_node(self, tokens: List[CommandToken], config_arguments: List[ArgumentConfig]) -> CommandNode:
        """
        构建命令节点（统一处理主命令和子命令）
        
        Args:
            tokens: 该节点的 tokens
            config_arguments: 该节点对应的参数配置
        """
        if not tokens:
            raise ValueError("没有 tokens")
        
        # 节点名称从第一个 token 获取
        node_name = tokens[0].get_first_value() or ""
        node = CommandNode(name=node_name)
        debug(f"创建命令节点: {node_name}")
        
        # 处理参数 tokens（跳过第一个程序名/子命令名）
        i = 1
        n = len(tokens)
        
        flag_counts = {}
        positional_args = []
        
        while i < n:
            token = tokens[i]
            debug(f"处理 token [{i}]: {token}")
            
            if token.is_flag():
                i = self._process_flag_token(token, node, flag_counts, config_arguments, tokens, i)
            elif token.token_type == TokenType.OPTION_NAME:
                i = self._process_option_token(token, node, config_arguments, tokens, i)
            elif token.token_type == TokenType.POSITIONAL_ARG:
                positional_args.extend(token.values)
                debug(f"收集位置参数: {token.values}, 当前总数: {len(positional_args)}")
            elif token.token_type == TokenType.EXTRA_ARG:
                self._process_extra_token(token, node)
            elif token.token_type == TokenType.SEPARATOR:
                # 分隔符后的都是额外参数
                debug("遇到分隔符，后续参数作为额外参数")
                if positional_args:
                    self._add_positional_args(node, positional_args, config_arguments)
                    positional_args.clear()
                
                # 剩余 tokens 都作为额外参数
                extra_values = []
                j = i + 1
                while j < n:
                    extra_values.extend(tokens[j].values)
                    j += 1
                
                if extra_values:
                    node.arguments.append(CommandArg(
                        node_type=ArgType.EXTRA,
                        values=extra_values
                    ))
                    debug(f"添加额外参数: {extra_values}")
                break
            
            i += 1
        
        # 处理最后收集的位置参数
        if positional_args:
            self._add_positional_args(node, positional_args, config_arguments)
        
        # 更新标志重复次数
        self._update_flag_repeats(node, flag_counts)
        
        return node
    
    def _process_flag_token(self, token: CommandToken, node: CommandNode, 
                        flag_counts: Dict, config_arguments: List[ArgumentConfig],
                        tokens: List[CommandToken], i: int) -> int:
        """处理标志 token"""
        option_name = token.get_first_value() or ""
        config_name = self._find_config_name_for_option(option_name, config_arguments)
        
        if not config_name:
            debug(f"警告：未找到选项 '{option_name}' 的配置")
            return i
        
        debug(f"添加标志: {option_name} (配置: {config_name})")
        
        # 统计重复次数 - 使用配置名作为键
        node_key = id(node)
        if node_key not in flag_counts:
            flag_counts[node_key] = {}
        
        if config_name in flag_counts[node_key]:
            flag_counts[node_key][config_name] += 1
            debug(f"标志 '{config_name}' 重复次数: {flag_counts[node_key][config_name]}")
        else:
            flag_counts[node_key][config_name] = 1
            node.arguments.append(CommandArg(
                node_type=ArgType.FLAG,
                option_name=option_name,  # 仍然保存原始选项名
                values=[],
                repeat=1
            ))
        
        return i

    def _process_option_token(self, token: CommandToken, node: CommandNode,
                            config_arguments: List[ArgumentConfig], tokens: List[CommandToken], i: int) -> int:
        """处理选项 token"""
        option_name = token.get_first_value()
        
        # 收集选项值
        option_values = []
        j = i + 1
        debug(f"开始收集选项 '{option_name}' 的值")
        while j < len(tokens) and tokens[j].token_type == TokenType.OPTION_VALUE:
            value = tokens[j].get_first_value() or ""
            option_values.append(value)
            debug(f"  选项值: {value}")
            j += 1
        
        new_i = j - 1  # 跳过已处理的值
        debug(f"选项 '{option_name}' 共有 {len(option_values)} 个值: {option_values}")
        
        node.arguments.append(CommandArg(
            node_type=ArgType.OPTION,
            option_name=option_name,
            values=option_values
        ))
        
        return new_i

    def _add_positional_args(self, node: CommandNode, positional_args: List[str], 
                            config_arguments: List[ArgumentConfig]):
        """添加位置参数到节点"""
        debug(f"添加位置参数: {positional_args}")
        
        # 查找位置参数配置
        positional_configs = [c for c in config_arguments if c.is_positional()]
        
        if positional_configs:
            # 使用配置中的位置参数名称
            config = positional_configs[0]
            node.arguments.append(CommandArg(
                node_type=ArgType.POSITIONAL,
                option_name=config.name,
                values=positional_args.copy()
            ))
        else:
            # 没有配置，使用无名位置参数
            node.arguments.append(CommandArg(
                node_type=ArgType.POSITIONAL,
                values=positional_args.copy()
            ))

    def _find_config_name_for_option(self, option_name: str, config_arguments: List[ArgumentConfig]) -> Optional[str]:
        """在给定的配置中查找选项对应的配置名称"""
        for arg_config in config_arguments:
            if option_name in arg_config.opt:
                return arg_config.name
        return None
    
    def _update_flag_repeats(self, node: CommandNode, flag_counts: Dict):
        """更新标志的重复次数"""
        node_key = id(node)
        if node_key in flag_counts:
            # 确定当前节点对应的配置参数
            config_arguments = self._get_config_arguments_for_node(node)
            
            for arg in node.arguments:
                if arg.node_type == ArgType.FLAG and arg.option_name:
                    # 使用正确的配置参数查找配置名
                    config_name = self._find_config_name_for_option(arg.option_name, config_arguments)
                    if config_name and config_name in flag_counts[node_key]:
                        arg.repeat = flag_counts[node_key][config_name]
                        debug(f"设置标志 '{arg.option_name}' (配置: {config_name}) 的重复次数为: {arg.repeat}")
        
        # 递归更新子命令
        if node.subcommand:
            self._update_flag_repeats(node.subcommand, flag_counts)

    def _get_config_arguments_for_node(self, node: CommandNode) -> List[ArgumentConfig]:
        """简化版本：获取节点对应的配置参数"""
        # 如果是程序名，使用全局参数
        if node.name == self.parser_config.program_name:
            return self.parser_config.arguments
        
        # 否则查找子命令配置
        sub_cmd_config = self.parser_config.find_subcommand(node.name)
        if sub_cmd_config:
            return sub_cmd_config.arguments
        
        # 如果都没找到，返回空列表
        return []

    def validate(self, command_node: CommandNode) -> bool:
        """
        验证解析结果是否符合配置
        
        Args:
            command_node: 解析后的命令树
            
        Returns:
            bool: 是否验证通过
        """
        debug("开始验证命令树")
        validation_passed = True
        
        # 验证当前节点
        current_node = command_node
        config = self.parser_config
        
        while current_node:
            debug(f"验证节点: {current_node.name}")
            
            # 检查节点配置是否存在
            if current_node != command_node:  # 子命令
                sub_cmd_config = config.find_subcommand(current_node.name)
                if not sub_cmd_config:
                    debug(f"❌ 未找到子命令配置: {current_node.name}")
                    validation_passed = False
                    break
                config_to_validate = sub_cmd_config
            else:  # 根节点
                config_to_validate = config
            
            # 使用通用函数验证参数
            if not self._validate_arguments(current_node.arguments, config_to_validate.arguments):
                validation_passed = False
            
            current_node = current_node.subcommand
        
        if validation_passed:
            debug("✅ 命令验证通过")
        else:
            debug("❌ 命令验证失败")
        
        return validation_passed

    def _validate_arguments(self, parsed_arguments: List[CommandArg], config_arguments: List[ArgumentConfig]) -> bool:
        """
        通用参数验证函数
        
        Args:
            parsed_arguments: 解析出的参数
            config_arguments: 配置的参数
            
        Returns:
            bool: 验证是否通过
        """
        validation_passed = True
        
        # 分离位置参数和选项参数
        positional_configs = [c for c in config_arguments if c.is_positional()]
        option_configs = [c for c in config_arguments if not c.is_positional()]
        
        parsed_positionals = [a for a in parsed_arguments 
                            if a.node_type == ArgType.POSITIONAL and not a.option_name]
        parsed_options = [a for a in parsed_arguments 
                        if a.node_type in (ArgType.OPTION, ArgType.FLAG)]
        
        # 验证位置参数（按顺序匹配）
        for i, pos_config in enumerate(positional_configs):
            if i < len(parsed_positionals):
                actual_count = len(parsed_positionals[i].values)
                if not pos_config.validate_count(actual_count):
                    debug(f"❌ 位置参数验证失败: {pos_config.name} 需要 {pos_config.nargs} 个值，实际有 {actual_count} 个")
                    validation_passed = False
                else:
                    debug(f"✅ 位置参数验证通过: {pos_config.name}")
            elif pos_config.is_required():
                debug(f"❌ 必需位置参数缺失: {pos_config.name}")
                validation_passed = False
        
        # 验证选项参数（按名称匹配）
        for opt_config in option_configs:
            matched_args = []
            for parsed_arg in parsed_options:
                if parsed_arg.option_name and parsed_arg.option_name in opt_config.opt:
                    matched_args.append(parsed_arg)
            
            if matched_args:
                # 对于选项，通常只关心第一个匹配的参数
                actual_count = len(matched_args[0].values)
                if not opt_config.validate_count(actual_count):
                    debug(f"❌ 选项参数验证失败: {opt_config.name} 需要 {opt_config.nargs} 个值，实际有 {actual_count} 个")
                    validation_passed = False
                else:
                    debug(f"✅ 选项参数验证通过: {opt_config.name}")
            elif opt_config.is_required():
                debug(f"❌ 必需选项参数缺失: {opt_config.name}")
                validation_passed = False
        
        return validation_passed