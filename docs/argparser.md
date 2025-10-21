## arg parser 的 parse 结果的数据结构

arg_type:
-   sub_cmd
-   arg         # 表示 `-` 开头的, 且可以带参数的, 不是 flag。e.g. -o/--output <path>,
-   flag        # 表示是一个 flag
-   value       # 存放 arg 的值的类型

比如: gen-config --help gen --force --output dst_path src_path_1 src_path_2 -- abc

arg_parse_result:

{
    cmd_name: "gen-config",
    args: [
        {name: "--help", type: flag, repeat: 1},
        {name: "gen", type: sub_cmd, args:  [
            {name: "--force", type: flag, repeat: 1},
            {name: "--output", type: arg},
            {name: "dst_path", type: value, values: ["dst_path"]},
            {name: "src_paths", type: value, values: ["src_path_1", "src_path_2"]},
        ]},
    ],
    extra: "abc"  # None/"", `--` 之后的字符串, None 表示没有出现, "" 表示出现了但是后面为空。
}

这样定义数据的好处:
-   可以按顺序处理
-   只要保证 arg 类型的参数的下一个兄弟是 value arg 即可。

def parse(cmd: String) -> arg_parse_result:

### 参数解析的流程

#### getopt

pacman -Ss vim git

根据 Parameter Parsing 配置,  pacman 的 nargs="*", 而 -S is_flag, 所以有

{
    cmd_name: "pacman",
    args: [
        {name: "-S", type: flag, repeat: 1},
        {name: "-s", type: flag, repeat: 1},
        {name: "files", type: value, values: ["vim", "git"]},
    ]
    extras: None
}

根据 getopt 的标准:
-   `-Ss` 表示 `-S -s`
-   --file -s <file>, 则 --file 的 value 不是 <file>。value 一定要在 --file 的旁边, 中间不能隔着。
    -   命令则不影响。比如: pacman -S vim, 中间隔着 `-S`
-   没有 sub_cmd

#### argparse

apt -h list --installed vim

根据 Parameter Parsing 配置,  apt 的 nargs="*", 和有 --installed 和 list 的 args="*" 所以有:

{
    cmd_name: "apt",
    args: [
        {name: "h", type: flag, repeat: 1},
        {name: "list", type: sub_cmd, args: [
            {name: "--installed", type: flag, repeat},
            {name: "pkg", type: value, values: ["vim"]}
        ]
        },
    ]
    extras: None
}

根据 argparse 的标准和 getopt 差不多只是有了 sub_cmd:
-   sub_cmd 的 arg values 可以被隔着和命令一样。

### 可以区分有没有传参数

怎么区分有没有传入包名:

```sh
cmdbridge -t pacman map apt list --installed            # pacman -Q
cmdbridge -t pacman map apt list --installed vim git    # pacman -Qs vim git
```

因为 list_installed 组没有 pkgs 参数, 而 search_local 组有:

```toml
[actions.list_installed.apt]
cmd_format = "apt list --installed"

[actions.search_local.apt]
cmd_format = "apt list --installed {pkgs}"      #  `{pkgs}` 用户要安装的包且 `{pkgs}` 不能为空
```

所以有大括号的 `{pkgs}` 是表示不能为空 (即不能省略)。