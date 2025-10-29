from enum import Enum
from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass, field

# === CommandToken ===
class TokenType(Enum):
    """Command line token types"""
    PROGRAM = "program"                 # Program name (e.g., git, pacman, apt)
    SUBCOMMAND = "subcommand"           # Subcommand name (e.g., commit, install, search)
    POSITIONAL_ARG = "positional_arg"   # Positional argument (non-option)
    OPTION_NAME = "option_name"         # Option name (-o/--output)
    OPTION_VALUE = "option_value"       # Option value
    FLAG = "flag"                       # Boolean flag
    SEPARATOR = "separator"             # Separator (--)
    EXTRA_ARG = "extra_arg"             # Arguments after separator

@dataclass
class CommandToken:
    """Command line token
    
    Represents a syntactic node in command line parsing.
    
    Attributes:
        token_type: Type of token, defined in TokenType enum
        values: List of values for this token
        original_text: Original command line string for debugging,
                      auto-generated from values if not provided
    """
    token_type: TokenType
    values: List[str]
    original_text: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.original_text is None and self.values:
            self.original_text = " ".join(self.values)
    
    def __str__(self) -> str:
        """String representation of the token"""
        return f"CommandToken(type={self.token_type.value}, values={self.values}, original='{self.original_text}')"
    
    def is_program(self) -> bool:
        """Check if this is a program token"""
        return self.token_type == TokenType.PROGRAM
    
    def is_subcommand(self) -> bool:
        """Check if this is a subcommand token"""
        return self.token_type == TokenType.SUBCOMMAND
    
    def is_flag(self) -> bool:
        """Check if this is a flag token"""
        return self.token_type == TokenType.FLAG
    
    def is_option(self) -> bool:
        """Check if this is an option token (OPTION_NAME or OPTION_VALUE)"""
        return self.token_type in (TokenType.OPTION_NAME, TokenType.OPTION_VALUE)
    
    def get_first_value(self) -> Optional[str]:
        """Get the first value if exists"""
        return self.values[0] if self.values else None
    
    def get_joined_values(self, separator: str = " ") -> str:
        """Join all values with separator into a single string"""
        return separator.join(self.values)

# === Command Tree ===
class ArgType(Enum):
    """Command tree node types"""
    POSITIONAL = "positional"
    OPTION = "option"
    FLAG = "flag"
    EXTRA = "extra"

@dataclass
class CommandArg:
    """Command argument in tree structure"""
    node_type: ArgType
    option_name: Optional[str] = None
    values: List[str] = field(default_factory=list)
    repeat: Optional[int] = None
    placeholder: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        result = {
            "node_type": self.node_type.value,
            "values": self.values.copy(),
        }
        
        # 只有非 None 的字段才包含
        if self.option_name is not None:
            result["option_name"] = self.option_name
        if self.repeat is not None:
            result["repeat"] = self.repeat
        if self.placeholder is not None:
            result["placeholder"] = self.placeholder
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandArg':
        """从字典反序列化"""
        return cls(
            node_type=ArgType(data["node_type"]),
            option_name=data.get("option_name"),
            values=data.get("values", []),
            repeat=data.get("repeat"),
            placeholder=data.get("placeholder")  # 反序列化 placeholder
        )

@dataclass
class CommandNode:
    """Command tree node - tree structure where subcommands create child nodes"""
    name: str
    arguments: List[CommandArg] = field(default_factory=list)  # Arguments for current node
    subcommand: Optional['CommandNode'] = None                # Subcommand node (tree expansion)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        result = {
            "name": self.name,
            "arguments": [arg.to_dict() for arg in self.arguments],
        }
        
        # 只有非 None 的子命令才包含
        if self.subcommand is not None:
            result["subcommand"] = self.subcommand.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandNode':
        """从字典反序列化"""
        arguments = [CommandArg.from_dict(arg_data) for arg_data in data.get("arguments", [])]
        
        node = cls(
            name=data["name"],
            arguments=arguments
        )
        
        # 递归反序列化子命令
        if "subcommand" in data and data["subcommand"] is not None:
            node.subcommand = cls.from_dict(data["subcommand"])
            
        return node

# === 参数配置 ===
# 解析器类型
class ParserType(Enum):
    GETOPT = "getopt"
    ARGPARSE = "argparse"

