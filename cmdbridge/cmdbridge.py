import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import tomli

from .config.path_manager import PathManager
from cmdbridge.cache.cache_mgr import CacheMgr
from cmdbridge.config.config_mgr import ConfigMgr
from .cache.parser_config_mgr import ParserConfigCacheMgr
from .cache.cmd_mapping_mgr import CmdMappingMgr
from .core.cmd_mapping import CmdMapping
from .core.operation_mapping import OperationMapping
from log import debug, info, warning, error


class CmdBridge:
    """CmdBridge Core Functionality Class"""
    
    def __init__(self):
        # Initialize path manager
        self.path_manager = PathManager()
        
        # Initialize configuration utilities
        self.cache_mgr = CacheMgr.get_instance()
        self.config_mgr = ConfigMgr()

        # Initialize program configuration cache manager
        self.parser_cache_mgr = ParserConfigCacheMgr()

        # Initialize command mapper
        self.command_mapper = CmdMapping({})
        
        # Initialize operation mapper - simplified constructor
        self.operation_mapper = OperationMapping()
        
        # Initialize mapping configuration cache
        self._mapping_config_cache = {}
        
        # Load global configuration
        self.global_config = self._load_global_config()

    def _load_global_config(self) -> dict:
        """Load global configuration"""
        config_file = self.path_manager.get_global_config_path()
        if config_file.exists():
            try:
                with open(config_file, 'rb') as f:
                    return tomli.load(f)
            except Exception as e:
                warning(f"Cannot read global configuration file: {e}")
        return {}
    
    def _auto_detect_source_group(self, command: str, domain: str) -> Optional[str]:
        """Automatically detect the group to which the source command belongs"""
        if not command.strip():
            return None
        
        # Get the first word of the command (program name)
        program_name = command.strip().split()[0]
        debug(f"Auto-detecting source operation group, command: '{command}', program name: '{program_name}', domain: '{domain}'")
        
        # Use cmd_to_operation.toml to find the operation group to which the program belongs
        cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path(domain)
        if not cmd_to_operation_file.exists():
            debug(f"cmd_to_operation file does not exist: {cmd_to_operation_file}")
            return None
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            # Find the operation group containing this program across all operation groups
            for op_group, group_data in cmd_to_operation_data.get("cmd_to_operation", {}).items():
                if program_name in group_data.get("programs", []):
                    debug(f"Auto-detection successful: program '{program_name}' belongs to operation group '{op_group}'")
                    return op_group
                    
            debug(f"Auto-detection failed: no operation group found for program '{program_name}'")
            return None
            
        except Exception as e:
            error(f"Failed to read cmd_to_operation file: {e}")
            return None

    def _get_mapping_config(self, domain: str, group_name: str) -> Dict[str, Any]:
        """Get mapping configuration for specified domain and program group"""
        cache_key = f"{domain}.{group_name}"
        if cache_key not in self._mapping_config_cache:
            # Load mapping configuration for this program group from cache file
            cache_file = self.path_manager.get_cmd_mappings_domain_dir_of_cache(domain) / f"{group_name}.toml"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._mapping_config_cache[cache_key] = tomli.load(f)
                except Exception as e:
                    warning(f"Failed to load {cache_key} mapping configuration: {e}")
                    self._mapping_config_cache[cache_key] = {}
            else:
                self._mapping_config_cache[cache_key] = {}
        
        return self._mapping_config_cache[cache_key]

    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                    dest_group: str, command_args: List[str]) -> Optional[str]:
        """Map complete command"""
        try:
            # Combine argument list into command string
            command_str = ' '.join(command_args)
            if not command_str:
                return None
            
            # Set default values
            domain = domain or self.path_manager.get_domain_for_group(dest_group)
            if domain is None:
                raise ValueError("Domain must be specified")
            
            # Auto-detect source group (if not specified)
            if not src_group:
                src_group = self._auto_detect_source_group(command_str, domain)
                if not src_group:
                    return None
            
            # Extract actual program name from command
            actual_program_name = command_args[0] if command_args else None
            if not actual_program_name:
                return None
            
            # Load mapping configuration using cross-operation group lookup
            self.command_mapper = CmdMapping.load_from_cache(domain, actual_program_name)
            
            # Load parser configuration for source program
            parser_config_file = self.path_manager.get_parser_config_path_of_cache(actual_program_name)
            if not parser_config_file.exists():
                error(f"Cannot find parser configuration for {actual_program_name}")
                return None
            
            # from parsers.config_loader import load_parser_config_from_file
            parser_cache_mgr = ParserConfigCacheMgr()
            source_parser_config = parser_cache_mgr.load_from_cache(actual_program_name)
            
            # Use the correct map_to_operation method
            operation_result = self.command_mapper.map_to_operation(
                source_cmdline=command_args,
                source_parser_config=source_parser_config,
                dst_operation_group=dest_group
            )
            
            if not operation_result:
                return None
            
            # Use OperationMapping to generate final command
            result_cmd = self.operation_mapper.generate_command(
                operation_name=operation_result["operation_name"],
                params=operation_result["params"],
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group,
            )
            
            return result_cmd
            
        except Exception as e:
            error(f"Command mapping failed: {e}")
            return None
        
    def map_operation(self, domain: Optional[str], dest_group: str, 
                operation_args: List[str]) -> Optional[str]:
        """Map operation and parameters"""
        try:
            # Combine argument list into operation string
            operation_str = ' '.join(operation_args)
            if not operation_str:
                return None
            
            # Set default values
            domain = domain or self.path_manager.get_domain_for_group(dest_group)
            if domain is None:
                raise ValueError("Domain must be specified")
            
            # Parse operation string, extract operation name and parameters
            parts = operation_str.split()
            if not parts:
                return None
            
            # First argument is operation name
            operation_name = parts[0]
            params = {}
            
            # Get actual parameter list for this operation
            cache_mgr = CacheMgr.get_instance()
            expected_params = cache_mgr.get_operation_parameters(domain, operation_name, dest_group)
            
            if expected_params:
                # Parse parameters based on expected parameter names
                if len(parts) > 1:
                    # Simple processing: if only one expected parameter, give all remaining arguments to it
                    if len(expected_params) == 1:
                        param_name = expected_params[0]
                        params[param_name] = " ".join(parts[1:])
                    else:
                        # If multiple expected parameters, need more complex parsing logic
                        # Simplified processing here, assign in order
                        for i, param_name in enumerate(expected_params):
                            if i + 1 < len(parts):
                                params[param_name] = parts[i + 1]
                            else:
                                params[param_name] = ""  # Give empty value for missing parameters
            else:
                # No expected parameters, but user provided parameters, issue warning
                if len(parts) > 1:
                    warning(f"Operation {operation_name} does not require parameters, but provided: {' '.join(parts[1:])}")
            
            # Call OperationMapping to generate command
            result = self.operation_mapper.generate_command(
                operation_name=operation_name,
                params=params,
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group
            )
            
            return result
                
        except Exception as e:
            error(f"Operation mapping failed: {e}")
            return None

    def refresh_cmd_mappings(self) -> bool:
        """Refresh all command mapping caches"""
        try:
            # 1. Delete all cache directories
            success = self.cache_mgr.remove_all_cache()
            if not success:
                return False
            
            if success:
                # 1. First refresh parser configuration cache
                self.parser_cache_mgr.generate_parser_config_cache()

                # First merge all domain configurations to cache directory
                info("Merging domain configurations to cache...")
                merge_success = self.cache_mgr.merge_all_domain_configs()
                if not merge_success:
                    warning("Failed to merge domain configurations")
                
                # Generate mapping data for each domain
                domains = self.path_manager.get_domains_from_config()
                for domain in domains:
                    # Ensure cache directories exist
                    self.path_manager.get_cmd_mappings_domain_of_cache(domain).mkdir(parents=True, exist_ok=True)
                    self.path_manager.get_operation_mappings_domain_dir_of_cache(domain).mkdir(parents=True, exist_ok=True)
                    
                    # Get domain configuration directory
                    domain_config_dir = self.path_manager.get_operation_domain_dir_of_config(domain)
                    parser_configs_dir = self.path_manager.program_parser_config_dir
                    
                    if domain_config_dir.exists() and parser_configs_dir.exists():
                        # Get all program groups for this domain
                        groups = self.path_manager.get_operation_groups_from_config(domain)
                        
                        for group_name in groups:
                            try:
                                # Create CmdMappingMgr instance for each program group
                                group_creator = CmdMappingMgr(domain, group_name)
                                
                                # Generate mapping data
                                mapping_data = group_creator.create_mappings()
                                
                                if mapping_data:  # Only write if there is mapping data
                                    # Write mapping files
                                    group_creator.write_to()
                                    info(f"✅ Generated command mappings for {domain}.{group_name}")
                                else:
                                    warning(f"⚠️ No mapping data generated for {domain}.{group_name}")
                                    
                            except Exception as e:
                                error(f"❌ Failed to generate command mappings for {domain}.{group_name}: {e}")
                                continue
                        
                        # Use OperationMappingCreator to generate operation mapping files
                        from .cache.operation_mapping_mgr import create_operation_mappings_for_domain
                        op_mapping_success = create_operation_mappings_for_domain(domain)
                        if op_mapping_success:
                            info(f"✅ Completed operation mapping generation for {domain} domain")
                        else:
                            warning(f"⚠️ Failed to generate operation mappings for {domain} domain")
                        
                        info(f"✅ Completed command mapping generation for all program groups in {domain} domain")
                    else:
                        warning(f"⚠️ Skipping {domain} domain: configuration directory does not exist")
                
                return True
            return False
        except Exception as e:
            error(f"Failed to refresh command mappings: {e}")
            return False

    def init_config(self) -> bool:
        """Initialize user configuration"""
        return self.config_mgr.init_config()