# Command Line Interpreter Syntax Parsing

## Tokenize

Tokenize: Processing raw characters is too inconvenient, so we first parse them into familiar data structures like Lists for easier subsequent processing. This can be understood as Lexemes and Tokens from "Crafting Interpreters".

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
```

Example 1: apt --help install vim git --config path --noconfirm -- abc

```python
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
```

Example 2: pacman -Syy --config path_1 --config path_2

```python
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
```

Example 3: tar -zxvf foo.tar.gz -- path_1 path_2

```python
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
```

## Building CommandTree

```python
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
```


Example 1: apt --help install vim git --config path --noconfirm -- abc

```python
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
            CommandArg(node_type=ArgType.EXTRA, values=["abc"])
        ]
    )
)
```

Example 2: pacman -Syy --config path_1 --config path_2

```python
tree_pacman = CommandNode(
    name="pacman",
    arguments=[
        CommandArg(node_type=ArgType.FLAG, option_name="-S"),
        CommandArg(node_type=ArgType.FLAG, option_name="-y", repeat = 2),
        CommandArg(node_type=ArgType.OPTION, option_name="--config", values=["path_1", "path_2"]),
    ]
)
```

Example 3: tar -zxvf foo.tar.gz -- path_1 path_2

```python
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

## Command Line Styles: getopt and argparse

The argparse style only adds subcommands compared to getopt, everything else is the same.

getopt format:

```
<program_name> [<flags>] [<options>] [--] [<positional_args>]        # <flag>, <option> and <positional_args> all belong to the program name (main command). <positional_args> has exactly one.
```

argparse style:

```
<main_command(program_name)> [<flags>] [<options>] [--] [<positional_args>]
<main_command(program_name)> [<main_command_flags>] [<main_command_options>] <subcommand> [<subcommand_flags>] [<subcommand_options>] [--] [<subcommand_positional_args>]     # If subcommands appear, the main command cannot have positional arguments, otherwise ambiguity may occur.
```

### Common Features

1. **Multi-value options**
   ```bash
   --config path --config path => --config path path   # Can specify multiple this way
   ```

2. **Short option combination**
   ```bash
   tar -zxvf foo.tar.gz -- path_1 path_2 
   # `-zxvf` means `-z -x -v -f`
   # `-f` is an option that requires arguments, can be written together
   # But cannot `tar -zxfv foo.tar.gz -- path_1 path_2` (arguments must be at the end)
   ```

3. **Repeat counting**
   ```bash
   -Syy  # Records flag repeat count, means -S -y -y
   -Sy   # Means -S -y
   ```

### getopt Style Command Line

1. **Strict argument order**
   ```bash
   # getopt style
   pacman -S -y vim git    # ✅ Correct
   pacman -S vim -y git    # ❌ -y may not be recognized as global flag
   ```

2. **Options and arguments must be adjacent**
   ```bash
   tar -f archive.tar -xzv  # ✅ -f and archive.tar are adjacent
   tar -xzv -f archive.tar  # ✅ Arguments follow options
   tar -xzv archive.tar -f  # ❌ -f missing arguments
   ```

3. **No subcommand support**
   ```bash
   # getopt programs usually have no subcommand concept
   pacman -S package    # -S is an option, not a subcommand
   ```

4. **Long/short option handling**
   ```bash
   --help     # Long option
   -h         # Short option  
   -abc       # Equivalent to -a -b -c
   ```
5. **Separator**
    ```bash
    pacman -S vim git  -- -s   # Means install vim git, -s doesn't affect pacman
    ```

### argparse Style Command Line

1. **Subcommand restrictions**
   ```bash
   # Cannot have two sibling subcommands, otherwise ambiguity occurs
   git commit push        # ❌ Ambiguity: commit and push are both first-level subcommands
   git commit && git push # ✅ Correct usage
   ```

2. **Main command positional arguments**
   ```bash
   # If there are subcommands, the main command usually has no positional arguments
   apt install vim        # ✅ install is subcommand, vim is subcommand positional argument
   apt vim install        # ❌ Ambiguity: is vim a main command positional argument or subcommand?
   ```

3. **Flexible argument positions**
   ```bash
   # argparse allows mixing options and positional arguments
   apt install -y vim git    # ✅ Correct
   apt install vim -y git    # ✅ Also correct
   apt --help install -y vim git  # ✅ Also correct, --help belongs to apt, while -y belongs to install
   ```

4. **Subcommand argument isolation**
   ```bash
   # Each subcommand has its own independent argument set
   git commit -m "message" --author="name"
   git push --force
   # commit and push arguments don't interfere with each other
   ```

### Examples

#### getopt Style Examples

```bash
# pacman (Arch Linux package manager)
pacman -Syu vim git --noconfirm
# Parsed as:
# -S (sync)
# -y (refresh)
# -u (upgrade) 
# vim git (positional arguments)
# --noconfirm (flag)

# tar (archiving tool)
tar -zxvf archive.tar.gz file1 file2
# Parsed as:
# -z (gzip)
# -x (extract) 
# -v (verbose)
# -f archive.tar.gz (file argument)
# file1 file2 (positional arguments)
```

#### argparse Style Examples

```bash
# apt (Debian package manager)
apt update
apt install -y vim git
apt remove vim --purge
# Parsed as:
# update (subcommand, no arguments)
# install (subcommand) + -y (flag) + vim git (subcommand positional arguments)
# remove (subcommand) + vim (subcommand positional arguments) + --purge (flag)

# git (version control)
git commit -m "message" --author="John"
git push origin main --force
# Parsed as:
# commit (subcommand) + -m "message" (option) + --author="John" (option)
# push (subcommand) + origin main (subcommand positional arguments) + --force (flag)

# docker (container management)
docker container ls --all
docker image build -t myapp .
# Parsed as:
# container (subcommand) + ls (sub-subcommand) + --all (flag)
# image (subcommand) + build (sub-subcommand) + -t myapp (option) + . (positional argument)
```

#### Complex Example Comparison

```bash
# getopt style (tar)
tar -czf backup.tar.gz --exclude="*.tmp" src/ docs/

# argparse style (kubectl)
kubectl get pods --namespace=production --sort-by=".status.startTime"

# mixed style (docker with getopt-like flags)
docker run -it --rm -v /host:/guest -p 8080:80 nginx
```

## Program Parameter Configuration

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
opt = ["-S"]
nargs = "0"

[[pacman.arguments]]
name = "y"
opt = ["-y"]
nargs = "0"

[[pacman.arguments]]
name = "noconfirm"
opt = ["--noconfirm"]
nargs = "0"
```

```python
pacman_config = ParserConfig(
    parser_type=ParserType.GETOPT,
    program_name="pacman",
    arguments=[
        ArgumentConfig(name="help", opt=["-h", "--help"], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="targets", opt=[], nargs=ArgumentCount.ONE_OR_MORE),
        ArgumentConfig(name="S", opt=["-S"], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="y", opt=["-y"], nargs=ArgumentCount.ZERO),
        ArgumentConfig(name="noconfirm", opt=["--noconfirm"], nargs=ArgumentCount.ZERO),
    ],
    sub_commands=[]
)
```

### apt

Example: `apt --help install --yes pkgs`

```toml
# apt.toml
[apt.parser_config]
parser_type = "argparse"
program_name = "apt"

[[apt.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"
# required = true/false # supports required

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