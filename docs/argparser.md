**更新文件：`docs/argparser.md`**

```markdown
## 解析器的设计

```python
from enum import Enum
from typing import List, Optional
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

# Example 1: apt --help install vim git --config path --noconfirm -- abc
tokens_apt = [
    CommandToken(token_type=TokenType.PROGRAM, values=["apt"]),
    CommandToken(token_type=TokenType.FLAG, values=["--help"]),
    CommandToken(token_type=TokenType.SUBCOMMAND, values=["install"]),
    CommandToken(token_type=TokenType.POSITIONAL_ARG, values=["vim"]),
    CommandToken(token_type=TokenType.POSITIONAL_ARG, values=["git"]),
    CommandToken(token_type=TokenType.OPTION_NAME, values=["--config"]),
    CommandToken(token_type=TokenType.OPTION_VALUE, values=["path"]),
    CommandToken(token_type=TokenType.FLAG, values=["--noconfirm"]),
    CommandToken(token_type=TokenType.SEPARATOR, values=["--"]),
    CommandToken(token_type=TokenType.EXTRA_ARG, values=["abc"])
]

# Example 2: pacman -Syy --config path_1 --config path_2
tokens_pacman = [
    CommandToken(token_type=TokenType.PROGRAM, values=["pacman"]),
    CommandToken(token_type=TokenType.FLAG, values=["-S"]),
    CommandToken(token_type=TokenType.FLAG, values=["-y"]),
    CommandToken(token_type=TokenType.FLAG, values=["-y"]),  # second -y
    CommandToken(token_type=TokenType.OPTION_NAME, values=["--config"]),
    CommandToken(token_type=TokenType.OPTION_VALUE, values=["path_1"]),
    CommandToken(token_type=TokenType.OPTION_NAME, values=["--config"]),
    CommandToken(token_type=TokenType.OPTION_VALUE, values=["path_2"]),
]

# Example 3: tar -zxvf foo.tar.gz -- path_1 path_2
tokens_tar = [
    CommandToken(token_type=TokenType.PROGRAM, values=["tar"]),
    CommandToken(token_type=TokenType.FLAG, values=["-z"]),
    CommandToken(token_type=TokenType.FLAG, values=["-x"]),
    CommandToken(token_type=TokenType.FLAG, values=["-v"]),
    CommandToken(token_type=TokenType.OPTION_NAME, values=["-f"]),
    CommandToken(token_type=TokenType.OPTION_VALUE, values=["foo.tar.gz"]),
    CommandToken(token_type=TokenType.SEPARATOR, values=["--"]),
    CommandToken(token_type=TokenType.EXTRA_ARG, values=["path_1"]),
    CommandToken(token_type=TokenType.EXTRA_ARG, values=["path_2"]),
]

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

# Example 1: apt --help install vim git --config path --noconfirm -- abc
tree_apt = CommandNode(
    name="apt",
    arguments=[
        CommandArg(node_type=ArgType.FLAG, option_name="--help"),
    ],
    subcommand=CommandNode(
        name="install",
        arguments=[
            CommandArg(node_type=ArgType.POSITIONAL, values=["vim", "git"]),
            CommandArg(node_type=ArgType.OPTION, option_name="--config", values=["path"]),
            CommandArg(node_type=ArgType.FLAG, option_name="--noconfirm")
            CommandArg(node_type=ArgType.EXTRA, values=["abc"])             # 不放主命令了, 方便处理
        ]
    )
)

# Example 2: pacman -Syy --config path_1 --config path_2
tree_pacman = CommandNode(
    name="pacman",
    arguments=[
        CommandArg(node_type=ArgType.FLAG, option_name="-S"),
        CommandArg(node_type=ArgType.FLAG, option_name="-y", repeat = 2),
        CommandArg(node_type=ArgType.OPTION, option_name="--config", values=["path_1", "path_2"]),
    ]
)

