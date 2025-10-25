# cmdbridge/cli/cli.py

import click
import sys

from .cli_helper import CmdBridgeCLIHelper, CustomCommand, create_cli_helper
from ..click_ext.params import domain_option, dest_group_option, operation_argument, source_group_option, command_argument
from ..click_ext.completor import DynamicCompleter


# Click 命令行接口
@click.group(invoke_without_command=True) 
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: 输出映射后的命令"""
    # 创建 CLI 辅助类实例
    cli_helper = create_cli_helper()
    
    # 设置日志级别
    cli_helper.handle_debug_mode(debug)
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)

    ctx.obj = cli_helper


@cli.group()
def config():
    """配置管理命令"""
    pass


@cli.group()
def cache():
    """缓存管理命令"""
    pass


@cli.group()
def list():
    """列出映射信息命令"""
    pass


@config.command()
@click.pass_obj
def init(cli_helper):
    """初始化用户配置目录"""
    success = cli_helper.handle_init_config()
    sys.exit(0 if success else 1)


@cache.command()
@click.pass_obj
def refresh(cli_helper):
    """刷新命令映射缓存"""
    success = cli_helper.handle_refresh_cache()
    sys.exit(0 if success else 1)


@list.command()
@domain_option()
@dest_group_option()
@click.pass_obj
def op_cmds(cli_helper, domain, dest_group):
    """输出动作映射
    
    示例:
        cmdbridge list op-cmds
        cmdbridge list -d package -t apt op-cmds
    """
    cli_helper.handle_list_op_cmds(domain, dest_group)


@list.command()
@domain_option()
@source_group_option()
@dest_group_option()
@click.pass_obj
def cmd_mappings(cli_helper, domain, source_group, dest_group):
    """输出命令之间的映射
    
    示例:
        cmdbridge list cmd-mappings
        cmdbridge list -d package -s pacman -t apt cmd-mappings
    """
    cli_helper.handle_list_cmd_mappings(domain, source_group, dest_group)   

def get_map_completions(ctx, args, incomplete):
    """map 命令的补全回调"""
    # 这里实现 map 命令的补全逻辑
    return DynamicCompleter.get_command_completions(ctx, None, incomplete)

def get_op_completions(ctx, args, incomplete):
    """op 命令的补全回调"""
    # 这里实现 op 命令的补全逻辑
    return DynamicCompleter.get_operation_completions(ctx, None, incomplete)

# 暂时恢复 map 命令到工作状态
@cli.command(cls=CustomCommand)
@domain_option()
@source_group_option() 
@dest_group_option()
@command_argument()  # 恢复这个
@click.pass_context
def map(ctx, domain, source_group, dest_group, command_parts):  # 恢复这个参数
    """映射完整命令"""
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])

    # command_parts 已经通过补全参数获取
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command_args)
    sys.exit(0 if success else 1)

@cli.command(cls=CustomCommand)
@domain_option()
@dest_group_option()
@operation_argument()
@click.pass_context
def op(ctx, domain, dest_group, operation_parts):
    import sys
    
    cli_helper = ctx.obj
    operation_args = ctx.meta.get('protected_args', [])
    
    if operation_parts:
        operation_args = list(operation_parts) + operation_args
        
    success = cli_helper.handle_map_operation(domain, dest_group, operation_args)
    sys.exit(0 if success else 1)


@cli.command()
@click.pass_obj
def version(cli_helper):
    """显示版本信息"""
    cli_helper.handle_version()


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()