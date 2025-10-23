# cmdbridge-edit/cli.py

import click
import sys
import os
from typing import Optional, List

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from cmdbridge.cmdbridge import CmdBridge
from log import set_level, LogLevel


class CmdBridgeEditCLI:
    """cmdbridge-edit 命令行接口"""
    
class CmdBridgeEditCLI:
    """cmdbridge-edit 命令行接口"""
    
    def __init__(self):
        # 初始化 CmdBridge 核心功能
        self.cmdbridge = CmdBridge()

    def _get_default_domain(self) -> str:
        """获取默认领域"""
        return self.cmdbridge._get_default_domain()
    
    def _get_default_group(self) -> str:
        """获取默认程序组"""
        return self.cmdbridge._get_default_group()
    
    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                   dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令并输出到 line editor"""
        result = self.cmdbridge.map_command(domain, src_group, dest_group, command_args)
        if result:
            # 输出映射后的命令到标准输出
            # 使用特殊返回码 113 表示成功映射（供 shell 函数识别）
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射命令", err=True)
            return False
    
    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> bool:
        """映射操作和参数并输出到 line editor"""
        result = self.cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            # 输出映射后的命令到标准输出
            # 使用特殊返回码 113 表示成功映射（供 shell 函数识别）
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
    # 设置日志级别
    if debug:
        set_level(LogLevel.DEBUG)
        click.echo("🔧 调试模式已启用")
    
    # 如果没有子命令，显示帮助信息
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    
    ctx.obj = CmdBridgeEditCLI()


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-s', '--source-group', help='源程序组（只有无法识别才需要使用）')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def map(ctx, domain, source_group, dest_group):
    """映射完整命令到 line editor
    
    使用 -- 分隔符将命令参数与 cmdbridge-edit 选项分开：
    cmdbridge-edit map -t apt -- pacman -S vim
    """
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])
    if not command_args:
        click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_command(domain, source_group, dest_group, command_args)
    
    # 使用特殊退出码 113 表示成功映射（供 shell 函数识别）
    exit_code = 113 if success else 1
    sys.exit(exit_code)


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def op(ctx, domain, dest_group):
    """映射操作和参数到 line editor
    
    使用 -- 分隔符将操作参数与 cmdbridge-edit 选项分开：
    cmdbridge-edit op -t apt -- install vim git
    """
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    operation_args = ctx.meta.get('protected_args', [])
    if not operation_args:
        click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_operation(domain, dest_group, operation_args)
    
    # 使用特殊退出码 113 表示成功映射（供 shell 函数识别）
    exit_code = 113 if success else 1
    sys.exit(exit_code)


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    from cmdbridge import __version__
    click.echo(f"cmdbridge-edit 版本: {__version__}")


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()