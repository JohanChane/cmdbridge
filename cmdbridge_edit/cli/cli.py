import click
import sys

from .cli_helper import CmdBridgeEditCLIHelper
from cmdbridge.cli_common.completor import DomainType, SourceGroupType, DestGroupType, CommandType, OperationType

def print_version(ctx, param, value):
    """Version information callback function"""
    if not value or ctx.resilient_parsing:
        return
    cli_helper = CmdBridgeEditCLIHelper()
    cli_helper.handle_version()
    ctx.exit()

# Click command line interface
@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--version', is_flag=True, callback=print_version, 
              expose_value=False, is_eager=True, help='Display version information')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge-edit: Place mapped commands in user's line editor
    
    Use -- separator to separate command arguments from cmdbridge-edit options.
    
    Examples:
        cmdbridge-edit map -- pacman -S vim
        cmdbridge-edit op -- install vim git
    """
    # Create CLI helper class instance
    cli_helper = CmdBridgeEditCLIHelper()
    
    # Set log level
    cli_helper.handle_debug_mode(debug)
    
    # If no subcommand, display help information
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    
    ctx.obj = cli_helper


@cli.command()
@click.option('-d', '--domain', type= DomainType(), help='Domain name')
@click.option('-s', '--source-group', type=SourceGroupType(), help='Source program group (only needed when cannot be automatically identified)')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.argument('command', nargs=-1, type=CommandType())
@click.pass_context
def map(ctx, domain, source_group, dest_group, command):
    """Map complete command to line editor
    
    Use -- separator to separate command arguments from cmdbridge-edit options:
    cmdbridge-edit map -t apt -- pacman -S vim
    """
    cli_helper = ctx.obj
    
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command)
    cli_helper.exit_with_success_code(success)


@cli.command()
@click.option('-d', '--domain', type= DomainType(), help='Domain name')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.argument('operation', nargs=-1, type=OperationType())
@click.pass_context
def op(ctx, domain, dest_group, operation):
    """Map operation and parameters to line editor
    
    Use -- separator to separate operation arguments from cmdbridge-edit options:
    cmdbridge-edit op -t apt -- install vim git
    """
    cli_helper = ctx.obj
    
    success = cli_helper.handle_map_operation(domain, dest_group, operation)
    cli_helper.exit_with_success_code(success)


def main():
    """Main entry function"""
    cli()


if __name__ == '__main__':
    main()