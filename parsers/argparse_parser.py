"""
argparse 风格命令行解析器
"""

from typing import List, Dict, Any, Optional
from .types import CommandToken, TokenType, CommandNode, CommandArg, ArgType, ParserConfig, ArgumentConfig, SubCommandConfig
from .base import BaseParser

from log import debug, info, warning, error


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
                # 查找选项配置（全局选项在任何位置都有效）
                option_config = self._find_option_config(arg)
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
    
    def _is_global_option(self, option_name: str) -> bool:
        """检查选项是否是全局选项"""
        # 检查是否是根节点的配置参数
        for arg_config in self.parser_config.arguments:
            if option_name in arg_config.opt:
                debug(f"选项 '{option_name}' 是全局选项")
                return True
        
        debug(f"选项 '{option_name}' 不是全局选项")
        return False
    
    def _build_command_tree(self, tokens: List[CommandToken]) -> CommandNode:
        """从 token 列表构建命令树"""
        if not tokens:
            error("没有命令行参数")
            raise ValueError("没有命令行参数")
        
        program_token = tokens[0]
        if not program_token.is_program():
            error(f"第一个 token 不是程序名: {program_token}")
            raise ValueError("第一个 token 必须是程序名")
        
        root_node = CommandNode(name=program_token.get_first_value() or "")
        debug(f"创建命令树根节点: {root_node.name}")
        
        i = 1  # 跳过程序名
        n = len(tokens)
        
        current_node = root_node
        
        # 用于跟踪重复的标志（按配置名称分组，而不是按选项名称）
        flag_counts = {}
        
        # 用于收集位置参数
        positional_args = []
        
        while i < n:
            token = tokens[i]
            debug(f"构建命令树，处理 token [{i}]: {token}")
            
            if token.token_type == TokenType.SUBCOMMAND:
                # 先处理之前收集的位置参数
                if positional_args:
                    debug(f"添加收集的位置参数: {positional_args}")
                    current_node.arguments.append(CommandArg(
                        node_type=ArgType.POSITIONAL,
                        values=positional_args.copy()
                    ))
                    positional_args.clear()
                
                # 创建子命令节点
                subcommand_name = token.get_first_value() or ""
                debug(f"创建子命令节点: {subcommand_name}")
                current_node.subcommand = CommandNode(name=subcommand_name)
                current_node = current_node.subcommand
            
            elif token.token_type == TokenType.SEPARATOR:
                # 遇到分隔符，先处理之前收集的位置参数
                if positional_args:
                    debug(f"添加收集的位置参数: {positional_args}")
                    current_node.arguments.append(CommandArg(
                        node_type=ArgType.POSITIONAL,
                        values=positional_args.copy()
                    ))
                    positional_args.clear()
                debug("遇到分隔符，开始额外参数模式")
            
            elif token.is_flag():
                # 检查是否是全局选项
                option_name = token.get_first_value() or ""
                is_global_option = self._is_global_option(option_name)
                
                if is_global_option:
                    # 全局选项应该添加到根节点
                    debug(f"全局选项 '{option_name}' 添加到根节点")
                    target_node = root_node
                    # 查找配置名称
                    config_name = self._find_config_name_for_option(option_name, is_global=True)
                else:
                    # 子命令选项添加到当前节点
                    debug(f"子命令选项 '{option_name}' 添加到当前节点")
                    target_node = current_node
                    # 查找配置名称
                    config_name = self._find_config_name_for_option(option_name, is_global=False)
                
                # 先处理之前收集的位置参数
                if positional_args:
                    debug(f"添加收集的位置参数: {positional_args}")
                    current_node.arguments.append(CommandArg(
                        node_type=ArgType.POSITIONAL,
                        values=positional_args.copy()
                    ))
                    positional_args.clear()
                
                # 处理标志
                debug(f"添加标志: {option_name} (配置: {config_name})")
                
                # 统计重复次数（按配置名称分组）
                node_key = id(target_node)
                if node_key not in flag_counts:
                    flag_counts[node_key] = {}
                
                if config_name in flag_counts[node_key]:
                    flag_counts[node_key][config_name] += 1
                    debug(f"标志 '{config_name}' 重复次数: {flag_counts[node_key][config_name]}")
                else:
                    flag_counts[node_key][config_name] = 1
                    # 第一次遇到这个配置的标志，添加到参数列表
                    target_node.arguments.append(CommandArg(
                        node_type=ArgType.FLAG,
                        option_name=option_name,  # 使用第一个遇到的选项名称
                        values=[],
                        repeat=1
                    ))
                    debug(f"标志 '{config_name}' 重复次数: {flag_counts[node_key][config_name]}")
            
            elif token.token_type == TokenType.OPTION_NAME:
                # 检查是否是全局选项
                option_name = token.get_first_value()
                is_global_option = self._is_global_option(option_name)
                
                if is_global_option:
                    # 全局选项应该添加到根节点
                    debug(f"全局选项 '{option_name}' 添加到根节点")
                    target_node = root_node
                else:
                    # 子命令选项添加到当前节点
                    debug(f"子命令选项 '{option_name}' 添加到当前节点")
                    target_node = current_node
                
                # 先处理之前收集的位置参数
                if positional_args:
                    debug(f"添加收集的位置参数: {positional_args}")
                    current_node.arguments.append(CommandArg(
                        node_type=ArgType.POSITIONAL,
                        values=positional_args.copy()
                    ))
                    positional_args.clear()
                
                # 处理选项
                option_values = []
                
                # 收集选项值
                j = i + 1
                debug(f"开始收集选项 '{option_name}' 的值")
                while j < n and tokens[j].token_type == TokenType.OPTION_VALUE:
                    value = tokens[j].get_first_value() or ""
                    option_values.append(value)
                    debug(f"  选项值: {value}")
                    j += 1
                
                i = j - 1  # 跳过已处理的值
                debug(f"选项 '{option_name}' 共有 {len(option_values)} 个值: {option_values}")
                
                target_node.arguments.append(CommandArg(
                    node_type=ArgType.OPTION,
                    option_name=option_name,
                    values=option_values
                ))
            
            elif token.token_type == TokenType.POSITIONAL_ARG:
                # 收集位置参数，稍后统一处理
                positional_args.extend(token.values)
                debug(f"收集位置参数: {token.values}, 当前总数: {len(positional_args)}")
            
            elif token.token_type == TokenType.EXTRA_ARG:
                # 先处理之前收集的位置参数
                if positional_args:
                    debug(f"添加收集的位置参数: {positional_args}")
                    current_node.arguments.append(CommandArg(
                        node_type=ArgType.POSITIONAL,
                        values=positional_args.copy()
                    ))
                    positional_args.clear()
                
                # 处理额外参数
                debug(f"添加额外参数: {token.values}")
                current_node.arguments.append(CommandArg(
                    node_type=ArgType.EXTRA,
                    values=token.values
                ))
            
            i += 1
        
        # 处理最后收集的位置参数
        if positional_args:
            debug(f"添加最后收集的位置参数: {positional_args}")
            current_node.arguments.append(CommandArg(
                node_type=ArgType.POSITIONAL,
                values=positional_args.copy()
            ))
        
        # 更新标志的重复次数
        def update_flag_counts(node: CommandNode):
            node_key = id(node)
            if node_key in flag_counts:
                for arg in node.arguments:
                    if arg.node_type == ArgType.FLAG:
                        # 查找这个选项对应的配置名称
                        config_name = self._find_config_name_for_option(arg.option_name, node == root_node)
                        if config_name in flag_counts[node_key]:
                            arg.repeat = flag_counts[node_key][config_name]
                            debug(f"设置标志 '{arg.option_name}' (配置: {config_name}) 的重复次数为: {arg.repeat}")
            if node.subcommand:
                update_flag_counts(node.subcommand)
        
        update_flag_counts(root_node)
        
        debug(f"命令树构建完成")
        return root_node

    def _find_config_name_for_option(self, option_name: str, is_global: bool = False) -> Optional[str]:
        """根据选项名称查找对应的配置名称"""
        if is_global:
            # 在全局参数中查找
            for arg_config in self.parser_config.arguments:
                if option_name in arg_config.opt:
                    return arg_config.name
        else:
            # 在所有子命令参数中查找
            for sub_cmd in self.parser_config.sub_commands:
                for arg_config in sub_cmd.arguments:
                    if option_name in arg_config.opt:
                        return arg_config.name
        return None
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
        
        # 检查是否有子命令（如果有子命令配置，则必须提供子命令）
        if config.sub_commands and not command_node.subcommand:
            debug("❌ 验证失败: 配置中有子命令但命令行未提供子命令")
            validation_passed = False
        
        while current_node:
            debug(f"验证节点: {current_node.name}")
            
            # 如果是子命令，获取对应的配置
            if current_node != command_node:  # 不是根节点
                sub_cmd_config = config.find_subcommand(current_node.name)
                if sub_cmd_config:
                    config_to_validate = sub_cmd_config
                else:
                    debug(f"❌ 未找到子命令配置: {current_node.name}")
                    validation_passed = False
                    break
            else:
                config_to_validate = config
            
            # 验证参数
            for arg_config in config_to_validate.arguments:
                debug(f"验证参数: {arg_config.name}, nargs: {arg_config.nargs}, required: {arg_config.required}")
                
                # 查找对应的命令参数
                cmd_args = []
                for arg in current_node.arguments:
                    if arg.option_name and arg.option_name in arg_config.opt:
                        cmd_args.append(arg)
                        debug(f"  找到选项参数: {arg.option_name}")
                    elif not arg.option_name and arg_config.is_positional() and arg.node_type == ArgType.POSITIONAL:
                        cmd_args.append(arg)
                        debug(f"  找到位置参数: {arg_config.name}")
                
                debug(f"找到 {len(cmd_args)} 个匹配的参数")
                
                if cmd_args:
                    # 检查参数数量
                    actual_count = len(cmd_args[0].values)
                    if not arg_config.validate_count(actual_count):
                        debug(f"❌ 验证失败: 参数 {arg_config.name} 需要 {arg_config.nargs} 个值，实际有 {actual_count} 个")
                        validation_passed = False
                    else:
                        debug(f"✅ 参数 {arg_config.name} 数量验证通过")
                else:
                    # 参数不存在，检查是否是必需的
                    if arg_config.is_required():
                        debug(f"❌ 验证失败: 必需参数 {arg_config.name} 不存在")
                        validation_passed = False
                    else:
                        debug(f"✅ 参数 {arg_config.name} 是可选的，验证通过")
            
            # 移动到子命令
            current_node = current_node.subcommand
        
        if validation_passed:
            debug("✅ 命令验证通过")
        else:
            debug("❌ 命令验证失败")
        
        return validation_passed