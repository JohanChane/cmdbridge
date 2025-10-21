# CmdBridge - Intelligent Command Mapping Tool

A powerful command-line tool for intelligently mapping commands between different package managers. Let you use familiar package manager syntax on any system!

## 🌟 Features

- **Multi-Package Manager Support**: pacman, apt, dnf, brew, zypper
- **Intelligent Command Parsing**: Automatically recognizes command intent (install, search, update, etc.)
- **Flexible Mapping**: Map any package manager command to target package manager
- **Safe Execution**: Interactive confirmation and force execution modes
- **Easy Extensibility**: Modular design based on configuration files (command mapping implemented via configuration)
- **Detailed Debugging**: Rich log output and debug information

## Installation

```sh
# Install from source
git clone https://github.com/your-username/cmdbridge.git
cd cmdbridge
pipx install .
```

### Command Completion

#### zsh

```sh
if command -v cmdbridge &>/dev/null; then
  eval "$(_ACTMAP_COMPLETE=zsh_source cmdbridge)"
fi

if command -v cmdbridge-edit &>/dev/null; then
  eval "$(_ACTMAP_EXECUTE_COMPLETE=zsh_source cmdbridge-edit)"
fi

alias am="cmdbridge"

cmde() {
  local cmd
  output="$(command cmdbridge-edit "$@" 2>&1)"
  local ret=$?

  case $ret in
    113) print -z -- "$output" ;;   # Return code 113 indicates successful mapping
    0)   echo "$output" ;;
    *)   echo "$output" >&2 ;;
  esac
}
compdef cmde=cmdbridge-edit
```

## Basic Usage

init-config and set default target cmdbridge:

```sh
# Initialize user configuration (first-time use)
cmdbridge-config --init-config

# Edit ~/.config/cmdbridge/config.toml, configure default
default_target_cmdbridge = "<your default target>"  # `cmdbridge -t, --target` will override this option
```

cmde: Put the mapped command into the line editor
-   map: Automatically detect commands after map to map to target cmdbridge
-   act: Use action name to map commands

cmde map:

```sh
cmde map -- pacman -S vim git         # If target cmdbridge is `apt`, generates `apt install vim git`
# If you forget pip command to show package info, you can use any familiar way to execute
cmde -t pip map -- pacman -Si neovim  # pip show neovim
cmde -t pip map -- brew info neovim   # pip show neovim
```

cmde act:

```sh
cmde act -- install vim git           # If target cmdbridge is `pacman`, generates `pacman -S vim git`
cmde -t pip act -- info neovim        # Generates `pip show neovim`

# If there's an action grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
cmde act -- grep_log foo.log bar.log == ERROR == write
# Will generate cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

list cmdbridge:

```sh
cmdbridge --list-cmdbridges
```

output cmdbridge mapping:

```sh
cmdbridge --output-cmdbridge pacman apt
```

## 🎯 Usage Examples

### Use Your Familiar Package Manager to Install vim git

```sh
# debian
cmde map -- apt install vim git
# arch
cmde map -- pacman -S search vim git
```

### Use Your Familiar Action to Install vim git

```sh
# use `install` action
cmdbridge act -- install vim git
```

### Temporarily Switch Targets

```sh
# If you forget pip command to show package info, you can use any familiar way to execute
cmdbridge-edit -t pip map -- pacman -Si <pkg>   # Will map to: pip show <pkg>
# OR
cmdbridge-edit -t pip map -- brew info <pkg>
```

### cmdbridge

cmdbridge: The difference from cmde is that it only outputs the mapped command
-   map: Same usage as cmde map
-   act: Same usage as cmde act

```sh
# Map apt command to target cmdbridge
cmdbridge map -- apt install vim git
# If target_cmdbridge is "pacman", maps to: pacman -S vim git

# Map pacman command to apt cmdbridge
cmdbridge -t apt map -- pacman -S vim git  # Maps to: apt install vim git

# View mapping from pacman cmdbridge to apt cmdbridge
cmdbridge --output-cmdbridge pacman apt
```

cmdbridge act:

```sh
cmdbridge act -- install vim git
# If target_cmdbridge is "pacman", executes: pacman -S vim git
```

## Using cmdbridge-config to Manage cmdbridge Configuration

```sh
# Initialize user configuration (creates ~/.config/cmdbridge/)
cmdbridge-config --init-config

# Use cmdbridges
cmdbridge-config --use-cmdbridges pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey

# Add cmdbridges
cmdbridge-config --add-cmdbridges brew,scoop,winget

# View supported cmdbridges
cmdbridge-config --list-cmdbridges
```

## `cmdbridge-config` cmdbridge Configuration

### Configured cmdbridges

```sh
cmdbridge --list-cmdbridges
```

```
ℹ️ INFO: 📦 Package managers in current configuration:
  ✅ apt - supports 15 actions
  ✅ brew - supports 15 actions
  ✅ cargo - supports 8 actions
  ✅ chocolatey - supports 15 actions
  ✅ dnf - supports 15 actions
  ✅ npm - supports 8 actions
  ✅ pacman - supports 15 actions
  ✅ pip - supports 10 actions
  ✅ scoop - supports 15 actions
  ✅ winget - supports 15 actions
  ✅ zypper - supports 15 actions
```

### output-cmdbridge examples

pacman -> apt:

```sh
cmdbridge --output-cmdbridge pacman apt
```

```
================================================================================
Status Action          Source Command            Target Command
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          apt install {pkgs}
✅    remove          pacman -R {pkgs}          apt remove {pkgs}
✅    search          pacman -Ss {pkgs}         apt search {pkgs}
✅    update          pacman -Sy                apt update
✅    upgrade         pacman -Syu               apt upgrade
✅    force_update    pacman -Syy               apt update --refresh-all
✅    force_upgrade   pacman -Syyu              apt update --refresh-all && apt upgrade
✅    info            pacman -Si {pkgs}         apt show {pkgs}
✅    list_installed  pacman -Q                 apt list --installed
✅    clean           pacman -Sc                apt autoclean
✅    help            pacman -h                 apt --help
✅    list_files      pacman -Ql {pkgs}         dpkg -L {pkgs}
✅    find_file_owner pacman -Qo {files}        dpkg -S {files}
✅    find_file_owner_remote pacman -F {files}         apt-file search {files}
✅    download_source asp export {pkgs}         apt source {pkgs}
================================================================================
```

pacman -> pip:

```sh
cmdbridge --output-cmdbridge pacman pip
```

```
================================================================================
Status Action          Source Command            Target Command
--------------------------------------------------------------------------------
✅    install         pacman -S {pkgs}          pip install {pkgs}
✅    remove          pacman -R {pkgs}          pip uninstall {pkgs}
✅    search          pacman -Ss {pkgs}         pip search {pkgs}
✅    update          pacman -Sy                pip install --upgrade pip
✅    upgrade         pacman -Syu               pip install --upgrade {pkgs}
❌    force_update    pacman -Syy               Not supported
❌    force_upgrade   pacman -Syyu              Not supported
✅    info            pacman -Si {pkgs}         pip show {pkgs}
✅    list_installed  pacman -Q                 pip list
✅    clean           pacman -Sc                pip cache purge
✅    help            pacman -h                 pip --help
❌    list_files      pacman -Ql {pkgs}         Not supported
❌    find_file_owner pacman -Qo {files}        Not supported
❌    find_file_owner_remote pacman -F {files}         Not supported
✅    download_source asp export {pkgs}         pip download {pkgs}
================================================================================
```

## CmdBridge Configuration Format Reference

See [ref](./doc/cmdbridge_config.md)