import click
import sys

from .cli_helper import CmdBridgeCLIHelper
from ..cli_common.completor import DomainType, SourceGroupType, DestGroupType, CommandType, OperationType

def print_version(ctx, param, value):
    """Version information callback function"""
    if not value or ctx.resilient_parsing:
        return
    cli_helper = CmdBridgeCLIHelper()
    cli_helper.handle_version()
    ctx.exit()

# Click command line interface
@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--version', is_flag=True, callback=print_version, 
              expose_value=False, is_eager=True, help='Display version information')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: Output mapped commands
    
    Use -- separator to separate command arguments from cmdbridge options.
    
    Examples:
        cmdbridge map -- pacman -S vim
        cmdbridge op -- install vim git
    """
    # Create CLI helper class instance
    cli_helper = CmdBridgeCLIHelper()
    
    # Set log level
    cli_helper.handle_debug_mode(debug)

    # If no subcommand, display help information
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)
    
    ctx.obj = cli_helper


@cli.group()
def config():
    """Configuration management commands"""
    pass


@cli.group()
def cache():
    """Cache management commands"""
    pass


@cli.group()
def list():
    """List mapping information commands"""
    pass


@config.command()
@click.pass_obj
def init(cli_helper):
    """Initialize user configuration directory"""
    success = cli_helper.handle_init_config()
    sys.exit(0 if success else 1)


@cache.command()
@click.pass_obj
def refresh(cli_helper):
    """Refresh command mapping cache"""
    success = cli_helper.handle_refresh_cache()
    sys.exit(0 if success else 1)


@list.command()
@click.option('-d', '--domain', type=DomainType(), help='Domain name')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.pass_obj
def op_cmds(cli_helper, domain, dest_group):
    """Output operation mappings
    
    Examples:
        cmdbridge list op-cmds
        cmdbridge list -d package -t apt op-cmds
    """
    cli_helper.handle_list_op_cmds(domain, dest_group)


@list.command()
@click.option('-d', '--domain', type=DomainType(), help='Domain name')
@click.option('-s', '--source-group', required=True, type=SourceGroupType(), help='Source program group')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.pass_obj
def cmd_mappings(cli_helper, domain, source_group, dest_group):
    """Output mappings between commands
    
    Examples:
        cmdbridge list cmd-mappings
        cmdbridge list -d package -s pacman -t apt cmd-mappings
    """
    cli_helper.handle_list_cmd_mappings(domain, source_group, dest_group)

@list.command()
@click.pass_obj
def all(cli_helper):
    """Display support status for all domains, operation groups, and operations"""
    cli_helper.handle_list_all()

@cli.command()
@click.option('-d', '--domain', type=DomainType(), help='Domain name')
@click.option('-s', '--source-group', type=SourceGroupType(), help='Source program group (only needed when cannot be automatically identified)')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.argument('command', nargs=-1, type=CommandType())
@click.pass_context
def map(ctx, domain, source_group, dest_group, command):
    """Map complete command
    
    Use -- separator to separate command arguments from cmdbridge options:
    cmdbridge map -t apt -- pacman -S vim
    """

    cli_helper = ctx.obj
    
    success = cli_helper.handle_map_command(domain, source_group, dest_group, command)
    sys.exit(0 if success else 1)


@cli.command()
@click.option('-d', '--domain', type=DomainType(), help='Domain name')
@click.option('-t', '--dest-group', required=True, type=DestGroupType(), help='Destination program group')
@click.argument('operation', nargs=-1, type=OperationType())
@click.pass_context
def op(ctx, domain, dest_group, operation):
    """Map operation and parameters
    
    Use -- separator to separate operation arguments from cmdbridge options:
    cmdbridge op -t apt -- install vim git
    """
    cli_helper = ctx.obj
    
    success = cli_helper.handle_map_operation(domain, dest_group, operation)
    sys.exit(0 if success else 1)

def main():
    """Main entry function"""
    cli()


if __name__ == '__main__':
    main()