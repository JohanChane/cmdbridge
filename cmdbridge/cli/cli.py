# cmdbridge/cli/cli.py

import click
import sys

from .cli_helper import CmdBridgeCLIHelper
from ..cli_common.completor import DomainType, SourceGroupType, DestGroupType, CommandType, OperationType


# Click 命令行接口
@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: 输出映射后的命令
    
    使用 -- 分隔符将命令参数与 cmdbridge 选项分开。
    
    示例:
        cmdbridge map -- pacman -S vim
        cmdbridge op -- install vim git
    """
    # 创建 CLI 辅助类实例
    cli_helper = CmdBridgeCLIHelper()
    
    # 设置日志级别
    cli_helper.handle_debug_mode(debug)
    
    # 如果没有子命令，显示帮助信息
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
@click.option('-d', '--domain', type=DomainType(), help='领域名称')
@click.option('-t', '--dest-group', type=DestGroupType(), help='目标程序组')
@click.pass_obj
def op_cmds(cli_helper, domain, dest_group):
    """输出动作映射
    
    示例:
        cmdbridge list op-cmds
        cmdbridge list -d package -t apt op-cmds
    """
    cli_helper.handle_list_op_cmds(domain, dest_group)


@list.command()
@click.option('-d', '--domain', type=DomainType(), help='领域名称')
@click.option('-s', '--source-group', type=SourceGroupType(), help='源程序组')
@click.option('-t', '--dest-group', type=DestGroupType(), help='目标程序组')
@click.pass_obj
def cmd_mappings(cli_helper, domain, source_group, dest_group):
    """输出命令之间的映射
    
    示例:
        cmdbridge list cmd-mappings
        cmdbridge list -d package -s pacman -t apt cmd-mappings
    """
    cli_helper.handle_list_cmd_mappings(domain, source_group, dest_group)


@cli.command()
@click.option('-d', '--domain', type=DomainType(), help='领域名称')
@click.option('-s', '--source-group', type=SourceGroupType(), help='源程序组（只有无法识别才需要使用）')
@click.option('-t', '--dest-group', type=DestGroupType(), help='目标程序组')
@click.argument('command', nargs=-1, type=CommandType())
@click.pass_context
def map(ctx, domain, source_group, dest_group, command):
    """映射完整命令
    
    使用 -- 分隔符将命令参数与 cmdbridge 选项分开：
    cmdbridge map -t apt -- pacman -S vim
    """

    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    # command_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command)
    sys.exit(0 if success else 1)


@cli.command()
@click.option('-d', '--domain', type=DomainType(), help='领域名称')
@click.option('-t', '--dest-group', type=DestGroupType(), help='目标程序组')
@click.argument('operation', nargs=-1, type=OperationType())
@click.pass_context
def op(ctx, domain, dest_group, operation):
    """映射操作和参数
    
    使用 -- 分隔符将操作参数与 cmdbridge 选项分开：
    cmdbridge op -t apt -- install vim git
    """
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    # operation_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_operation(domain, dest_group, operation)
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