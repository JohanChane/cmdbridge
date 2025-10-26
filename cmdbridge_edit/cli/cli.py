# cmdbridge_edit/cli/cli.py

import click
import sys

from .cli_helper import CmdBridgeEditCLIHelper, create_edit_cli_helper  # 更新导入路径
from .completor import DomainType, SourceGroupType, DestGroupType, CommandType, OperationType


# Click 命令行接口
@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge-edit: 将映射后命令放在用户的 line editor
    
    使用 -- 分隔符将命令参数与 cmdbridge-edit 选项分开。
    
    示例:
        cmdbridge-edit map -- pacman -S vim
        cmdbridge-edit op -- install vim git
    """
    # 创建 CLI 辅助类实例
    cli_helper = create_edit_cli_helper()
    
    # 设置日志级别
    cli_helper.handle_debug_mode(debug)
    
    # 如果没有子命令，显示帮助信息
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    
    ctx.obj = cli_helper


@cli.command()
@click.option('-d', '--domain', type= DomainType(), help='领域名称')
@click.option('-s', '--source-group', type=SourceGroupType(), help='源程序组（只有无法识别才需要使用）')
@click.option('-t', '--dest-group', type=DestGroupType(), help='目标程序组')
@click.argument('command', nargs=1, type=CommandType())
@click.pass_context
def map(ctx, domain, source_group, dest_group):
    """映射完整命令到 line editor
    
    使用 -- 分隔符将命令参数与 cmdbridge-edit 选项分开：
    cmdbridge-edit map -t apt -- pacman -S vim
    """
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command_args)
    cli_helper.exit_with_success_code(success)


@cli.command()
@click.option('-d', '--domain', help='领域名称')
@click.option('-t', '--dest-group', help='目标程序组')
@click.argument('operation', nargs=1, type=OperationType())
@click.pass_context
def op(ctx, domain, dest_group):
    """映射操作和参数到 line editor
    
    使用 -- 分隔符将操作参数与 cmdbridge-edit 选项分开：
    cmdbridge-edit op -t apt -- install vim git
    """
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    operation_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_operation(domain, dest_group, operation_args)
    cli_helper.exit_with_success_code(success)


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    cli_helper = ctx.obj
    cli_helper.handle_version()


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()