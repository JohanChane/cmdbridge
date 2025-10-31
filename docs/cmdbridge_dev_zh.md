# cmdbridge 的开发笔记

## 目的

简单记录一下, 防止时间久忘了。也为了以后的重构。有部分 ai 写的代码质量不高, 没有太多的时间写代码。当然我已经将处理流程模块化且解耦, 就算 ai 的部分代码混乱也在控制之中。

## 整体的处理流程

### map_cmd_to_operation

map_cmd_to_operation: 对比用户输入的命令行与 source operation group 的 cmd_format 的命令行语法解析的结果 (CommandTree)CommandTree, 从而得出 "操作名" 和 "参数"。

比如:

```sh
pacman -S vim git
```

得出

```json
{
    "operation_name": "install_remote",
    "params": {
        "pkgs": "vim git"
    }
}
```

### map_operation_to_cmd

map_operation_to_cmd: 将 map_cmd_to_operation 得出的结果, 替换 cmd_format 从而生成最终的映射命令。

比如:

```json
{
    "operation_name": "install_remote",
    "params": {
        "pkgs": "vim git"
    }
}
```

如果 install_remote 的 cmd_format = "apt install {pkgs}", 则得出:

```
apt install vim git
```

### 总结

-   cmdbridge 的 op 操作就是用 map_operation_to_cmd
-   cmdbridge 的 map 操作就是用 map_cmd_to_operation -> map_operation_to_cmd

## cmd_mappings 的缓存

cmd_mappings cache: 是针对 map_cmd_to_operation 的。

### 如何判断 source cmdline 的 cmd_format 和提取相应的参数

生成 cmd_format 的语法树 (CommandTree):
-   根据命令的参数配置生成 cmd_format 的示例命令。为什么要先生成示例命令:
    -   比如: `{pkgs}` 的参数配置可能是多个, 而 `{pkgs}` 的字符串并不符合参数配置的要求。
    -   所以根据 nargs 生成相应的参数 `__param_pkgs_1__, __param_pkgs_2__`。
-   用命令行解释器生成 cmd_format 的示例命令的语法树 (CommandTree)
-   判断参数的格式, 如果是 `__param_pkgs_1__, __param_pkgs_2__` 样子的, 则标识 `placehold: {param_name: "pkgs"}`

对比 source cmdline 的语法树和 cmd_format 的语法树:
-   先判断 CommandNode 的 name, len(arguments)。
-   比较它们的 `set(arguments)`。当然 option_value 和 positional_value 如果有 placehold 则跳过判断它们的具体值。
-   如果有子命令则重复上面的步骤 (递归)。

如果语法树相同, 则取出参数 (同时遍历两个语法树即可) 和操作名。

## operation_mappings 的缓存

operation_mappings cache: 是针对 map_operation_to_cmd 的。

比如, map_cmd_to_operation 的结果是:

```json
{
    "operation_name": "install_remote",
    "params": {
        "pkgs": "vim git"
    }
}
```

查找 target operation group 的 install_remote, 直接替换即可。