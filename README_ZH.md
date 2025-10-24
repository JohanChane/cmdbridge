# CmdBridge - 智能命令映射工具

一个强大的命令行工具，用于在不同包管理器之间智能映射命令。让你在任意系统上使用熟悉的包管理器语法！

## 🌟 特性

- **多包管理器支持**: pacman, apt, dnf, brew, zypper
- **智能命令解析**: 自动识别命令意图（安装、搜索、更新等）
- **灵活映射**: 将任何包管理器命令映射到目标包管理器
- **安全执行**: 交互式确认和强制执行模式
- **易于扩展**: 基于配置文件的模块化设计 (用配置实现命令映射)
- **详细调试**: 丰富的日志输出和调试信息

## 安装

```sh
# 从源码安装
git clone https://github.com/your-username/cmdbridge.git
cd cmdbridge
pipx install .
```

### 命令补全

#### zsh

```sh
if command -v cmdbridge &>/dev/null; then
  eval "$(_CMDBRIDGE_COMPLETE=zsh_source cmdbridge)"
fi

if command -v cmdbridge-edit &>/dev/null; then
  eval "$(_CMDBRIDGE_EDIT_COMPLETE=zsh_source cmdbridge-edit)"
fi

alias am="cmdbridge"

cmde() {
  local cmd
  output="$(command cmdbridge-edit "$@" 2>&1)"
  local ret=$?

  case $ret in
    113) print -z -- "$output" ;;   # 映射成功的返回码是 113
    0)   echo "$output" ;;
    *)   echo "$output" >&2 ;;
  esac
}
compdef cmde=cmdbridge-edit
```

## 基本使用

init-config and set default target cmdbridge:

```sh
# 初始化用户配置（首次使用）
cmdbridge-config --init-config

# 编辑 ~/.config/cmdbridge/config.toml, 配置默认的
default_target_cmdbridge = "<your default target>"  # `cmdbridge -t, --target` 会覆盖这个选项
```

cmde: 将映射之后的命令放到 line editor
-   map: 自动检测 map 之后的命令来映射到 target cmdbridge
-   op: 使用 operation name 来映射命令

cmde map:

```sh
cmde map -- pacman -S vim git         # 如果 target cmdbridge 是 `apt`, 则生成 `apt install vim git`
# 如果你忘记了 pip 显示包的信息的命令, 则可以使用任意一种你熟悉的方式来执行
cmde -t pip map -- pacman -Si neovim  # pip show neovim
cmde -t pip map -- brew info neovim   # pip show neovim
```

cmde op:

```sh
cmde op -- install vim git           # 如果 target cmdbridge 是 `pacman`, 则生成 `pacman -S vim git`
cmde -t pip op -- info neovim        # 生成 `pip show neovim`

# 如果有动作 grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
cmde op -- grep_log foo.log bar.log == ERROR == write
# 会生成 cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

list cmdbridge:

```sh
cmdbridge --list-cmdbridges
```

output cmdbridge mapping:

```sh
cmdbridge --output-cmdbridge pacman apt
```

## 🎯 使用示例

### 使用你熟悉的包管理来安装 vim git

```sh
# debian
cmde map -- apt install vim git
# arch
cmde map -- pacman -S search vim git
```

### 使用你熟悉的动作来安装 vim git

```sh
# use `install` operation
cmdbridge op -- install vim git
```

### 临时切换目标

```sh
# 如果你忘记了 pip 显示包的信息的命令, 则可以使用任意一种你熟悉的方式来执行
cmdbridge-edit -t pip map -- pacman -Si <pkg>   # 会映射为: pip show <pkg>
# OR
cmdbridge-edit -t pip map -- brew info <pkg>
```

### cmdbridge

cmdbridge: 和 cmde 的区别是, 它只是输出映射后的命令
-   map: 和 cmde map 的用法一样
-   op: 和 cmde op 的用法一样

```sh
# 将 apt 命令映射到 target cmdbridge
cmdbridge map -- apt install vim git
# 如果 target_cmdbridge 是 "pacman"，则映射为: pacman -S vim git

# 将 pacman 命令映射到 apt cmdbridge
cmdbridge -t apt map -- pacman -S vim git  # 映射为: apt install vim git

# 查看 pacman actman 到 apt cmdbridge 的映射
cmdbridge --output-cmdbridge pacman apt
```

cmdbridge op:

```sh
cmdbridge op -- install vim git
# 如果 target_cmdbridge 是 "pacman"，则执行: pacman -S vim git
```

## 使用 cmdbridge-config 管理 cmdbridge 配置

```sh
# 初始化用户配置（创建 ~/.config/cmdbridge/）
cmdbridge-config --init-config

# 使用 cmdbridges
cmdbridge-config --use-cmdbridges pacman,apt,dnf,brew,zypper,scoop,winget,chocolatey

# 新增 cmdbridges
cmdbridge-config --add-cmdbridges brew,scoop,winget

# 查看支持的 cmdbridges
cmdbridge-config --list-cmdbridges
```

## `cmdbridge-config` 的 cmdbridge 配置

### 已经配置的 cmdbridges

```sh
cmdbridge --list-cmdbridges
```

```
ℹ️ INFO: 📦 Package managers in current configuration:
  ✅ apt - supports 15 operations
  ✅ brew - supports 15 operations
  ✅ cargo - supports 8 operations
  ✅ chocolatey - supports 15 operations
  ✅ dnf - supports 15 operations
  ✅ npm - supports 8 operations
  ✅ pacman - supports 15 operations
  ✅ pip - supports 10 operations
  ✅ scoop - supports 15 operations
  ✅ winget - supports 15 operations
  ✅ zypper - supports 15 operations
```

### output-cmdbridge examples

pacman -> apt:

```sh
cmdbridge --output-cmdbridge pacman apt
```

```
================================================================================
Status Operation          Source Command            Target Command
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
Status Operation          Source Command            Target Command
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

## cmdbridge 配置格式说明

See [ref](./doc/cmdbridge_config_zh.md)