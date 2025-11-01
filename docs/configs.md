# CmdBridge Configuration Guide

## Concepts

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

Terminology definitions:
- **Domain**: Used to categorize operation groups.
- **Operation Group**: Represents a collection of operations that can use multiple programs.
- **Domain Interface**: Defines the interface for a domain, i.e., the interface for all operation groups.
- **Program Parser Config**: Provides program arguments to the program interpreter. Related syntax references: Python's getopt and argparse.

## Domain

Name format: `<domain>.domain`  
Example: `package.domain`

## Domain Interface

Name format: `<domain>.domain.base.toml`  
Example: `package.domain.base.toml`

Configuration format example:

```toml
[operations.install_remote]     # Operation name: install_remote
description = "Install packages from remote repositories"
args = ["pkgs"]                 # Parameters required for install_remote operation: pkgs
```

## Operation Group

Name format: `<operation_group_name>.toml`  
Example: `pacman.toml`, `apt.toml`

Configuration format example:

```toml
[operations.install_remote]             # Operation name: install_remote
cmd_format = "apt install {pkgs}"       # `{pkgs}`: CmdBridge's command line interpreter will extract the pkgs from user input based on the "Program Parser Config" parsing parameters, then replace `{pkgs}` to generate the final cmd.
                                        # Note: The parameter name "pkgs" in `{pkgs}` must match the name defined in the Domain Interface.
```

## Program Parser Config

Name format: `<program_name>.toml`  
Example: `pacman.toml`, `apt.toml`, `apt-file.toml`

Configuration format example:

```toml
[apt.parser_config]
program_name = "apt"                # program name

[[apt.sub_commands]]
name = "install"                    # Define subcommand `install`

[[apt.sub_commands.arguments]]
name = "packages"                   # Positional arguments for subcommand `install`
nargs = "+"
```

---

## Detailed Configuration for Program Parser Config

### Flag Argument

```toml
[[pacman.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"                 # Having opt and nargs = "0" indicates a Flag Argument
```

### Option Argument

Example: `apt --config <config_path> install vim`:

```toml
[[apt.arguments]] 
name = "config"
opt = ["--config"]
nargs = "1"             # Having opt and nargs not equal to 0 indicates an Option Argument
```

### Positional Argument

Example: `pacman -S vim`:

```toml
[pacman.parser_config]
program_name = "pacman"

[[pacman.arguments]]
name = "targets"        # No opt but has nargs indicates a Positional Argument
nargs = "+"
```

### Sub Command

Example: `apt install vim`:

```toml
[[apt.sub_commands]]        # Having sub_commands indicates a subcommand
name = "install"
```

Subcommand aliases. Example: `brew list/ls -v vim`:

```toml
[[brew.sub_commands]]
name = "list"
alias = ["ls"]              # Alias for list is ls
```

### Reusing Subcommand Argument Configurations

**mufw (my ufw) is a custom command**

Example: mufw subcommands allow, deny

```toml
# ## allow
[[mufw.sub_commands]]
name = "allow"
id = "subcmd_id_allow"              # Define id first for reusing its parameters. IDs cannot be duplicated within one config file.

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
include_arguments_and_subcmds = "subcmd_id_allow"       # Reuse allow subcommand's parameter configuration (arguments and subcommands)
id = "subcmd_id_deny"
```

Example: mufw delete subcommand's subcommands allow, deny

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

Summary:
- Through the mufw example, you can create custom commands to map operations within a domain. This way you only need to remember the usage of the custom command to map commands from other operation groups in the same domain.
- If you don't need other operation groups' commands to map to the custom command simultaneously, then you don't need to configure the command parameters for other operation groups, just configure the custom command.

## Additional Parameters for Operation Group

### final_cmd_format

final_cmd_format: Only used when finally mapping to a command, not used in other cases.

Use case:
- For example, I have scripts `my-list-installed-pacman` and `my-list-installed-apt`, both using custom formats to list installed software.
- Reference: [my-list-installed-pacman](https://github.com/JohanChane/intuit-backup/blob/main/Doc/example/lsmipkgs)

Example pacman configuration:

```toml
[operations.my_list_installed]
cmd_format = "pacman -Q --my"
final_cmd_format = "my-list-installed-pacman"       # For ArchLinux platform
```

Corresponding apt configuration:

```toml
[operations.my_list_installed]
cmd_format = "apt list --installed --my"
final_cmd_format = "my-list-installed-apt"          # For Debian platform
```

Usage:

```sh
cmdbridge map -t apt -- pacman -Q --my                      # Maps to: my-list-installed-apt
cmdbridge map -t pacman -- apt list --installed --my        # Maps to: my-list-installed-pacman
```

Program parameter configuration:

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

Through the above examples, you should now know how to extend program parameters.