# Example 3: tar -zxvf foo.tar.gz -- path_1 path_2
tree_tar = CommandNode(
    name="tar",
    arguments=[
        CommandArg(node_type=ArgType.FLAG, option_name="-z"),
        CommandArg(node_type=ArgType.FLAG, option_name="-x"),
        CommandArg(node_type=ArgType.FLAG, option_name="-v"),
        CommandArg(node_type=ArgType.OPTION, option_name="-f", values=["foo.tar.gz"]),
        CommandArg(node_type=ArgType.EXTRA, values=["path_1", "path_2"])
    ]
)
```

## getopt/argparse 解释器

### 共通之处

1. **多值选项**
   ```bash
   --config path --config path => --config path path   # 可以这样指定多个
   ```

2. **短选项组合**
   ```bash
   tar -zxvf foo.tar.gz -- path_1 path_2 
   # `-zxvf` 表示 `-z -x -v -f`
   # `-f` 是需要指定参数的选项，可以连在一起写
   # 但不能 `tar -zxfv foo.tar.gz -- path_1 path_2`（参数必须在最后）
   ```

3. **重复计数**
   ```bash
   -Syy  # 记录 flag 的重复次数，表示 -S -y -y
   -Sy   # 表示 -S -y
   ```

### getopt 解释器

**C-style parser**

#### 特别之处

1. **严格的参数顺序**
   ```bash
   # getopt 风格
   pacman -S -y vim git    # ✅ 正确
   pacman -S vim -y git    # ❌ -y 可能不会被识别为全局标志
   ```

2. **选项和参数必须相邻**
   ```bash
   tar -f archive.tar -xzv  # ✅ -f 和 archive.tar 相邻
   tar -xzv -f archive.tar  # ✅ 参数跟在选项后面
   tar -xzv archive.tar -f  # ❌ -f 缺少参数
   ```

3. **不支持子命令**
   ```bash
   # getopt 程序通常没有子命令概念
   pacman -S package    # -S 是选项，不是子命令
   ```

4. **长短选项处理**
   ```bash
   --help     # 长选项
   -h         # 短选项  
   -abc       # 等同于 -a -b -c
   ```
5. **分隔符**
    ```bash
    pacman -S vim git  -- -s   # 表示安装 vim git,  -s 不作用于 pacman
    ```

### argparse 解释器

**Parser for command-line options, arguments and subcommands**

#### 特别之处

1. **子命令限制**
   ```bash
   # 不能有两个子命令，否则会有歧义
   git commit push        # ❌ 歧义：commit 和 push 都是子命令
   git commit && git push # ✅ 正确用法
   ```

2. **主命令位置参数**
   ```bash
   # 如果有子命令，则主命令通常没有位置参数
   apt install vim        # ✅ install 是子命令，vim 是子命令的位置参数
   apt vim install        # ❌ 歧义：vim 是主命令位置参数还是子命令？
   ```

3. **灵活的参数位置**
   ```bash
   # argparse 允许选项和位置参数混合
   apt install -y vim git    # ✅ 正确
   apt install vim -y git    # ✅ 也正确
   apt --help install -y vim git  # ✅ 也正确, --help 属于 apt, 而 -y 属于 install
   ```

4. **子命令参数隔离**
   ```bash
   # 每个子命令有自己独立的参数集
   git commit -m "message" --author="name"
   git push --force
   # commit 和 push 的参数不会相互干扰
   ```

### 例子

#### getopt 风格示例

```bash
# pacman (Arch Linux package manager)
pacman -Syu vim git --noconfirm
# 解析为：
# -S (sync)
# -y (refresh)
# -u (upgrade) 
# vim git (位置参数)
# --noconfirm (标志)

