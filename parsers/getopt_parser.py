"""
getopt 风格命令行解析器
"""

from typing import List, Dict, Any, Optional
from .types import CommandToken, TokenType, CommandNode, CommandArg, ArgType, ParserConfig, ArgumentConfig, ArgumentCount
from .base import BaseParser

from log import debug, info, warning, error

class GetoptParser(BaseParser):
    """getopt 风格命令行解析器"""
    
    def __init__(self, parser_config: ParserConfig):
        """
        初始化 getopt 解析器
        
        Args:
            parser_config: 解析器配置
        """
        super().__init__(parser_config)
        debug(f"初始化 GetoptParser，程序名: {parser_config.program_name}")
        debug(f"配置参数数量: {len(parser_config.arguments)}")
        for arg in parser_config.arguments:
            debug(f"  参数: {arg.name}, 选项: {arg.opt}, nargs: {arg.nargs}")
    
    def parse(self, args: List[str]) -> CommandNode:
        """
        解析 getopt 风格命令行
        
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
        
        while i < n:
            arg = args[i]
            debug(f"处理参数 [{i}]: '{arg}', 当前选项: {current_option}, 在选项阶段: {in_options}")
            
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
                # 查找选项配置
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
                        debug(f"长选项带等号值: {opt_name} = {opt_value}")
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
                    if len(arg) > 1:
                        # 组合短选项，如 -xyz
                        debug(f"处理组合短选项: {arg}")
                        for char_index, char in enumerate(arg[1:]):
                            short_opt = f"-{char}"
                            opt_config = self._find_option_config(short_opt)
                            debug(f"  短选项 '{short_opt}' 配置: {opt_config.name if opt_config else '未找到'}")
                            
                            if opt_config and opt_config.accepts_values() and char_index == len(arg[1:]) - 1:
                                # 如果接受值，只能是最后一个字符
                                debug(f"  选项 '{short_opt}' 接受值，设置为当前选项")
                                current_option = short_opt
                                current_option_config = opt_config
                            else:
                                debug(f"  选项 '{short_opt}' 作为标志处理")
                                tokens.append(CommandToken(
                                    token_type=TokenType.FLAG,
                                    values=[short_opt]
                                ))
                    else:
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
    
    def _find_option_config(self, option_name: str) -> Optional[ArgumentConfig]:
        """根据选项名称查找配置"""
        for arg_config in self.parser_config.arguments:
            if option_name in arg_config.opt:
                debug(f"找到选项 '{option_name}' 的配置: {arg_config.name}")
                return arg_config
        debug(f"未找到选项 '{option_name}' 的配置")
        return None
    
    def _build_command_tree(self, tokens: List[CommandToken]) -> CommandNode:
        """从 token 列表构建命令树"""
        if not tokens:
            error("没有命令行参数")
            raise ValueError("没有命令行参数")
        
        # getopt 没有子命令概念，所有参数都在根节点
        program_token = tokens[0]
        if not program_token.is_program():
            error(f"第一个 token 不是程序名: {program_token}")
            raise ValueError("第一个 token 必须是程序名")
        
        root_node = CommandNode(name=program_token.get_first_value() or "")
        debug(f"创建命令树根节点: {root_node.name}")
        
        i = 1  # 跳过程序名
        n = len(tokens)
        
        # 收集位置参数
        positional_args = []
        
        # 用于跟踪重复的标志
        flag_counts = {}
        
        while i < n:
            token = tokens[i]
            debug(f"构建命令树，处理 token [{i}]: {token}")
            
            if token.is_flag():
                # 查找标志配置
                option_name = token.get_first_value() or ""
                option_config = self._find_option_config(option_name)
                debug(f"添加标志: {option_name}")
                
                # 统计重复次数
                if option_name in flag_counts:
                    flag_counts[option_name] += 1
                else:
                    flag_counts[option_name] = 1
                    # 第一次遇到这个标志，添加到参数列表
                    root_node.arguments.append(CommandArg(
                        node_type=ArgType.FLAG,
                        option_name=option_name,
                        values=[],
                        repeat=1
                    ))
                debug(f"标志 '{option_name}' 重复次数: {flag_counts[option_name]}")
                
            elif token.token_type == TokenType.OPTION_NAME:
                # 选项名，需要查找对应的值
                option_name = token.get_first_value()
                option_config = self._find_option_config(option_name or "")
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
                
                root_node.arguments.append(CommandArg(
                    node_type=ArgType.OPTION,
                    option_name=option_name,
                    values=option_values
                ))
            elif token.token_type == TokenType.POSITIONAL_ARG:
                # 收集位置参数，稍后统一处理
                positional_args.extend(token.values)
                debug(f"收集位置参数: {token.values}, 当前总数: {len(positional_args)}")
            elif token.token_type == TokenType.EXTRA_ARG:
                debug(f"额外参数: {token.values}")
                root_node.arguments.append(CommandArg(
                    node_type=ArgType.EXTRA,
                    values=token.values
                ))
            
            i += 1
        
        # 更新标志的重复次数
        for arg in root_node.arguments:
            if arg.node_type == ArgType.FLAG and arg.option_name in flag_counts:
                arg.repeat = flag_counts[arg.option_name]
                debug(f"设置标志 '{arg.option_name}' 的重复次数为: {arg.repeat}")
        
        # 处理收集的位置参数
        if positional_args:
            debug(f"处理 {len(positional_args)} 个位置参数: {positional_args}")
            # 查找位置参数配置
            positional_configs = self.parser_config.get_positional_arguments()
            if positional_configs and len(positional_configs) > 0:
                config = positional_configs[0]  # 只取第一个位置参数配置
                debug(f"使用位置参数配置: {config.name}")
                root_node.arguments.append(CommandArg(
                    node_type=ArgType.POSITIONAL,
                    option_name=config.name,
                    values=positional_args
                ))
            else:
                # 没有位置参数配置
                debug("没有位置参数配置，使用默认处理")
                root_node.arguments.append(CommandArg(
                    node_type=ArgType.POSITIONAL,
                    values=positional_args
                ))
        
        debug(f"命令树构建完成，共有 {len(root_node.arguments)} 个参数")
        return root_node

    def validate(self, command_node: CommandNode) -> bool:
        """
        验证解析结果是否符合配置
        """
        debug("开始验证命令树")
        validation_passed = True
        
        for arg_config in self.parser_config.arguments:
            debug(f"验证参数: {arg_config.name}, nargs: {arg_config.nargs}, required: {arg_config.required}")
            
            # 查找对应的命令参数
            cmd_args = []
            for arg in command_node.arguments:
                debug(f"  检查命令参数: {arg.option_name}, node_type: {arg.node_type}, values: {arg.values}")
                
                if arg.option_name and arg.option_name in arg_config.opt:
                    # 选项参数
                    cmd_args.append(arg)
                    debug(f"    匹配选项参数: {arg.option_name}")
                elif arg_config.is_positional() and arg.node_type == ArgType.POSITIONAL:
                    # 位置参数 - 检查参数名称是否匹配
                    if arg.option_name == arg_config.name:
                        cmd_args.append(arg)
                        debug(f"    匹配位置参数: {arg_config.name}")
                    elif not arg.option_name and not arg_config.opt:
                        # 没有名称的位置参数匹配没有选项的位置参数配置
                        cmd_args.append(arg)
                        debug(f"    匹配无名位置参数: {arg_config.name}")
            
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
        
        if validation_passed:
            debug("✅ 命令验证通过")
        else:
            debug("❌ 命令验证失败")
        
        return validation_passed