import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge.cmdbridge import CmdBridge
from cmdbridge.cache.cache_mgr import CacheMgr

class CommonCliHelper:
    """cmdbridge command line helper class - handles CLI business logic"""
    
    def __init__(self):
        # Initialize CmdBridge core functionality
        self._cmdbridge = CmdBridge()
    
    def get_cmdbridge(self) -> CmdBridge:
        return self._cmdbridge
    
    def handle_debug_mode(self, debug: bool) -> None:
        """Handle debug mode settings"""
        if debug:
            set_level(LogLevel.DEBUG)
            click.echo("🔧 Debug mode enabled")
        else:
            set_level(LogLevel.INFO)

    def handle_version(self) -> None:
        """Handle version information display"""
        from .. import __version__
        click.echo(f"cmdbridge version: {__version__}")

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        """Map complete command
        
        Returns:
            bool: Returns True if successful, False if failed
        """
        if not command_args:
            click.echo("Error: Must provide command to map, use -- separator", err=True)
            return False
        
        result = self._cmdbridge.map_command(domain, src_group, dest_group, command_args)
        if result:
            # Output mapped command to standard output
            click.echo(result)
            return True
        else:
            click.echo("Error: Cannot map command", err=True)
            return False

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        """Map operation and parameters
        
        Returns:
            bool: Returns True if successful, False if failed
        """
        if not operation_args:
            click.echo("Error: Must provide operation to map, use -- separator", err=True)
            return False
        
        result = self._cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            # Output mapped command to standard output
            click.echo(result)
            return True
        else:
            click.echo("Error: Cannot map operation", err=True)
            return False
        
    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        """Get domain for program group based on group name"""
        return self.get_cmdbridge().path_manager.get_domain_for_group(group_name)