# 参数配置
@dataclass
class ArgumentCount:
    """参数数量规范"""
    spec: str  # argparse 风格的 nargs 规范
    
    def __init__(self, spec: str):
        """初始化参数数量规范"""
        # 校验 nargs 字符串
        valid_specs = {'?', '*', '+', '0'}
        if (spec not in valid_specs and 
            not spec.isdigit() and 
            not self._is_valid_range(spec)):
            raise ValueError(f"不支持的 nargs 值: {spec}。支持的格式: ?, *, +, 0, 数字, 或数字范围")
        
        self.spec = spec
    
    def _is_valid_range(self, spec: str) -> bool:
        """检查是否是有效的数字范围格式，如 '1..3'"""
        if '..' in spec:
            parts = spec.split('..')
            if len(parts) == 2:
                return parts[0].isdigit() and (parts[1].isdigit() or parts[1] == '')
        return False
    
    def __str__(self) -> str:
        return self.spec
    
    def is_flag(self) -> bool:
        """检查是否是标志参数（无参数）"""
        return self.spec == '0'
    
    def validate_count(self, actual_count: int) -> bool:
        """验证实际参数数量是否符合要求"""
        if self.spec == '?':
            return actual_count <= 1
        elif self.spec == '*':
            return True  # 任意数量
        elif self.spec == '+':
            return actual_count >= 1
        elif self.spec.isdigit():
            return actual_count == int(self.spec)
        elif self.spec == '0':
            return actual_count == 0
        elif '..' in self.spec:
            # 处理范围格式，如 '1..3' 或 '1..'
            parts = self.spec.split('..')
            min_count = int(parts[0])
            max_count = int(parts[1]) if parts[1].isdigit() else None
            
            if actual_count < min_count:
                return False
            if max_count is not None and actual_count > max_count:
                return False
            return True
        else:
            # 默认情况，argparse 默认是 1
            return actual_count == 1
    
    def is_required(self) -> bool:
        """检查根据 nargs 是否是必需参数"""
        # 只有 nargs='+' 或数字 > 0 时才是必需的
        return self.spec == '+' or (self.spec.isdigit() and int(self.spec) > 0)
    
# 常用预设
ArgumentCount.ZERO = ArgumentCount('0')           # 无参数 (标志)
ArgumentCount.ZERO_OR_ONE = ArgumentCount('?')    # 可选参数
ArgumentCount.ZERO_OR_MORE = ArgumentCount('*')   # 零个或多个
ArgumentCount.ONE_OR_MORE = ArgumentCount('+')    # 一个或多个

# 参数配置
@dataclass
class ArgumentConfig:
    """参数配置"""
    name: str                    # 参数名称
    opt: List[str]              # 选项名称列表 (如 ["-h", "--help"])
    nargs: ArgumentCount        # 参数数量规范
    required: bool = False      # 是否是必需参数
    description: Optional[str] = None  # 参数描述
    
    def is_flag(self) -> bool:
        """检查是否是标志参数"""
        return self.nargs.is_flag()
    
    def is_positional(self) -> bool:
        """检查是否是位置参数"""
        return not self.opt or (self.opt and "" in self.opt)
    
    def is_option(self) -> bool:
        """检查是否是选项参数"""
        return self.opt and "" not in self.opt and not self.is_flag()
    
    def accepts_values(self) -> bool:
        """检查是否接受值"""
        return not self.is_flag()
    
    def get_expected_count(self) -> str:
        """获取期望的参数数量"""
        return str(self.nargs)
    
    def validate_count(self, actual_count: int) -> bool:
        """验证实际参数数量是否符合要求"""
        return self.nargs.validate_count(actual_count)
    
    def is_required(self) -> bool:
        """检查是否是必需参数"""
        return self.required
    
    def matches_option(self, option_name: str) -> bool:
        """检查选项名称是否匹配此配置"""
        # 跳过空字符串，只匹配实际的选项名
        for opt in self.opt:
            if opt and opt == option_name:
                return True
        return False
    
    def get_primary_option_name(self) -> Optional[str]:
        """获取主要选项名称

        选择规则:
        1. 优先返回长参数名 (包含 '--' 的选项)
        2. 如果没有长参数名，返回短参数名 (包含 '-') (如果有多个，返回第一个)
        3. 如果没有有效的选项名，返回 None

        Returns:
            Optional[str]: 主要选项名称
        """
        # 1. 查找并返回第一个长参数名 (以 '--' 开头)
        for opt in self.opt:
            if opt and opt.startswith('--') and opt.strip():
                return opt

        # 2. 查找并返回第一个短参数名 (以 '-' 开头)
        for opt in self.opt:
            if opt and opt.startswith('-') and not opt.startswith('--') and opt.strip():
                return opt

        # 3. 如果都没有找到有效选项名，返回 None
        return None

@dataclass
class SubCommandConfig:
    """子命令配置"""
    name: str                              # 子命令名称
    arguments: List[ArgumentConfig] = field(default_factory=list)  # 子命令参数
    description: Optional[str] = None      # 子命令描述
    
    def find_argument(self, option_name: str) -> Optional['ArgumentConfig']:
        """根据选项名称查找参数配置"""
        for arg in self.arguments:
            if arg.matches_option(option_name):
                return arg
        return None

@dataclass
class ParserConfig:
    """解析器配置"""
    parser_type: ParserType                # 解析器类型
    program_name: str                      # 程序名称
    arguments: List[ArgumentConfig] = field(default_factory=list)  # 全局参数
    sub_commands: List[SubCommandConfig] = field(default_factory=list)  # 子命令
    
    def find_argument(self, opt_name: str) -> Optional[ArgumentConfig]:
        """根据选项名称查找参数配置"""
        for arg in self.arguments:
            if arg.matches_option(opt_name):
                return arg
        return None
    
    def find_subcommand(self, name: str) -> Optional[SubCommandConfig]:
        """根据名称查找子命令配置"""
        for sub_cmd in self.sub_commands:
            if sub_cmd.name == name:
                return sub_cmd
        return None
    
    def get_positional_arguments(self) -> List[ArgumentConfig]:
        """获取所有位置参数"""
        return [arg for arg in self.arguments if arg.is_positional()]