## cmdbridge

cmdbridge: 输出映射后的命令

```
cmdbridge [-h/--help]
cmdbridge [--debug]
# `--` 不能省略
cmdbridge map [-d <domain> -s <src_group> -t <dst_group>] -- pacman -S vim  # `-s <src_group>`: 只有无法识别才需要使用
cmdbridge op [-d <domain> -t <dst_group>] -- install vim
```

如果不指定则默认是:

${XDG_CONFIG_HOME:-$HOME/.config}"/cmdbridge/config.toml

长选项:
    -d/--domain
    -s/--source-group
    -t/--dest-group

更新 cmd_mappings 缓存:

```bash
cmdbridge --refresh-cmd-mappings
```

配置的默认路径: "${XDG_CONFIG_HOME:-$HOME/.config}"/cmdbridge
缓存的默认路径: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge
cmd_mappings 缓存的路径: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge/cmd_mappings/{domain}
operation_mappings 缓存的路径: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge/operation_mappings/{domain}

输出动作映射:

```
cmdbridge list op-mappings [-d <domain> -t <dst_group>] 
```

输出命令之间的映射:

```
cmdbridge list cmd-mappings [-d <domain> -s <src_group> -t <dst_group>]
```

## cmdbridge-edit

cmdbridge-edit: 将映射后命令放在用户的 line_editor

```
cmdbridge-edit [-h/--help]
cmdbridge-edit [--debug]
# `--` 不能省略
cmdbridge-edit map [-d <domain> -s <src_group> -t <dst_group>] -- pacman -S vim
cmdbridge-edit op [-d <domain> -t <dst_group>] -- install vim
```