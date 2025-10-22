from enum import Enum
from typing import List, Optional, Union
from dataclasses import dataclass, field

# === ArgList ===
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

@dataclass
class CommandNode:
    """Command tree node - tree structure where subcommands create child nodes"""
    name: str
    arguments: List[CommandArg] = field(default_factory=list)  # Arguments for current node
    subcommand: Optional['CommandNode'] = None                # Subcommand node (tree expansion)

# === 参数配置 ===
# 解析器类型
class ParserType(Enum):
    GETOPT = "getopt"
    ARGPARSE = "argparse"

# 参数数量规范
class ArgumentCount(Enum):
    ZERO = "0"        # 无参数 (标志)
    ZERO_OR_ONE = "?" # 可选参数
    ZERO_OR_MORE = "*" # 零个或多个参数  
    ONE_OR_MORE = "+"  # 一个或多个参数
    EXACTLY_N = "n"    # 有 n 个参数

# === 参数配置 ===
# 解析器类型
class ParserType(Enum):
    GETOPT = "getopt"
    ARGPARSE = "argparse"

# 参数数量规范
class ArgumentCount(Enum):
    ZERO = "0"              # 无参数 (标志)
    ZERO_OR_ONE = "?"       # 可选参数
    ZERO_OR_MORE = "*"      # 零个或多个参数  
    ONE_OR_MORE = "+"       # 一个或多个参数
    EXACTLY_N = "n"         # 有 n 个参数

# 参数配置
@dataclass
class ArgumentConfig:
    """参数配置"""
    name: str                    # 参数名称
    opt: List[str]              # 选项名称列表 (如 ["-h", "--help"])
    nargs: ArgumentCount        # 参数数量规范
    count: Optional[int] = None # 当 nargs=EXACTLY_N 时的具体数量
    description: Optional[str] = None  # 参数描述
    
    def is_flag(self) -> bool:
        """检查是否是标志参数"""
        return self.nargs == ArgumentCount.ZERO
    
    def is_positional(self) -> bool:
        """检查是否是位置参数"""
        return not self.opt or (self.opt and "" in self.opt)  # 空字符串或没有 opt 就是位置参数
    
    def is_option(self) -> bool:
        """检查是否是选项参数"""
        return self.opt and "" not in self.opt and not self.is_flag()
    
    def accepts_values(self) -> bool:
        """检查是否接受值"""
        return self.nargs != ArgumentCount.ZERO
    
    def get_expected_count(self) -> Union[int, str]:
        """获取期望的参数数量"""
        if self.nargs == ArgumentCount.ZERO:
            return 0
        elif self.nargs == ArgumentCount.EXACTLY_N and self.count is not None:
            return self.count
        else:
            return self.nargs.value  # 返回符号 *, +, ?
    
    def get_primary_name(self) -> str:
        """获取主要名称（优先返回长选项名）"""
        if not self.opt:
            return self.name
        
        # 优先返回长选项名
        for opt in self.opt:
            if opt.startswith("--"):
                return opt
        # 返回第一个选项名
        return self.opt[0] if self.opt else self.name

@dataclass
class SubCommandConfig:
    """子命令配置"""
    name: str                              # 子命令名称
    arguments: List[ArgumentConfig] = field(default_factory=list)  # 子命令参数
    description: Optional[str] = None      # 子命令描述
    
    def find_argument(self, opt_name: str) -> Optional[ArgumentConfig]:
        """根据选项名称查找参数配置"""
        for arg in self.arguments:
            if opt_name in arg.opt:
                return arg
        # 也检查位置参数
        for arg in self.arguments:
            if arg.is_positional() and opt_name == "":
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
            if opt_name in arg.opt:
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