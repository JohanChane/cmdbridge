from typing import List
from .types import CommandNode, CommandArg
from log import debug

class Utils:
    @staticmethod
    def print_command_tree(node: CommandNode, level: int = 0):
        """打印命令树结构（用于调试）"""
        indent = "  " * level
        debug(f"{indent}└── {node.name}")
        
        # 打印当前节点的参数
        for arg in node.arguments:
            arg_info = Utils._format_command_arg(arg)
            debug(f"{indent}    ├── {arg_info}")
        
        # 递归打印子命令
        if node.subcommand:
            Utils.print_command_tree(node.subcommand, level + 1)

    @staticmethod
    def _format_command_arg(arg: CommandArg) -> str:
        """格式化 CommandArg 为可读字符串"""
        parts = []
        
        # 参数类型
        parts.append(f"type={arg.node_type.value}")
        
        # 选项名（如果有）
        if arg.option_name:
            parts.append(f"option='{arg.option_name}'")
        
        # 值（如果有）
        if arg.values:
            parts.append(f"values={arg.values}")
        
        # 重复次数（如果是标志）
        if arg.repeat and arg.repeat > 1:
            parts.append(f"repeat={arg.repeat}")
        
        # 占位符标记（如果有）
        if hasattr(arg, 'is_placeholder') and arg.is_placeholder:
            parts.append("placeholder=True")
        
        return f"CommandArg({', '.join(parts)})"

    @staticmethod
    def normalize_command_line(args: List[str]) -> List[str]:
        """
        预处理命令行，统一样式
        
        处理规则：
        1. 分解组合短选项：-zxvf -> -z -x -v -f
        2. 分离等号形式：--config=bar -> --config bar
        3. 不处理 -- 分隔符之后的字符串
        4. 保持其他参数不变
        
        Args:
            args: 原始命令行参数列表
            
        Returns:
            List[str]: 标准化后的命令行参数列表
        """
        if not args:
            return []
        
        normalized_args = []
        found_separator = False  # 是否找到了分隔符
        
        for arg in args:
            if not arg:
                continue
                
            if arg == "--":
                # 分隔符，后面的都不再处理
                normalized_args.append(arg)
                found_separator = True
                debug(f"找到分隔符 '--'，后续参数不再处理")
                continue
            
            if found_separator:
                # 分隔符之后的所有参数都保持原样
                normalized_args.append(arg)
                debug(f"分隔符后保持原样: {arg}")
                continue
                
            if arg.startswith("--") and "=" in arg:
                # 处理长选项的等号形式：--config=bar -> --config bar
                opt_name, opt_value = arg.split("=", 1)
                normalized_args.append(opt_name)
                normalized_args.append(opt_value)
                debug(f"分离等号形式: {arg} -> {opt_name} {opt_value}")
                
            elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
                # 处理组合短选项：-zxvf -> -z -x -v -f
                # 不依赖配置，直接分解所有字符
                decomposed = Utils._decompose_short_options(arg)
                normalized_args.extend(decomposed)
                debug(f"分解组合短选项: {arg} -> {decomposed}")
                
            else:
                # 其他情况保持不变
                normalized_args.append(arg)
                debug(f"保持原样: {arg}")
        
        return normalized_args
    
    @staticmethod
    def _decompose_short_options(combined_option: str) -> List[str]:
        """
        分解组合短选项
        
        Args:
            combined_option: 组合短选项，如 "-zxvf"
            
        Returns:
            List[str]: 分解后的选项列表，如 ["-z", "-x", "-v", "-f"]
        """
        if len(combined_option) <= 2:
            return [combined_option]
        
        # 提取选项字符（去掉开头的 "-"）
        option_chars = combined_option[1:]
        decomposed = []
        
        # 简单分解：所有字符都作为独立标志
        # 在实际使用中，接受参数的选项通常不会在组合选项中间出现
        # 例如：tar -zxvf file.tar.gz 中的 -f 应该在最后单独出现
        for char in option_chars:
            decomposed.append(f"-{char}")
        
        debug(f"分解组合短选项: {combined_option} -> {decomposed}")
        return decomposed