# CmdBridge

一个根据命令行语法解析来转换命令行的工具。

<img alt="Welcome to CmdBridge" src="https://github.com/user-attachments/assets/da132b90-ef25-48dd-b6d2-5734dfa7f75d"/>

## 安装

### 从源码安装

```sh
git clone https://github.com/your-username/cmdbridge.git
cd cmdbridge
pipx install .
```

### 命令补全

#### zsh

<details>
<summary>zshrc</summary>

```sh
# cmdbridge 补全
eval "$(_CMDBRIDGE_COMPLETE=zsh_source cmdbridge)"

# cmdbridge-edit 补全
eval "$(_CMDBRIDGE_EDIT_COMPLETE=zsh_source cmdbridge-edit)"

# 自定义补全函数 (同时 `--` 后面的补全不使用转义字符)
_cmdbridge_custom_complete() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[cmdbridge] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _CMDBRIDGE_COMPLETE=zsh_complete cmdbridge)}")

    for type key descr in ${response}; do
        if [[ "$type" == "no_escape" ]]; then
            # 特殊处理：不使用转义
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
        # 关键：使用 -Q 选项避免转义
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
            # 特殊处理：不使用转义
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
        # 关键：使用 -Q 选项避免转义
        compadd -Q -U -V unsorted -a completions
    fi
}

# 注册补全函数
compdef _cmdbridge_custom_complete cmdbridge
#compdef _cmdbridge_edit_custom_complete cmdbridge-edit

# bbe 包装函数 - cmdbridge-edit 的别名
bbe() {
  local output
  output="$(command cmdbridge-edit "$@" 2>&1)"
  local ret=$?

  case $ret in
    113) print -z -- "$output" ;;  # 特殊退出码：将输出填充到命令行
    0)   echo "$output" ;;         # 正常退出：显示输出
    *)   echo "$output" >&2        # 错误退出：显示到标准错误
         return $ret ;;
  esac
}

# 为 bbe 也注册补全
compdef _cmdbridge_edit_custom_complete bbe
```

</details>

## 基本使用

init config and refresh cache:

```sh
# 初始化用户配置（首次使用）
cmdbridge config init

# 每次更新配置后, 都需要刷新缓存
cmdbridge cache refresh
```

bbe: 将映射之后的命令放到 line editor
-   map: 自动检测 map 之后的命令来映射到目标命令
-   op: 使用 operation name 来映射命令

bbe map:

```sh
bbe map -t apt -- pacman -S vim git         # 映射为 `apt install vim git`
# 如果你忘记了 pip 显示包的信息的命令, 则可以使用任意一种你熟悉的方式来执行
bbe map -t pip -- pacman -Si neovim         # pip show neovim
bbe map -t pip -- brew info neovim          # pip show neovim
```

bbe op:

```
bbe op -t pacman -- install vim git           # 映射为 `pacman -S vim git`
bbe op -t pip -- info neovim                  # 映射为 `pip show neovim`

# 如果有动作 grep_log: cat foo.log bar.log | grep -i '{log_level}' | grep -i '{log_msg}'
bbe op -t <dest_operation_group> -- grep_log "foo.log bar.log" "ERROR" "write"
# 会生成 cat foo.log bar.log | grep -i 'ERROR' | grep -i 'write'
```

list cmd mappings:

```sh
cmdbridge list cmd-mappings -s apt -t pacman
```

list operation commands:

```sh
cmdbridge list op-cmds -t pacman
```

## 🎯 使用示例

### 使用你熟悉的包管理来安装 vim git

```sh
# debian
bbe map -t apt -- apt install vim git
# arch
bbe map -t apt -- pacman -S search vim git
```

### 使用你熟悉的操作名来安装 vim git

```sh
# use `install_remote` operation
cmdbridge op -t pacman -- install_remote vim git
```

### 临时切换目标

```
# 如果你忘记了 pip 显示包的信息的命令, 则可以使用任意一种你熟悉的方式来执行
cmdbridge map -t pip -- pacman -Si <pkg>   # 会映射为: pip show <pkg>
# OR
cmdbridge map -t pip -- brew info <pkg>
```

### cmdbridge

cmdbridge: 和 bbe 的区别是, 它只是输出映射后的命令。

```sh
cmdbridge map -t pacman -- apt install vim git  # 映射为 `pacman -S vim git`
cmdbridge map -t apt -- pacman -S vim git       # 映射为 `apt install vim git`
cmdbridge list cmd-mappings -s pacman -t apt    # 查看 `pacman` operation group 到 `pacman` operation group 的映射
```

cmdbridge op:

```sh
cmdbridge op -t pacman -- install vim git       # 映射为 `pacman -S vim git`
```

## Docs

-   [configs](./docs/configs_zh.md)
-   [cmdbridge_clis](./docs/cmdbridge_clis_zh.md)

See [ref](./docs)

## 比较实用的配置

-   [cmdbridge-configs](https://github.com/JohanChane/cmdbridge-configs)
