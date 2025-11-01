## cmdbridge

cmdbridge: Outputs the mapped command

```
cmdbridge [-h/--help]
cmdbridge [--debug]
# `--` cannot be omitted
cmdbridge map [-d <domain> -s <src_group> -t <dst_group>] -- pacman -S vim  # `-s <src_group>`: Only needed when automatic identification fails
cmdbridge op [-d <domain> -t <dst_group>] -- install vim
```

If not specified, defaults to:

${XDG_CONFIG_HOME:-$HOME/.config}"/cmdbridge/config.toml

Long options:
    -d/--domain
    -s/--source-group
    -t/--dest-group

Update cmd_mappings cache:

```bash
cmdbridge --refresh-cmd-mappings
```

Default configuration path: "${XDG_CONFIG_HOME:-$HOME/.config}"/cmdbridge
Default cache path: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge
cmd_mappings cache path: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge/cmd_mappings/{domain}
operation_mappings cache path: "${XDG_CACHE_HOME:-$HOME/.cache}"/cmdbridge/operation_mappings/{domain}

Output operation mappings:

```
cmdbridge list op-mappings [-d <domain> -t <dst_group>] 
```

Output mappings between commands:

```
cmdbridge list cmd-mappings [-d <domain> -s <src_group> -t <dst_group>]
```

## cmdbridge-edit

cmdbridge-edit: Places the mapped command in the user's line editor

```
cmdbridge-edit [-h/--help]
cmdbridge-edit [--debug]
# `--` cannot be omitted
cmdbridge-edit map [-d <domain> -s <src_group> -t <dst_group>] -- pacman -S vim
cmdbridge-edit op [-d <domain> -t <dst_group>] -- install vim
```