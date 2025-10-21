"""与业务无关的解析器类型定义"""

from typing import TypedDict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum

class ArgType(Enum):
    """参数类型枚举"""
    SUB_CMD = "sub_cmd"    # 子命令
    OPTION_NEEDS_VALUE = "arg"           # 带参数的选项 (-o/--output <path>)
    FLAG = "flag"         # 标志选项
    VALUE = "value"       # 值参数

class ArgDataType(Enum):
    """参数数据类型枚举"""
    STRING = "string"        # 字符串类型
    INTEGER = "integer"      # 整数类型  
    BOOLEAN = "boolean"      # 布尔类型
    LIST = "list"            # 列表类型
    PATH = "path"            # 文件路径类型

@dataclass
class ArgNode:
    """参数节点"""
    name: str              # 参数名称
    type: ArgType          # 参数类型
    data_type: ArgDataType = ArgDataType.STRING  # 数据类型
    values: List[str] = field(default_factory=list)  # 值参数的值列表
    args: List['ArgNode'] = field(default_factory=list)  # 子参数（用于 sub_cmd）
    repeat: int = 1        # 重复次数（主要用于 flag）
    original_opt: Optional[str] = None  # 原始选项名
    validated: bool = True  # 是否通过验证
    validation_error: Optional[str] = None  # 验证错误信息

@dataclass  
class ParserConfig:
    """解析器配置"""
    name: str
    arg_name: str
    type: ArgType = ArgType.FLAG
    data_type: ArgDataType = ArgDataType.STRING
    nargs: Optional[Union[str, int]] = None
    short_opt: Optional[str] = None
    long_opt: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    sub_args: List['ParserConfig'] = field(default_factory=list)
    
    # 数据类型特定配置
    default_value: Any = None
    choices: List[str] = field(default_factory=list)
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    required: bool = False
    help_text: str = ""
    validation_regex: Optional[str] = None
    
    @property
    def is_flag(self) -> bool:
        return self.type == ArgType.FLAG
    
    @property
    def is_sub_cmd(self) -> bool:
        return self.type == ArgType.SUB_CMD
    
    @property
    def is_arg(self) -> bool:
        return self.type == ArgType.OPTION_NEEDS_VALUE
    
    @property
    def is_value(self) -> bool:
        return self.type == ArgType.VALUE

class SyntaxTree(TypedDict):
    """语法解析树"""
    command_name: str
    argument_nodes: List[ArgNode]
    extra_content: Optional[str]