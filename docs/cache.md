## cmd_mapping

查找命令行对应的动作

### 生成命令映射需要的数据

操作接口文件 `package.domain`:

```toml
[operations.install_with_config]
cmd_format = "apt install {pkgs} --config {config_path}"

[operations.install_with_config]
cmd_format = "pacman -S {pkgs} --config {config_path}"
```

```py
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
    repeat: Optional[int] = None  # 重复次数，仅 FLAG 类型使用
```

使用命令行解释器分析 cmd_format 生成下面的文件 `package.domain.cmd_mappings.toml`:

```toml
[[command_mappings.apt]]
operation: ""
params: {
    pkgs: {cmd_arg: CommandArg  }
    config_path: {cmd_arg: CommandArg }
}
cmd_node: CommandNode

[[command_mappings.pacman]]
operation: ""
params: {
    pkgs: {cmd_arg: CommandArg  }
    config_path: {cmd_arg: CommandArg }
}

cmd_node: CommandNode
```

### 匹配命令的规则

匹配规则:
1. 程序名相同（已在外部检查）
2. 命令节点结构相同（名称、参数数量、子命令结构）
3. 参数结构相同（类型、选项名、重复次数、值数量）
4. 忽略占位符参数的具体值内容

## operation_mapping

operation_mapping: operation => 