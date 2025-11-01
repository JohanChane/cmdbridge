import sys
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli
from typing import Dict, List, Optional
from pathlib import Path

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class OperationMapping:
    """Operation Mapper - Generates target commands based on operation names and parameters"""

    def __init__(self):
        """Initialize operation mapper"""
        # Directly use PathManager singleton
        self.path_manager = PathManager.get_instance()
        self.operation_to_program = {}
        self.command_formats = {}
        self._loaded = False  # Add loading status flag

    def _ensure_loaded(self) -> None:
        """Ensure operation mapping is loaded (lazy loading)"""
        if not self._loaded:
            self._load_operation_mapping()
            self._loaded = True

    def _load_operation_mapping(self) -> None:
        """Load separated operation mapping files from cache directory"""
        debug("Starting to load operation mapping from cache...")
        
        domains = self.path_manager.get_domains_from_config()
        if not domains:
            warning("No domain configurations found")
            return
        
        for domain in domains:
            # Get operation mapping cache directory
            cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache(domain)
            
            # 1. Load operation to program mapping file
            operation_to_program_file = self.path_manager.get_operation_to_program_path(domain)  # Use new path
            if operation_to_program_file.exists():
                try:
                    with open(operation_to_program_file, 'rb') as f:
                        operation_data = tomli.load(f)
                    
                    if "operation_to_program" in operation_data:
                        for op_name, groups in operation_data["operation_to_program"].items():
                            if op_name not in self.operation_to_program:
                                self.operation_to_program[op_name] = {}
                            # Merge operation group information
                            for group_name, programs in groups.items():
                                if group_name not in self.operation_to_program[op_name]:
                                    self.operation_to_program[op_name][group_name] = []
                                # Deduplicate and add
                                for program in programs:
                                    if program not in self.operation_to_program[op_name][group_name]:
                                        self.operation_to_program[op_name][group_name].append(program)
                                debug(f"Loaded operation mapping: {op_name}.{group_name} -> {self.operation_to_program[op_name][group_name]}")
                                
                except Exception as e:
                    warning(f"Failed to load operation to program mapping file {operation_to_program_file}: {e}")
            else:
                debug(f"Operation to program mapping file does not exist: {operation_to_program_file}")
            
            # 2. Load command format files for all operation groups
            for group_dir in cache_dir.iterdir():
                if group_dir.is_dir():
                    group_name = group_dir.name
                    for command_file in group_dir.glob("*_commands.toml"):
                        program_name = command_file.stem.replace("_commands", "")
                        
                        try:
                            with open(command_file, 'rb') as f:
                                command_data = tomli.load(f)
                            
                            if "commands" in command_data:
                                if program_name not in self.command_formats:
                                    self.command_formats[program_name] = {}
                                self.command_formats[program_name].update(command_data["commands"])
                                debug(f"Loaded {group_name}/{program_name} command formats: {len(command_data['commands'])} commands")
                                    
                        except Exception as e:
                            warning(f"Failed to load command format file {command_file}: {e}")
        
        debug(f"Operation mapping loading completed: {len(self.operation_to_program)} operations, {len(self.command_formats)} programs")

    def generate_command(self, operation_name: str, params: Dict[str, str],
                        dst_operation_domain_name: str, 
                        dst_operation_group_name: str, use_final_format: bool = False) -> str:
        """
        Generate target command
        
        Args:
            operation_name: Operation name (e.g., "install_remote", "search_remote")
            params: Parameter dictionary
            dst_operation_domain_name: Target domain name
            dst_operation_group_name: Target program name
            
        Returns:
            str: Generated command line string
            
        Raises:
            ValueError: If operation is not supported or command format not found
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        # 1. Check if domain exists
        if not self.path_manager.domain_exists(dst_operation_domain_name):
            raise ValueError(f"Domain '{dst_operation_domain_name}' does not exist")
        
        # 2. Check if operation supports target operation group and get actual program name
        supported_groups = self.operation_to_program.get(operation_name, {})
        if dst_operation_group_name not in supported_groups:
            raise ValueError(f"Operation {operation_name} does not support operation group {dst_operation_group_name}, supported operation groups: {list(supported_groups.keys())}")
        
        # Get list of programs supported under this operation group
        supported_programs = supported_groups[dst_operation_group_name]
        if not supported_programs:
            raise ValueError(f"Operation {operation_name} has no supported programs under operation group {dst_operation_group_name}")
        
        # Use the first supported program (usually only one)
        actual_program_name = supported_programs[0]
        debug(f"Operation {operation_name} uses program {actual_program_name} under operation group {dst_operation_group_name}")
        
        # 3. Get command format - prioritize final_cmd_format
        cmd_format = self.get_final_command_format(operation_name, actual_program_name)
        format_type = "final_cmd_format"
        
        # If no final_cmd_format, fall back to regular cmd_format
        if not cmd_format:
            cmd_format = self.get_command_format(operation_name, actual_program_name)
            format_type = "cmd_format"
        
        if not cmd_format:
            raise ValueError(f"Command format not found: {operation_name} for {actual_program_name} (operation group: {dst_operation_group_name})")
        
        # 4. Replace parameters
        debug(f"Using command format: {cmd_format} (type: {format_type}, program: {actual_program_name})")
        cmdline = self._replace_parameters(cmd_format, params)
        
        debug(f"Command generation successful: {cmdline} (type: {format_type}, program: {actual_program_name})")
        return cmdline
    
    def get_final_command_format(self, operation_name: str, program_name: str) -> Optional[str]:
        """
        Get final command format (final_cmd_format)
        
        Args:
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            Optional[str]: final_cmd_format string, returns None if not exists
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        # Get final_cmd_format from cache
        program_formats = self.command_formats.get(program_name, {})
        final_format = program_formats.get(f"{operation_name}_final")  # Use suffix to distinguish
        
        debug(f"Getting final command format: {operation_name}.{program_name} -> {final_format}")
        return final_format

    def _replace_parameters(self, cmd_format: str, params: Dict[str, str]) -> str:
        """
        Replace parameter placeholders in command format
        
        Args:
            cmd_format: Command format string
            params: Parameter dictionary
            
        Returns:
            str: Command string after replacement
        """
        result = cmd_format
        
        for param_name, param_value in params.items():
            placeholder = "{" + param_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, param_value)
                debug(f"Replaced parameter: {placeholder} -> {param_value}")
            else:
                warning(f"Parameter placeholder {placeholder} not found in command format")
        
        # Check if there are any remaining unplaced placeholders
        import re
        remaining_placeholders = re.findall(r'\{(\w+)\}', result)
        if remaining_placeholders:
            warning(f"Command format still has unplaced placeholders: {remaining_placeholders}")
        
        return result

    def list_supported_operations(self, program_name: str) -> List[str]:
        """
        List all operations supported by program
        
        Args:
            program_name: Program name
            
        Returns:
            List[str]: List of supported operation names
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        supported_ops = []
        for op_name, programs in self.operation_to_program.items():
            if program_name in programs:
                supported_ops.append(op_name)
        
        debug(f"Program {program_name} supports {len(supported_ops)} operations: {supported_ops}")
        return sorted(supported_ops)

    def list_supported_programs(self, operation_name: str) -> List[str]:
        """
        List all programs supporting the operation
        
        Args:
            operation_name: Operation name
            
        Returns:
            List[str]: List of supported program names
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        programs = self.operation_to_program.get(operation_name, [])
        debug(f"Operation {operation_name} supports {len(programs)} programs: {programs}")
        return sorted(programs)

    def get_all_operations(self) -> List[str]:
        """
        Get all available operation names
        
        Returns:
            List[str]: List of all operation names
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        operations = list(self.operation_to_program.keys())
        debug(f"Total {len(operations)} available operations: {operations}")
        return sorted(operations)

    def get_all_programs(self) -> List[str]:
        """
        Get all available program names
        
        Returns:
            List[str]: List of all program names
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        programs = list(self.command_formats.keys())
        debug(f"Total {len(programs)} available programs: {programs}")
        return sorted(programs)

    def is_operation_supported(self, operation_name: str, program_name: str) -> bool:
        """
        Check if operation supports specified program
        
        Args:
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            bool: Whether supported
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        supported = program_name in self.operation_to_program.get(operation_name, [])
        debug(f"Operation {operation_name} supports program {program_name}: {supported}")
        return supported

    def get_command_format(self, operation_name: str, program_name: str) -> Optional[str]:
        """
        Get command format for specified operation and program
        
        Args:
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            Optional[str]: Command format string, returns None if not exists
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        program_formats = self.command_formats.get(program_name, {})
        cmd_format = program_formats.get(operation_name)
        debug(f"Getting command format: {operation_name}.{program_name} -> {cmd_format}")
        return cmd_format

    def reload(self) -> None:
        """
        Reload operation mapping configuration
        
        Used to refresh in-memory mapping data after configuration updates
        """
        debug("Reloading operation mapping...")
        self.operation_to_program.clear()
        self.command_formats.clear()
        self._loaded = False  # Reset loading status
        self._ensure_loaded()  # Reload
        debug("Operation mapping reload completed")

    def get_operation_parameters(self, operation_name: str, program_name: str) -> List[str]:
        """
        Get operation parameter list
        
        Args:
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            List[str]: Parameter name list
        """
        # Ensure operation mapping is loaded
        self._ensure_loaded()
        
        program_formats = self.command_formats.get(program_name, {})
        cmd_format = program_formats.get(operation_name)
        
        if not cmd_format:
            return []
        
        # Extract parameters from command format
        import re
        params = re.findall(r'\{(\w+)\}', cmd_format)
        return params


# Convenience functions
def create_operation_mapping() -> OperationMapping:
    """
    Create operation mapper instance
    
    Returns:
        OperationMapping: Operation mapper instance
    """
    return OperationMapping()


def generate_command_from_operation(operation_name: str, params: Dict[str, str],
                                  dst_operation_domain_name: str,
                                  dst_operation_group_name: str) -> str:
    """
    Convenience function: Generate command directly from operation
    
    Args:
        operation_name: Operation name
        params: Parameter dictionary
        dst_operation_domain_name: Target domain name
        dst_operation_group_name: Target program name
        
    Returns:
        str: Generated command line string
    """
    mapping = OperationMapping()
    return mapping.generate_command(operation_name, params, 
                                  dst_operation_domain_name, dst_operation_group_name)