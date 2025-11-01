import os
import tomli
import tomli_w
from typing import Dict, List, Any, Optional
from pathlib import Path

from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType, ArgumentConfig
from parsers.config_loader import load_parser_config_from_file
from parsers.factory import ParserFactory

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class CmdMappingMgr:
    """Command Mapping Creator - Generates separate command mapping files for each program"""
    
    def __init__(self, domain_name: str, group_name: str):
        """
        Initialize command mapping creator
        
        Args:
            domain_name: Domain name (e.g., "package", "process")
            group_name: Operation group name (e.g., "apt", "pacman")
        """
        # Use singleton PathManager
        self.path_manager = PathManager.get_instance()
        self.domain_name = domain_name
        self.group_name = group_name
        self.program_mappings = {}  # Mapping data organized by program
        self.cmd_to_operation_data = {}  # cmd_to_operation data
    
    def create_mappings(self) -> Dict[str, Any]:
        debug(f"=== Starting processing operation group: {self.domain_name}.{self.group_name} ===")
        
        # Get operation group configuration file path
        group_file = self.path_manager.get_operation_group_path_of_config(self.domain_name, self.group_name)
        debug(f"Operation group configuration file: {group_file}")
        debug(f"Configuration file exists: {group_file.exists()}")
        
        if not group_file.exists():
            error(f"Operation group configuration file does not exist: {group_file}")
            raise FileNotFoundError(f"Operation group configuration file does not exist: {group_file}")
        
        # Process single operation group file
        self._process_group_file(group_file)
        
        debug(f"Program mappings after processing: {self.program_mappings}")
        
        # Generate cmd_to_operation data
        self._generate_cmd_to_operation_data()
        
        debug(f"Generated cmd_to_operation data: {self.cmd_to_operation_data}")
        debug(f"=== Completed processing operation group: {self.domain_name}.{self.group_name} ===\n")
        
        return {
            "program_mappings": self.program_mappings,
            "cmd_to_operation": self.cmd_to_operation_data
        }
    
    def _process_group_file(self, operation_group_file: Path):
        """Process single operation group file"""
        
        # Load operation file content
        try:
            with open(operation_group_file, 'rb') as f:
                group_data = tomli.load(f)
        except (tomli.TOMLDecodeError, Exception) as e:
            warning(f"Cannot parse operation file {operation_group_file}: {e}")
            return
    
        debug(f"Processing operation group: {self.group_name}")
        
        # Process all operations
        if "operations" in group_data:
            for operation_key, operation_config in group_data["operations"].items():
                debug(f"Processing operation key: {operation_key}")
                self._process_operation(operation_key, operation_config)
        else:
            debug(f"No operations section in file {operation_group_file}")
    
    def _process_operation(self, operation_key: str, operation_config: Dict[str, Any]):
        """Process single operation"""
        if "cmd_format" not in operation_config:
            warning(f"Operation {operation_key} missing cmd_format, skipping")
            return
        
        cmd_format = operation_config["cmd_format"]
        final_cmd_format = operation_config.get("final_cmd_format")
        
        # Preprocessing: Remove quotes around parameters
        import re
        original_cmd_format = cmd_format
        cmd_format = re.sub(r"""['"]\{(\w+)\}['"]""", r'{\1}', cmd_format)
        
        debug(f"Command format preprocessing: '{original_cmd_format}' -> '{cmd_format}'")
        
        # Extract operation_name from operation_key
        operation_parts = operation_key.split('.')
        if len(operation_parts) > 1 and operation_parts[-1] == self.group_name:
            operation_name = '.'.join(operation_parts[:-1])
        else:
            operation_name = operation_key
        
        debug(f"Extracted operation name: {operation_name}")
        
        # Extract actual program name from command format
        actual_program_name = self._extract_program_from_cmd_format(cmd_format)
        if not actual_program_name:
            actual_program_name = self.group_name  # Fallback to operation group name
        
        debug(f"Operation {operation_name} uses program: {actual_program_name}")
        
        # Generate example command and parse to get CommandNode
        cmd_node = self._parse_command_and_map_params(cmd_format, actual_program_name)
        if not cmd_node:
            error(f"Cannot parse command: {cmd_format}")
            return
        
        # Create mapping entry
        mapping_entry = {
            "operation": operation_name,
            "cmd_format": cmd_format,
            "cmd_node": self._serialize_command_node(cmd_node)
        }
        
        # Add final_cmd_format (if exists)
        if final_cmd_format:
            mapping_entry["final_cmd_format"] = final_cmd_format
        
        # Organize mapping data by program name
        if actual_program_name not in self.program_mappings:
            self.program_mappings[actual_program_name] = {"command_mappings": []}
        
        self.program_mappings[actual_program_name]["command_mappings"].append(mapping_entry)
        debug(f"Created mapping for program {actual_program_name}: {operation_name}")

    def _extract_program_from_cmd_format(self, cmd_format: str) -> Optional[str]:
        """Extract program name from command format"""
        parts = cmd_format.strip().split()
        if parts:
            program_name = parts[0]
            debug(f"Extracted program name from command format '{cmd_format}': {program_name}")
            return program_name
        return None

    def _generate_cmd_to_operation_data(self):
        """Generate cmd_to_operation data"""
        # Collect all programs used by this operation group
        programs = list(self.program_mappings.keys())
        if programs:
            self.cmd_to_operation_data[self.group_name] = {
                "programs": programs
            }
            debug(f"Operation group {self.group_name} uses programs: {programs}")

    def _parse_command_and_map_params(self, cmd_format: str, program_name: str) -> Optional[CommandNode]:
        """Parse command and set placeholders"""
        debug(f"Parsing command: '{cmd_format}', program: {program_name}")
        
        # Load parser configuration
        from .parser_config_mgr import ParserConfigCacheMgr
        parser_cache_mgr = ParserConfigCacheMgr()
        parser_config = parser_cache_mgr.load_from_cache(program_name)
        if not parser_config:
            error(f"Cannot load parser configuration for program '{program_name}'")
            return None
        
        # Generate example command
        example_command = self._generate_example_command(cmd_format, parser_config)
        
        # Parse command to get CommandNode
        cmd_node = self._parse_command(parser_config, example_command)
        if not cmd_node:
            return None
        
        # Set placeholder markers
        self._set_placeholder_markers(cmd_node, cmd_format)
        
        return cmd_node
    
    def _set_placeholder_markers(self, cmd_node: CommandNode, cmd_format: str):
        """Set placeholder markers in CommandNode"""
        import re
        
        # Extract all parameter names from cmd_format
        param_names = re.findall(r'\{(\w+)\}', cmd_format)
        if not param_names:
            return
        
        # Create mapping from parameter names to placeholders
        param_mapping = {}
        for param_name in param_names:
            # For each parameter name, create corresponding placeholder pattern
            placeholder_pattern = re.compile(rf'__param_{param_name}(?:_\d+)?__')
            param_mapping[param_name] = placeholder_pattern
        
        # Recursively traverse CommandNode to set placeholders
        def set_placeholders(node: CommandNode):
            for arg in node.arguments:
                # Check if argument values contain placeholders
                for value in arg.values:
                    # Use parameter mapping to match placeholders
                    for param_name, pattern in param_mapping.items():
                        if pattern.match(value):
                            arg.placeholder = param_name  # Use parameter name from command format
                            debug(f"Set placeholder for parameter {param_name}")
                            break  # One CommandArg only needs to be set once
                    else:
                        continue
                    break
                
            if node.subcommand:
                set_placeholders(node.subcommand)
        
        set_placeholders(cmd_node)

    def _generate_example_command(self, cmd_format: str, parser_config: ParserConfig) -> List[str]:
        """Generate example command for cmd_format"""
        parts = cmd_format.split()
        example_parts = []
        
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                # Parameter placeholder
                param_name = part[1:-1]
                example_values = self._generate_param_example_values(param_name, parser_config)
                example_parts.extend(example_values)
            else:
                example_parts.append(part)
        
        debug(f"Generated example command: {example_parts}")
        return example_parts
    
    def _generate_param_example_values(self, param_name: str, parser_config: ParserConfig) -> List[str]:
        """Generate example values for parameters (with placeholder markers)"""
        # Use unique placeholder format
        PLACEHOLDER_PREFIX = "__param_"
        PLACEHOLDER_SUFFIX = "__"
        
        # Find parameter configuration
        arg_config = self._find_param_config(param_name, parser_config)
        if arg_config:
            # Generate corresponding number of example values based on nargs
            if arg_config.nargs.spec == '+' or arg_config.nargs.spec == '*':
                # For multi-value parameters, use same parameter name (without numeric suffix)
                # This keeps parameter names consistent with placeholders in command format
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}",
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"  # Same parameter name
                ]
            elif arg_config.nargs.spec.isdigit():
                # Fixed number of parameters
                count = int(arg_config.nargs.spec)
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}" 
                    for _ in range(count)  # Same parameter name
                ]
            else:
                # Default to generating 1 example value
                return [f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"]
        else:
            # No configuration found, default to generating 1 example value
            return [f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"]
    
    def _find_param_config(self, param_name: str, parser_config: ParserConfig) -> Optional[ArgumentConfig]:
        """Find configuration based on parameter name"""
        # Search in global arguments
        for arg_config in parser_config.arguments:
            if arg_config.name == param_name:
                return arg_config
        
        # Search in subcommand arguments
        for sub_cmd in parser_config.sub_commands:
            for arg_config in sub_cmd.arguments:
                if arg_config.name == param_name:
                    return arg_config
        
        return None
    
    def _load_parser_config(self, program_name: str) -> Optional[ParserConfig]:
        """Load parser configuration"""
        # Use PathManager to get parser configuration file path
        parser_config_file = self.path_manager.get_program_parser_path_of_config(program_name)
        
        if not parser_config_file.exists():
            warning(f"Cannot find parser configuration for program {program_name}: {parser_config_file}")
            return None
        
        debug(f"Loading parser configuration: {parser_config_file}")
        try:
            return load_parser_config_from_file(str(parser_config_file), program_name)
        except Exception as e:
            error(f"Failed to load parser configuration: {e}")
            return None
    
    def _parse_command(self, parser_config: ParserConfig, command_parts: List[str]) -> Optional[CommandNode]:
        """Parse command to get CommandNode"""
        try:

            parser = ParserFactory.create_parser(parser_config)
            
            # Use complete command (including program name)
            return parser.parse(command_parts)
            
        except Exception as e:
            error(f"Failed to parse command: {e}")
            return None
    
    def _serialize_command_node(self, node: CommandNode) -> Dict[str, Any]:
        """Serialize CommandNode object"""
        return node.to_dict()

    def write_to(self) -> None:
        """
        Write mapping data to cache files
        """
        # Check if there is program mapping data
        if not self.program_mappings:
            warning(f"⚠️ {self.domain_name}.{self.group_name} has no program mapping data to write")
            return
        
        # Ensure operation group directory exists
        self.path_manager.ensure_cmd_mappings_group_dir(self.domain_name, self.group_name)
        
        # Generate separate command files for each program
        for program_name, program_data in self.program_mappings.items():
            program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
                self.domain_name, self.group_name, program_name
            )
            try:
                with open(program_file, 'wb') as f:
                    tomli_w.dump(program_data, f)
                info(f"✅ Generated {self.group_name}/{program_name}_command.toml file")
            except Exception as e:
                error(f"❌ Failed to write program command file {program_file}: {e}")
                raise
        
        # Generate cmd_to_operation.toml file (read → merge → write)
        if self.cmd_to_operation_data:
            cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path(self.domain_name)
            cmd_to_operation_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Read existing cmd_to_operation data (if exists)
                existing_data = {}
                if cmd_to_operation_file.exists():
                    with open(cmd_to_operation_file, 'rb') as f:
                        existing_data = tomli.load(f)
                
                # Merge data: keep existing, add or update current operation group data
                merged_data = existing_data.copy()
                merged_data.setdefault("cmd_to_operation", {})
                merged_data["cmd_to_operation"].update(self.cmd_to_operation_data)
                
                # Write merged data
                with open(cmd_to_operation_file, 'wb') as f:
                    tomli_w.dump(merged_data, f)
                info(f"✅ Updated cmd_to_operation.toml file, containing operation groups: {list(self.cmd_to_operation_data.keys())}")
                
            except Exception as e:
                error(f"❌ Failed to write cmd_to_operation file {cmd_to_operation_file}: {e}")
                raise

# Convenience functions
def create_cmd_mappings_for_group(domain_name: str, group_name: str) -> Dict[str, Any]:
    """
    Convenience function: Create command mappings for specified domain's operation group
    
    Args:
        domain_name: Domain name
        group_name: Operation group name
        
    Returns:
        Dict[str, Any]: Mapping data
    """
    creator = CmdMappingMgr(domain_name, group_name)
    mapping_data = creator.create_mappings()
    creator.write_to()
    return mapping_data

def create_cmd_mappings_for_domain(domain_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function: Create command mappings for all operation groups in specified domain
    
    Args:
        domain_name: Domain name
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping data for all operation groups
    """
    path_manager = PathManager.get_instance()
    groups = path_manager.get_operation_groups_from_config(domain_name)
    
    all_mappings = {}
    for group_name in groups:
        try:
            mapping_data = create_cmd_mappings_for_group(domain_name, group_name)
            all_mappings[group_name] = mapping_data
            info(f"✅ Created command mappings for {domain_name}.{group_name}")
        except Exception as e:
            error(f"❌ Failed to create command mappings for {domain_name}.{group_name}: {e}")
    
    return all_mappings

def create_cmd_mappings_for_all_domains() -> None:
    """
    Convenience function: Create command mappings for all operation groups in all domains
    """
    path_manager = PathManager.get_instance()
    domains = path_manager.get_domains_from_config()
    
    for domain in domains:
        create_cmd_mappings_for_domain(domain)