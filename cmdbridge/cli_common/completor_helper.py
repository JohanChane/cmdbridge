import sys
from typing import List, Optional
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from cmdbridge.config.path_manager import PathManager
from cmdbridge.cache.cache_mgr import CacheMgr
from log import debug, warning, error


class CommonCompletorHelper:
    """Provides dynamic completion data, retrieves real-time configuration from cache"""

    @staticmethod
    def get_domains() -> List[str]:
        """Return supported domains from configuration"""
        try:
            path_manager = PathManager.get_instance()
            domains = path_manager.get_domains_from_config()
            debug(f"Retrieved domain list: {domains}")
            return domains
        except Exception as e:
            warning(f"Failed to retrieve domain list: {e}")
            return []  # Default fallback value

    @staticmethod
    def get_operation_groups(domain: str) -> List[str]:
        """Return program groups from configuration based on domain"""
        try:
            path_manager = PathManager.get_instance()
            groups = path_manager.get_operation_groups_from_config(domain)
            debug(f"Retrieved program groups for domain '{domain}': {groups}")
            return groups
        except Exception as e:
            warning(f"Failed to retrieve program groups for domain '{domain}': {e}")
            return []

    @staticmethod
    def get_all_operation_groups() -> List[str]:
        """Return all supported program groups"""
        try:
            path_manager = PathManager.get_instance()
            all_groups = path_manager.get_all_operation_groups_from_config()
            debug(f"Retrieved all program groups: {all_groups}")
            return all_groups
        except Exception as e:
            warning(f"Failed to retrieve all program groups: {e}")
            return []

    @staticmethod
    def get_commands(domain: Optional[str], source_group: str) -> List[str]:
        """Retrieve command list for specified domain and source program group from cache"""
        try:
            # If domain not specified, try auto-detection
            if not domain:
                domains = CommonCompletorHelper.get_domains()
                for dom in domains:
                    if source_group in CommonCompletorHelper.get_operation_groups(dom):
                        domain = dom
                        break
            
            if not domain:
                warning(f"Cannot determine domain for source program group '{source_group}'")
                return []
            
            path_manager = PathManager.get_instance()
            cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain)
            
            if not cmd_to_operation_file.exists():
                return []
            
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            # Get all programs for this operation group
            programs = cmd_to_operation_data.get("cmd_to_operation", {}).get(source_group, {}).get("programs", [])
            if not programs:
                return []
            
            # Collect command formats for all programs
            commands = []
            for program_name in programs:
                program_file = path_manager.get_cmd_mappings_group_program_path_of_cache(
                    domain, source_group, program_name
                )
                
                if program_file.exists():
                    try:
                        with open(program_file, 'rb') as f:
                            program_data = tomli.load(f)
                        
                        # Extract all command formats for this program
                        for mapping in program_data.get("command_mappings", []):
                            cmd_format = mapping.get("cmd_format", "")
                            if cmd_format:
                                commands.append(cmd_format)
                                
                    except Exception as e:
                        warning(f"Failed to read program command file {program_file}: {e}")
            
            return commands
            
        except Exception as e:
            warning(f"Failed to retrieve command list (domain={domain}, group={source_group}): {e}")
            return []
        
    @staticmethod
    def get_all_commands(domain: Optional[str]) -> List[str]:
        """Get all commands for specified domain"""
        try:
            all_commands = []
            
            # Determine domain list to process
            domains = [domain] if domain else CommonCompletorHelper.get_domains()
            
            # Collect commands from all domains
            for dom in domains:
                groups = CommonCompletorHelper.get_operation_groups(dom)
                for group in groups:
                    commands = CommonCompletorHelper.get_commands(dom, group)
                    all_commands.extend(commands)
            
            # Deduplicate and return
            return list(set(all_commands))
                
        except Exception as e:
            warning(f"Failed to retrieve all commands (domain={domain}): {e}")
            return []
        
    @staticmethod
    def get_operation_names(domain: Optional[str], dest_group: Optional[str]) -> List[str]:
        """Retrieve operation name list from cache"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            if domain and dest_group:
                # Get operations supported by specific program group
                supported_ops = cache_mgr.get_supported_operations(domain, dest_group)
                debug(f"Retrieved operations supported by {domain}.{dest_group}: {supported_ops}")
                return supported_ops
            elif domain:
                # Get all operations for specified domain
                all_ops = cache_mgr.get_all_operations(domain)
                debug(f"Retrieved all operations for domain '{domain}': {all_ops}")
                return all_ops
            else:
                # Get all operations
                all_ops = []
                domains = CommonCompletorHelper.get_domains()
                for dom in domains:
                    ops = cache_mgr.get_all_operations(dom)
                    all_ops.extend(ops)
                return list(set(all_ops))
                
        except Exception as e:
            warning(f"Failed to retrieve operation names (domain={domain}, group={dest_group}): {e}")
            return []

    @staticmethod
    def get_all_operation_names(domain: Optional[str] = None) -> List[str]:
        """Get all operation names (compatibility method)"""
        return CommonCompletorHelper.get_operation_names(domain, None)

    @staticmethod
    def get_operation_with_params(domain: str, operation_name: str, dest_group: str) -> str:
        """Get operation string with parameter information"""
        try:
            cache_mgr = CacheMgr.get_instance()
            
            # Directly call cache_mgr method, let it handle domain=None case
            params = cache_mgr.get_operation_parameters(domain, operation_name, dest_group)
            
            if params:
                # Format display: operation_name {param1} {param2} ...
                params_display = " ".join([f"{{{param}}}" for param in params])
                return f"{operation_name} {params_display}"
            else:
                # Operation without parameters
                return operation_name
                
        except Exception as e:
            # If error occurs, return original operation name
            warning(f"Failed to retrieve operation parameters: {e}")
            return operation_name
      
    @staticmethod
    def get_domain_for_group(group_name: str) -> Optional[str]:
        return PathManager.get_instance().get_domain_for_group(group_name)