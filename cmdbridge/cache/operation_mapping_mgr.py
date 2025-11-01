import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import tomli_w  # type: ignore
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class OperationMappingMgr:
    """Operation Mapping Creator - Generates separated operation mapping files"""
    
    def __init__(self, domain_name: str):
        """
        Initialize operation mapping creator
        
        Args:
            domain_name: Domain name (e.g., "package", "process")
        """
        # Use singleton PathManager
        self.path_manager = PathManager.get_instance()
        self.domain_name = domain_name
    
    def create_mappings(self) -> Dict[str, Any]:
        """
        Create separated operation mapping files for specified domain
        
        Returns:
            Dict[str, Any]: Dictionary containing operation mapping data, structure:
            {
                "operation_to_program": Dict[str, Dict[str, List[str]]],  # Operation to operation group to program mapping
                "command_formats_by_group": Dict[str, Dict[str, Dict[str, str]]]   # Operation group to program to command format mapping
            }
        """
        try:
            # Get domain configuration directory
            domain_config_dir = self.path_manager.get_operation_domain_dir_of_config(self.domain_name)
            if not domain_config_dir.exists():
                warning(f"Domain configuration directory does not exist: {domain_config_dir}")
                return {}
            
            # Get operation mapping cache directory
            cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache(self.domain_name)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect mapping data
            operation_to_program = {}  # Structure: {operation: {operation_group: [programs]}}
            command_formats_by_group = {}  # Structure: {operation_group: {program: {command_formats}}}
            
            # 1. First load domain base file
            base_file = self.path_manager.get_domain_base_path_of_config(self.domain_name)
            base_operations = {}
            if base_file.exists():
                try:
                    with open(base_file, 'rb') as f:
                        base_data = tomli.load(f)
                    if "operations" in base_data:
                        base_operations = base_data["operations"]
                    debug(f"Loaded base operation definitions: {base_file}")
                except Exception as e:
                    warning(f"Failed to parse base operation file {base_file}: {e}")
            else:
                warning(f"Domain base file does not exist: {base_file}")
            
            # 2. Traverse all program files in program group directory
            for config_file in domain_config_dir.glob("*.toml"):
                operation_group = config_file.stem  # Configuration file name is the operation group name
                debug(f"Processing operation group file: {config_file}, operation group: {operation_group}")
                
                try:
                    with open(config_file, 'rb') as f:
                        group_data = tomli.load(f)
                    
                    # Initialize command format storage for operation group
                    if operation_group not in command_formats_by_group:
                        command_formats_by_group[operation_group] = {}
                    
                    # Collect operation to program mapping
                    if "operations" in group_data:
                        for operation_key, operation_config in group_data["operations"].items():
                            # Extract operation name from operation_key (remove operation group suffix)
                            operation_parts = operation_key.split('.')
                            if len(operation_parts) > 1 and operation_parts[-1] == operation_group:
                                operation_name = '.'.join(operation_parts[:-1])
                            else:
                                operation_name = operation_key
                            
                            # Extract actual program name from command format
                            actual_program_name = self._extract_program_from_cmd_format(operation_config)
                            if not actual_program_name:
                                actual_program_name = operation_group  # Fallback to operation group name
                            
                            debug(f"Operation {operation_name}: operation_group={operation_group}, actual_program={actual_program_name}")
                            
                            # Add to operation to program mapping
                            if operation_name not in operation_to_program:
                                operation_to_program[operation_name] = {}
                            
                            if operation_group not in operation_to_program[operation_name]:
                                operation_to_program[operation_name][operation_group] = []
                            
                            if actual_program_name not in operation_to_program[operation_name][operation_group]:
                                operation_to_program[operation_name][operation_group].append(actual_program_name)
                            
                            # Collect command formats grouped by operation group and program name
                            if actual_program_name not in command_formats_by_group[operation_group]:
                                command_formats_by_group[operation_group][actual_program_name] = {}
                            
                            if "cmd_format" in operation_config:
                                command_formats_by_group[operation_group][actual_program_name][operation_name] = operation_config["cmd_format"]
                            
                            # Collect final_cmd_format
                            if "final_cmd_format" in operation_config:
                                final_key = f"{operation_name}_final"
                                command_formats_by_group[operation_group][actual_program_name][final_key] = operation_config["final_cmd_format"]
                                debug(f"Loaded final_cmd_format: {operation_name}.{operation_group}.{actual_program_name} -> {operation_config['final_cmd_format']}")
                                
                except Exception as e:
                    warning(f"Failed to parse operation group file {config_file}: {e}")
                    continue
            
            # 3. Verify all operations implemented by programs have corresponding definitions in base
            for operation_name in operation_to_program.keys():
                if operation_name not in base_operations:
                    warning(f"Operation {operation_name} not defined in base definition file")
            
            # Prepare return data
            mapping_data = {
                "operation_to_program": operation_to_program,
                "command_formats_by_group": command_formats_by_group
            }
            
            # Generate separated files
            
            # 1. Operation to program mapping file (placed in operation_mappings directory)
            operation_to_program_file = self.path_manager.get_operation_to_program_path(self.domain_name)
            with open(operation_to_program_file, 'wb') as f:
                tomli_w.dump({"operation_to_program": operation_to_program}, f)
            info(f"✅ Generated operation_to_program.toml file: {operation_to_program_file}")
            
            # 2. Create directories and generate command format files for each operation group
            for operation_group, programs_data in command_formats_by_group.items():
                # Ensure operation group directory exists
                self.path_manager.ensure_operation_mappings_group_dir(self.domain_name, operation_group)
                
                for program_name, command_formats in programs_data.items():
                    program_command_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
                        self.domain_name, operation_group, program_name
                    )
                    with open(program_command_file, 'wb') as f:
                        tomli_w.dump({"commands": command_formats}, f)
                    info(f"✅ Generated {operation_group}/{program_name}_commands.toml file: {program_command_file}")
            
            return mapping_data
            
        except Exception as e:
            error(f"Failed to generate operation mapping files: {e}")
            return {}
    
    def _extract_program_from_cmd_format(self, operation_config: Dict[str, Any]) -> Optional[str]:
        """
        Extract actual program name from command format
        
        Args:
            operation_config: Operation configuration
            
        Returns:
            Optional[str]: Extracted program name, returns None if cannot extract
        """
        cmd_format = operation_config.get("cmd_format") or operation_config.get("final_cmd_format")
        if not cmd_format:
            return None
        
        # Extract first word of command as program name
        parts = cmd_format.strip().split()
        if parts:
            program_name = parts[0]
            debug(f"Extracted program name from command format '{cmd_format}': {program_name}")
            return program_name
        
        return None


# Convenience functions
def create_operation_mappings_for_domain(domain_name: str) -> bool:
    """
    Convenience function: Create operation mappings for specified domain
    
    Args:
        domain_name: Domain name
        
    Returns:
        bool: Whether creation succeeded
    """
    creator = OperationMappingMgr(domain_name)
    mapping_data = creator.create_mappings()
    # Consider successful as long as there is data
    return bool(mapping_data)

def create_operation_mappings_for_all_domains() -> bool:
    """
    Convenience function: Create operation mappings for all domains
    
    Returns:
        bool: Whether all domain creations succeeded
    """
    path_manager = PathManager.get_instance()
    domains = path_manager.get_domains_from_config()
    
    all_success = True
    for domain in domains:
        try:
            success = create_operation_mappings_for_domain(domain)
            if success:
                info(f"✅ Completed operation mapping generation for {domain} domain")
            else:
                error(f"❌ Failed to generate operation mappings for {domain} domain")
                all_success = False
        except Exception as e:
            error(f"❌ Exception occurred while generating operation mappings for {domain} domain: {e}")
            all_success = False
    
    return all_success