# tar (归档工具)
tar -zxvf archive.tar.gz file1 file2
# 解析为：
# -z (gzip)
# -x (extract) 
# -v (verbose)
# -f archive.tar.gz (文件参数)
# file1 file2 (位置参数)
```

#### argparse 风格示例

```bash
# apt (Debian package manager)
apt update
apt install -y vim git
apt remove vim --purge
# 解析为：
# update (子命令，无参数)
# install (子命令) + -y (标志) + vim git (子命令位置参数)
# remove (子命令) + vim (子命令位置参数) + --purge (标志)

# git (版本控制)
git commit -m "message" --author="John"
git push origin main --force
# 解析为：
# commit (子命令) + -m "message" (选项) + --author="John" (选项)
# push (子命令) + origin main (子命令位置参数) + --force (标志)

# docker (容器管理)
docker container ls --all
docker image build -t myapp .
# 解析为：
# container (子命令) + ls (子子命令) + --all (标志)
# image (子命令) + build (子子命令) + -t myapp (选项) + . (位置参数)
```

#### 复杂示例对比

```bash
# getopt 风格 (tar)
tar -czf backup.tar.gz --exclude="*.tmp" src/ docs/

# argparse 风格 (kubectl)
kubectl get pods --namespace=production --sort-by=".status.startTime"

# 混合风格 (docker with getopt-like flags)
docker run -it --rm -v /host:/guest -p 8080:80 nginx
```

### 解析规则总结

| 特性 | getopt | argparse |
|------|--------|----------|
| 子命令支持 | ❌ 无 | ✅ 有 |
| 参数位置 | 严格相邻 | 灵活混合 |
| 选项组合 | ✅ 支持 (`-xyz`) | ✅ 支持 |
| 多值选项 | 有限支持 | ✅ 良好支持 |
```

## 程序的参数配置

### pacman

```toml
[pacman.parser_config]
parser_type = "getopt"
program_name = "pacman"

[[pacman.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"

[[pacman.arguments]]
name = "targets"
nargs = "+"

[[pacman.arguments]]
name = "S"
opt = ["-S", ""]
nargs = "0"

[[pacman.arguments]]
name = "y"
opt = ["-y", ""]
nargs = "0"

[[pacman.arguments]]
name = "noconfirm"
opt = ["--noconfirm", ""]
nargs = "0"
```

```python
pacman_config = ParserConfig(
    parser_type=ParserType.GETOPT,
    program_name="pacman",
    arguments=[
        ArgumentConfig(name="help", opt=["-h", "--help"], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="targets", opt=[], nargs=ArgumentCount.ONE_OR_MORE),
        ArgumentConfig(name="S", opt=["-S", ""], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="y", opt=["-y", ""], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="noconfirm", opt=["--noconfirm", ""], nargs=ArgumentCount.ZERO),
    ],
    sub_commands=[]
)
```

### apt

```toml
# apt.toml
[apt.parser_config]
parser_type = "argparse"
program_name = "apt"

[[apt.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"
# required = true/false # 支持 required

[[apt.sub_commands]]
name = "install"

[[apt.sub_commands.arguments]]
name = "packages"
nargs = "+"

[[apt.sub_commands.arguments]]
name = "yes"
opt = ["-y", "--yes"]
nargs = "0"

[[apt.sub_commands]]
name = "search"

[[apt.sub_commands.arguments]]
name = "packages"
nargs = "+"
```

```python
apt_config = ParserConfig(
    parser_type=ParserType.ARGPARSE,
    program_name="apt",
    arguments=[
        ArgumentConfig(name="help", opt=["-h", "--help"], nargs=ArgumentCount.ZERO),
    ],
    sub_commands=[
        SubCommandConfig(
            name="install",
            arguments=[
                ArgumentConfig(name="packages", opt=[], nargs=ArgumentCount.ONE_OR_MORE),
                ArgumentConfig(name="yes", opt=["-y", "--yes"], nargs=ArgumentCount.ZERO),
            ]
        ),
        SubCommandConfig(
            name="search",
            arguments=[
                ArgumentConfig(name="packages", opt=[], nargs=ArgumentCount.ONE_OR_MORE),
            ]
        ),
    ]
)
```