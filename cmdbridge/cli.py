# cmdbridge/cli.py

import click
import sys

from .cli_helper import CmdBridgeCLIHelper, CustomCommand, create_cli_helper


# Click 命令行接口
@click.group()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: 输出映射后的命令"""
    # 创建 CLI 辅助类实例
    cli_helper = create_cli_helper()
    
    # 设置日志级别
    cli_helper.handle_debug_mode(debug)
    
    ctx.obj = cli_helper


@cli.group()
def config():
    """配置管理命令"""
    pass


@cli.group()
def cache():
    """缓存管理命令"""
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


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-s', '--source-group', help='源程序组（只有无法识别才需要使用）')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def map(ctx, domain, source_group, dest_group):
    """映射完整命令
    
    使用 -- 分隔符将命令参数与 cmdbridge 选项分开：
    cmdbridge map -t apt -- pacman -S vim
    """
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command_args)
    sys.exit(0 if success else 1)


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def op(ctx, domain, dest_group):
    """映射操作和参数
    
    使用 -- 分隔符将操作参数与 cmdbridge 选项分开：
    cmdbridge op -t apt -- install vim
    """
    cli_helper = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    operation_args = ctx.meta.get('protected_args', [])
    
    success = cli_helper.handle_map_operation(domain, dest_group, operation_args)
    sys.exit(0 if success else 1)


@cli.command()
@click.pass_obj
def version(cli_helper):
    """显示版本信息"""
    cli_helper.handle_version()


@cli.command()
@click.pass_obj
def list_cmdbridges(cli_helper):
    """列出所有可用的包管理器"""
    cli_helper.handle_list_cmdbridges()


@cli.command()
@click.argument('source_group')
@click.argument('dest_group')
@click.pass_obj
def output_cmdbridge(cli_helper, source_group, dest_group):
    """输出两个包管理器之间的映射关系
    
    SOURCE_GROUP: 源包管理器名称
    DEST_GROUP: 目标包管理器名称
    """
    cli_helper.handle_output_cmdbridge(source_group, dest_group)


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()