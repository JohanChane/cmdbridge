# CmdBridge

A tool for mapping command lines based on command-line syntax parsing.

<img alt="Welcome to CmdBridge" src="https://github.com/user-attachments/assets/238030ec-1e44-4ff9-95f2-44a146f87164"/>

## Languages

[中文](./README_ZH.md)

## Installation

### Install from Source

```sh
git clone https://github.com/your-username/cmdbridge.git
cd cmdbridge
pipx install .
```

### Command Completion

#### zsh

<details>
<summary>zshrc</summary>

```sh
# cmdbridge completion
eval "$(_CMDBRIDGE_COMPLETE=zsh_source cmdbridge)"

# cmdbridge-edit completion
eval "$(_CMDBRIDGE_EDIT_COMPLETE=zsh_source cmdbridge-edit)"

# Custom completion function (also, completions after `--` do not use escape characters)
_cmdbridge_custom_complete() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[cmdbridge] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _CMDBRIDGE_COMPLETE=zsh_complete cmdbridge)}")

    for type key descr in ${response}; do
        if [[ "$type" == "no_escape" ]]; then
            # Special handling: no escaping
            completions+=("$key")
        elif [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        # Key: use the -Q option to avoid escaping
        compadd -Q -U -V unsorted -a completions
    fi
}

_cmdbridge_edit_custom_complete() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[cmdbridge-edit] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _CMDBRIDGE_EDIT_COMPLETE=zsh_complete cmdbridge-edit)}")

    for type key descr in ${response}; do
        if [[ "$type" == "no_escape" ]]; then
            # Special handling: no escaping
            completions+=("$key")
        elif [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        # Key: use the -Q option to avoid escaping
        compadd -Q -U -V unsorted -a completions
    fi
}

# Register completion functions
compdef _cmdbridge_custom_complete cmdbridge
#compdef _cmdbridge_edit_custom_complete cmdbridge-edit

# bbe wrapper function - alias for cmdbridge-edit
bbe() {
  local output
  output="$(command cmdbridge-edit "$@" 2>&1)"
  local ret=$?

  case $ret in
    113) print -z -- "$output" ;;  # Special exit code: populate command line with output
    0)   echo "$output" ;;         # Normal exit: display output
    *)   echo "$output" >&2        # Error exit: display to stderr
         return $ret ;;
  esac
}

# Also register completion for bbe
compdef _cmdbridge_edit_custom_complete bbe
```

</details>

## Basic Usage

Initialize config and refresh cache:

```sh
# Initialize user config (first-time use)
cmdbridge config init

# Refresh cache after every config update
cmdbridge cache refresh
```

bbe: Places the mapped command into the line editor.
-   map: Automatically detects the source command and maps it to the target command.
-   op: Uses the operation name to map commands.

bbe map:

```sh
bbe map -t apt -- pacman -S vim git         # Maps to `apt install vim git`
# If you forget the pip command to show package info, you can use any familiar way to execute it
bbe map -t pip -- pacman -Si neovim         # pip show neovim
bbe map -t pip -- brew info neovim          # pip show neovim
```

bbe op:

```
bbe op -t pacman -- install vim git           # Maps to `pacman -S vim git`
bbe op -t pip -- info neovim                  # Maps to `pip show neovim`

# If there is an action grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
bbe op -t <dest_operation_group> -- grep_log "foo.log bar.log" "ERROR" "write"
# Generates cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

List command mappings:

```sh
cmdbridge list cmd-mappings -s apt -t pacman
```

List operation commands:

```sh
cmdbridge list op-cmds -t pacman
```

## 🎯 Usage Examples

### Use your familiar package manager to install vim git

```sh
# debian
bbe map -t apt -- apt install vim git
# arch
bbe map -t apt -- pacman -S search vim git
```

### Use your familiar operation name to install vim git

```sh
# use `install_remote` operation
cmdbridge op -t pacman -- install_remote vim git
```

### Temporarily switch targets

```
# If you forget the pip command to show package information, you can use any familiar way to execute it
cmdbridge map -t pip -- pacman -Si <pkg>   # Maps to: pip show <pkg>
# OR
cmdbridge map -t pip -- brew info <pkg>
```

### cmdbridge

cmdbridge: The difference from bbe is that it only outputs the mapped command.

```sh
cmdbridge map -t pacman -- apt install vim git  # Maps to `pacman -S vim git`
cmdbridge map -t apt -- pacman -S vim git       # Maps to `apt install vim git`
cmdbridge list all
cmdbridge list cmd-mappings -s pacman -t apt    # View mappings from the `pacman` operation group to the `apt` operation group
```

cmdbridge op:

```sh
cmdbridge op -t pacman -- install vim git       # Maps to `pacman -S vim git`
```

## Docs

-   [configs](./docs/configs.md)
-   [cmdbridge_clis](./docs/cmdbridge_clis.md)

See [ref](./docs)

## Useful Configurations

Generally speaking, there is no need to learn the configuration syntax of cmdbridge. I will maintain a set of useful configurations:
- [cmdbridge-configs](https://github.com/JohanChane/cmdbridge-configs)
  - Currently, package management and firewall management have been added. Repository management (git/svn), process management (ps), etc., will be added later.

If you are familiar with the configuration syntax of cmdbridge, you can customize your own set of configurations or submit a PR to the repository above.