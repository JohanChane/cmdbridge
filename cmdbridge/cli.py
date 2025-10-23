# cmdbridge/cli.py

import click
import sys
from typing import Optional, List
from log import set_level, LogLevel

from .cmdbridge import CmdBridge


class CmdBridgeCLI:
    """cmdbridge 命令行接口"""
    
    def __init__(self):
        # 初始化 CmdBridge 核心功能
        self.cmdbridge = CmdBridge()

    def _init_config(self) -> bool:
        """初始化用户配置"""
        return self.cmdbridge.init_config()
    
    def _refresh_cmd_mappings(self) -> bool:
        """刷新所有命令映射缓存"""
        return self.cmdbridge.refresh_cmd_mappings()
        
    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                   dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令"""
        result = self.cmdbridge.map_command(domain, src_group, dest_group, command_args)
        if result:
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射命令", err=True)
            return False
    
    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> bool:
        """映射操作和参数"""
        result = self.cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射操作", err=True)
            return False


class CustomCommand(click.Command):
    """自定义命令类，支持 -- 分隔符"""
    
    def parse_args(self, ctx, args):
        """解析参数，处理 -- 分隔符"""
        if '--' in args:
            idx = args.index('--')
            # 使用 ctx.meta 来存储保护参数
            ctx.meta['protected_args'] = args[idx+1:]
            args = args[:idx]
        
        return super().parse_args(ctx, args)


# Click 命令行接口
@click.group()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: 输出映射后的命令"""
    # 设置日志级别
    if debug:
        set_level(LogLevel.DEBUG)
        click.echo("🔧 调试模式已启用")
    ctx.obj = CmdBridgeCLI()


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
def init(cli_obj):
    """初始化用户配置目录"""
    success = cli_obj._init_config()
    sys.exit(0 if success else 1)


@cache.command()
@click.pass_obj
def refresh(cli_obj):
    """刷新命令映射缓存"""
    success = cli_obj._refresh_cmd_mappings()
    if success:
        click.echo("命令映射缓存已刷新")
    else:
        click.echo("错误: 刷新命令映射缓存失败", err=True)
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
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])
    if not command_args:
        click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_command(domain, source_group, dest_group, command_args)
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
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    operation_args = ctx.meta.get('protected_args', [])
    if not operation_args:
        click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_operation(domain, dest_group, operation_args)
    sys.exit(0 if success else 1)


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()