import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge.cmdbridge import CmdBridge
from cmdbridge.cache.cache_mgr import CacheMgr
from ..cli_common import CommonCliHelper

class CmdBridgeCLIHelper:
    """cmdbridge command line helper class - handles CLI business logic"""
    
    def __init__(self):
        self._common_cli_helper = CommonCliHelper()
    
    def _get_common_cli_helper(self) -> CommonCliHelper:
        return self._common_cli_helper
    
    def _get_cmdbridge(self) -> CmdBridge:
        return self._get_common_cli_helper().get_cmdbridge()
    
    def handle_debug_mode(self, debug: bool) -> None:
        return self._get_common_cli_helper().handle_debug_mode(debug)

    def handle_version(self) -> None:
        return self._get_common_cli_helper().handle_version()

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        return self._get_common_cli_helper().handle_map_command(domain, src_group, dest_group, command_args)

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        return self._get_common_cli_helper().handle_map_operation(domain, dest_group, operation_args)

    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        return self._get_common_cli_helper().get_domain_for_group(group_name)
    
    def handle_init_config(self) -> bool:
        """Initialize user configuration"""
        success = self._get_cmdbridge().init_config()
        if success:
            click.echo("✅ User configuration initialized successfully")
        else:
            click.echo("❌ User configuration initialization failed", err=True)
        return success

    def handle_refresh_cache(self) -> bool:
        """Refresh command mapping cache"""
        success = self._get_cmdbridge().refresh_cmd_mappings()
        if success:
            click.echo("✅ Command mapping cache refreshed successfully")
        else:
            click.echo("❌ Command mapping cache refresh failed", err=True)
        return success
    
    def handle_list_op_cmds(self, domain: Optional[str], dest_group: str) -> None:
        """Output operation mappings - use shlex to handle parameter display"""
        cache_mgr = CacheMgr.get_instance()
        domain = domain or self.get_domain_for_group(dest_group)
        if domain is None:
            raise ValueError("Domain must be specified")

        if dest_group:
            operations = cache_mgr.get_supported_operations(domain, dest_group)
            
            if not operations:
                click.echo("❌ This program group does not support any operations")
                return
            
            # Collect all operation and parameter information
            op_data = []
            for op in sorted(operations):
                # Get operation parameters
                params = cache_mgr.get_operation_parameters(domain, op, dest_group)
                op_data.append((op, params))
            
            # Calculate maximum operation name length for alignment
            max_op_len = max(len(op) for op, _ in op_data) if op_data else 0
            
            # Use shlex to safely format parameters
            for op, params in op_data:
                if params:
                    # Use shlex.quote to ensure safe parameter display
                    param_display = ' '.join([f'{{{param}}}' for param in params])
                    # Align output
                    click.echo(f"{op:<{max_op_len}} {param_display}")
                else:
                    click.echo(f"{op:<{max_op_len}}")
        else:
            operations = cache_mgr.get_all_operations(domain)
            for op in sorted(operations):
                click.echo(op)

    def handle_list_cmd_mappings(self, domain: Optional[str], source_group: Optional[str], 
                            dest_group: Optional[str]) -> None:
        """Output mappings between commands - simplified version"""
        cache_mgr = CacheMgr.get_instance()
        
        # Set default values
        if source_group is None:
            raise ValueError("Source group must be specified")
        if dest_group is None:
            raise ValueError("Destination group must be specified")
        domain = domain or self.get_domain_for_group(dest_group)
        if domain is None:
            raise ValueError("Domain must be specified")

        # Get all operations
        operations = cache_mgr.get_all_operations(domain)
        if not operations:
            click.echo("❌ No operations found")
            return
        
        # Collect data
        operation_data = []
        
        for operation in operations:
            # Get source command format
            source_programs = cache_mgr.get_supported_programs(domain, operation)
            if source_group not in [pg for pg in source_programs]:
                continue
                
            source_cmd_format = cache_mgr.get_command_format(domain, operation, source_group)
            if not source_cmd_format:
                continue
                
            # Get target command format
            target_cmd_format = cache_mgr.get_command_format(domain, operation, dest_group)
            final_cmd_format = cache_mgr.get_final_command_format(domain, operation, dest_group)
            
            if target_cmd_format or final_cmd_format:
                display_cmd = final_cmd_format if final_cmd_format else target_cmd_format
                operation_data.append((operation, source_cmd_format, display_cmd))
        
        if not operation_data:
            click.echo("❌ No valid command mappings found")
            return
        
        # Calculate column widths
        max_op_len = max(len(op) for op, _, _ in operation_data)
        max_source_len = max(len(source) for _, source, _ in operation_data)
        
        # Output aligned results        
        for operation, source, target in operation_data:
            click.echo(f"{operation:<{max_op_len}} {source:<{max_source_len}} -> {target}")