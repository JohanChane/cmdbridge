from .types import CommandNode, CommandArg
from log import debug

class Utils:
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