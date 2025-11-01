# CmdBridge 的配置说明

## 概念

Configs Filetree:

```
configs
├── config.toml                         # cmdbridge config file
├── firewall.domain
│   ├── iptables.toml
│   └── mufw.toml
├── firewall.domain.base.toml
├── package.domain                      # `package` domain
│   ├── apt.toml                        # `apt` operation group
│   └── pacman.toml
├── package.domain.base.toml            # the interface of the operation groups
└── program_parser_configs              # the parser configs of programs
    ├── apt-file.toml
    ├── apt.toml
    ├── asp.toml
    ├── iptables.toml
    ├── mufw.toml
    └── pacman.toml                     # the parser config of programs `pacman`
```

名称的定义:
- Domain (操作组的域): 用于划分操作组。
- Operation Group (操作组): 表示操作的合集, 可以使用多个程序。
- Domain Interface (域接口): 定义一个域的接口。即所有操作组的接口
- Program Parser Config (程序参数解析配置): 提供程序参数给程序解释器。相关语法参考: python 的 getopt 和 argparse。

## Domain

名称格式: `<domain>.domain`。e.g. package.domain

## Domain Interface

名称格式: `<domain>.domain.base.toml`。e.g. package.domain.base.toml

配置格式。For Example:

```toml
[operations.install_remote]     # 操作名: install_remote
description = "Install packages from remote repositories"
args = ["pkgs"]                 # 操作 install_remote 需要的参数 pkgs
```

## Operation Group

名称格式: `<operation_group_name>.toml`。e.g. pacman.toml, apt.toml

配置格式。For Example:

```toml
[operations.install_remote]             # 操作名: install_remote
cmd_format = "apt install {pkgs}"       # `{pkgs}`: cmdbridge 的命令行解释器会根据 "Program Parser Config" 配置的解析参数来提取用户输入的 pkgs, 从而替换 `{pkgs}` 来生成最终的 cmd。
                                        # 注意: `{pkgs}` 的名称 "pkgs" 一定要和 Domain Interface 定义的名称相同
```

## Program Parser Config

名称格式: `<program_name>.toml`。e.g. pacman.toml, apt.toml, apt-file.toml

配置格式。For Example:

```toml
[apt.parser_config]
program_name = "apt"                # program name

[[apt.sub_commands]]
name = "install"                    # 定义子命令 `install`

[[apt.sub_commands.arguments]]
name = "packages"                   # 子命令 `install` 的位置参数
nargs = "+"
```

---

## Program Parser Config 的具体配置

### Flag Argument

```toml
[[pacman.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"                 # 有 opt 且 nargs = "0" 表示是一个 Flag Argument
```

### Option Argument

比如: `apt --config <config_path> install vim`:

```toml
[[apt.arguments]] 
name = "config"
opt = ["--config"]
nargs = "1"             # 有 opt 且 nargs 不为 0 则表示是一个 Option Argument
```

### Positional Argument (位置参数)

比如: `pacman -S vim`:

```toml
[pacman.parser_config]
program_name = "pacman"

[[pacman.arguments]]
name = "targets"        # 没有 opt 但有 nargs 则表示是一个 Positional Argument
nargs = "+"
```

### Sub Command (子命令)

比如: `apt install vim`:

```toml
[[apt.sub_commands]]        # 有 sub_commands 表示是一个子命令
name = "install"
```

子命令的别名。e.g. `brew list/ls -v vim`:

```toml
[[brew.sub_commands]]
name = "list"
alias = ["ls"]              # list 的别名是 ls
```

### 复用子命令的参数配置

**mufw (my ufw) 是自定义的命令**

比如: mufw 的子命令 allow, deny

```toml
# ## allow
[[mufw.sub_commands]]
name = "allow"
id = "subcmd_id_allow"              # 为了复用它的参数先定义 id。一个配置文件中 id 不能有相同。

[[mufw.sub_commands.arguments]]
name = "port"
opt = ["--port"]
nargs = "1"

[[mufw.sub_commands.arguments]]
name = "protocol"
opt = ["--proto"]
nargs = "1"

[[mufw.sub_commands.arguments]]
name = "service"
opt = ["--service"]
nargs = "1"

[[mufw.sub_commands.arguments]]
name = "from-ip"
opt = ["--from-ip"]
nargs = "1"

# ## deny
[[mufw.sub_commands]]
name = "deny"
include_arguments_and_subcmds = "subcmd_id_allow"       # 复用 allow 子命令的参数配置 (arguments 和 subcommands)
id = "subcmd_id_deny"
```

比如: mufw 的 delete 子命令的子命令 allow, deny

```toml
# ## delete
[[mufw.sub_commands]]
name = "delete"

[[mufw.sub_commands.sub_commands]]
name = "allow"
include_arguments_and_subcmds = "subcmd_id_allow"

[[mufw.sub_commands.sub_commands]]
name = "deny"
include_arguments_and_subcmds = "subcmd_id_deny"
```

总结:
- 通过 mufw 的例子, 你可以自定义命令来映射一个 domain 下的操作。这样你只需要记住自定义命令的用法即可映射同一个 domain 下的其他操作组的命令。
- 如果你同时不需要其他操作组的命令映射到自定义命令。那么其他操作组的命令参数可以不用配置, 只配置自定义命令即可。

## Operation Group 的额外参数

### final_cmd_format

final_cmd_format: 只有在最终映射成命令时, 才会使用其他情况下不会使用。

应用场景:
-   比如我有脚本 `my-list-installed-pacman` 和 `my-list-installed-apt`, 它们都是自定义的格式列出安装的软件。
-   参考: [my-list-installed-pacman](https://github.com/JohanChane/intuit-backup/blob/main/Doc/example/lsmipkgs)

比如 pacman 的配置:

```toml
[operations.my_list_installed]
cmd_format = "pacman -Q --my"
final_cmd_format = "my-list-installed-pacman"       # ArchLinux 平台的
```

对应的 apt 的配置:

```toml
[operations.my_list_installed]
cmd_format = "apt list --installed --my"
final_cmd_format = "my-list-installed-apt"          # Debian 平台的
```

使用:

```sh
cmdbridge map -t apt -- pacman -Q --my                      # 映射成: my-list-installed-apt
cmdbridge map -t pacman -- apt list --installed --my        # 映射成: my-list-installed-pacman
```

程序参数配置:

pacman:

```toml
[[pacman.arguments]]
name = "my"
opt = ["--my"]
nargs = "0"
```

apt:

```toml
[[apt.sub_commands.arguments]]
name = "installed"
opt = ["--installed"]
nargs = "0"

[[apt.sub_commands.arguments]]
name = "my"
opt = ["--my"]
nargs = "0"
```

通过上面的例子, 你应该知道怎么扩展程序参数了。