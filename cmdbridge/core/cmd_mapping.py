"""
Command Mapping Core Module - Operation Group Based Mapping System
"""

from typing import List, Dict, Any, Optional
from parsers.types import CommandNode, CommandArg, ArgType
from parsers.types import ParserConfig
from parsers.factory import ParserFactory
from ..config.path_manager import PathManager

from log import debug, info, warning, error
import tomli

class CmdMapping:
    """
    Command Mapper - Maps source commands to operations and parameters
    
    Input: 
      - source cmdline (string list, e.g., ["apt", "install", "vim"])
      - cmd_mapping configuration data (contains operation field)
      - dst_operation_group (program name, e.g., "apt")
    
    Output: 
      - {operation_name, params{pkgs:, path: }}
    """
    
    def __init__(self, mapping_config: Dict[str, Any]):
        """
        Initialize command mapper
        
        Args:
            mapping_config: Mapping configuration for a single program group
        """
        self.mapping_config = mapping_config
        self.source_parser_config = None

    @classmethod
    def load_from_cache(cls, domain_name: str, program_name: str) -> 'CmdMapping':
        """
        Load command mapping for specified program from cache (cross operation group lookup)
        
        Args:
            domain_name: Domain name
            program_name: Program name
            
        Returns:
            CmdMapping: Command mapper instance
        """
        path_manager = PathManager.get_instance()
        
        # Get program list from cmd_to_operation.toml
        cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain_name)
        
        if not cmd_to_operation_file.exists():
            debug(f"cmd_to_operation file does not exist: {cmd_to_operation_file}")
            return cls({})
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            debug(f"Cross operation group lookup for program: {program_name}")
            found_group = None
            
            # Find operation group containing this program across all operation groups
            for op_group, group_data in cmd_to_operation_data.get("cmd_to_operation", {}).items():
                if program_name in group_data.get("programs", []):
                    found_group = op_group
                    debug(f"Found program {program_name} in operation group {op_group}")
                    break
            
            if not found_group:
                debug(f"Program {program_name} not found in any operation group")
                return cls({})
            
            # Load command mapping for this program
            program_file = path_manager.get_cmd_mappings_group_program_path_of_cache(
                domain_name, found_group, program_name
            )
            
            if not program_file.exists():
                debug(f"Program mapping file does not exist: {program_file}")
                return cls({})
            
            with open(program_file, 'rb') as f:
                program_data = tomli.load(f)
            
            debug(f"Loaded command mapping for program {program_name} (from operation group {found_group})")
            debug(f"Program data: {program_data}")
            
            # Ensure correct data structure is returned
            # Program file structure is {"command_mappings": [...]}
            # But CmdMapping expects {program_name: {"command_mappings": [...]}}
            mapping_config = {
                program_name: program_data
            }
            
            return cls(mapping_config)
            
        except Exception as e:
            error(f"Failed to load cache file: {e}")
            return cls({})
        
    @classmethod
    def load_all_for_domain(cls, domain_name: str) -> Dict[str, 'CmdMapping']:
        """
        Load command mappings for all program groups in specified domain
        
        Args:
            domain_name: Domain name
            
        Returns:
            Dict[str, CmdMapping]: Dictionary mapping program group names to command mappers
        """
        path_manager = PathManager.get_instance()
        cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain_name)
        
        if not cmd_to_operation_file.exists():
            return {}
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            mappings = {}
            cmd_to_operation = cmd_to_operation_data.get("cmd_to_operation", {})
            
            for group_name in cmd_to_operation.keys():
                mappings[group_name] = cls.load_from_cache(domain_name, group_name)
            
            debug(f"Loaded {len(mappings)} program group mappings for {domain_name} domain")
            return mappings
            
        except Exception as e:
            error(f"Failed to load domain mappings: {e}")
            return {}

    def map_to_operation(self, source_cmdline: List[str], 
                        source_parser_config: ParserConfig,
                        dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """Map source command to operations and parameters of target operation group"""
        debug(f"Starting command mapping to operation group '{dst_operation_group}': {' '.join(source_cmdline)}")
        
        # 1. Parse source command
        source_parser = ParserFactory.create_parser(source_parser_config)
        source_node = source_parser.parse(source_cmdline)
        
        if not source_parser.validate(source_node):
            warning(f"Source command validation failed: {' '.join(source_cmdline)}")
            return None

        # 2. Find matching operation in mapping configuration
        matched_mapping = self._find_matching_mapping(source_node, dst_operation_group)
        if not matched_mapping:
            debug(f"No matching command mapping found in operation group '{dst_operation_group}'")
            return None
        
        # 3. Deserialize mapping node
        mapping_node = self._deserialize_command_node(matched_mapping["cmd_node"])
        
        # 4. Extract parameter values
        param_values = self._extract_parameter_values(source_node, mapping_node)
        
        # 5. Return operation and parameters
        result = {
            "operation_name": matched_mapping["operation"],
            "params": param_values
        }
        
        debug(f"Command mapping successful: {' '.join(source_cmdline)} -> {result}")
        return result

    def _normalize_option_name(self, option_name: Optional[str]) -> str:
        """Normalize option name, prioritize long argument names for short/long arguments"""
        if not option_name:
            return ""
        
        if not self.source_parser_config:
            return option_name
        
        # Find corresponding argument configuration in parser configuration
        arg_config = self.source_parser_config.find_argument(option_name)
        if not arg_config:
            return option_name
        
        primary_name = arg_config.get_primary_option_name()
        return primary_name or option_name
    
    def _find_matching_mapping(self, source_node: CommandNode, dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """
        Find matching command mapping
        
        Args:
            source_node: Parsed source command node
            dst_operation_group: Target operation group name
            
        Returns:
            Optional[Dict[str, Any]]: Matching mapping configuration, returns None if no match
        """
        program_name = source_node.name  # Source program name, e.g., "asp"
        debug(f"Looking for matching mapping in program {program_name}, target operation group: {dst_operation_group}")
        
        # Directly look up corresponding mapping configuration based on source program name
        if program_name not in self.mapping_config:
            debug(f"Program {program_name} not in mapping configuration")
            return None
        
        program_data = self.mapping_config[program_name]
        command_mappings = program_data.get("command_mappings", [])
        debug(f"Found {len(command_mappings)} possible mappings")
        
        for mapping in command_mappings:
            if self._is_command_match(source_node, mapping):
                debug(f"Found matching mapping: {mapping['operation']}")
                return mapping
        
        debug(f"No matching mapping found for program {program_name} in operation group {dst_operation_group}")
        return None
    
    def _is_command_match(self, source_node: CommandNode, mapping: Dict[str, Any]) -> bool:
        """
        Check if source command matches mapping configuration
        
        Matching rules:
        1. Same program name (already checked externally)
        2. Same command node structure (name, argument count, subcommand structure)
        3. Same argument structure (type, option name, repeat count)
        4. Ignore argument value content
        """
        # 1. Program name match (already checked in _find_matching_mapping)
        
        # 2. Deserialize CommandNode from mapping configuration
        mapping_node = self._deserialize_command_node(mapping["cmd_node"])
        
        # 3. Deep compare command node structures
        return self._compare_command_nodes_deep(source_node, mapping_node)
    
    def _compare_command_nodes_deep(self, node1: CommandNode, node2: CommandNode) -> bool:
        """Deep compare two command node structures"""
        # Compare node names
        if node1.name != node2.name:
            return False
        
        # Compare subcommand structure
        if (node1.subcommand is None) != (node2.subcommand is None):
            return False
        
        if node1.subcommand and node2.subcommand:
            # Recursively compare subcommands
            if not self._compare_command_nodes_deep(node1.subcommand, node2.subcommand):
                return False
        
        # Compare argument count
        if len(node1.arguments) != len(node2.arguments):
            return False
        
        # Compare arguments one by one
        for arg1, arg2 in zip(node1.arguments, node2.arguments):
            if not self._compare_command_args(arg1, arg2):
                debug(f"arg1 and arg2 are different. arg1: {arg1}, arg2: {arg2}")
                return False
        
        return True

    def _compare_command_args(self, arg1: CommandArg, arg2: CommandArg) -> bool:
        """Compare two CommandArgs"""
        # 1. Compare types
        if arg1.node_type != arg2.node_type:
            return False
        
        # 2. For Flag type, compare repeat count
        if arg1.node_type == ArgType.FLAG:
            if arg1.option_name != arg2.option_name:        # option_name must use unified name. ArgumentConfig.get_primary_option_name()
                return False
            if arg1.repeat != arg2.repeat:
                return False
            
        # 3. Compare option_name (for Option and Flag types)
        if arg1.node_type == ArgType.OPTION:
            if arg1.option_name != arg2.option_name:        # option_name must use unified name. ArgumentConfig.get_primary_option_name()
                return False
            if not arg1.placeholder and not arg2.placeholder:   # If either has placeholder field, ignore comparison
                if set(arg1.values) != set(arg2.values):
                    return False
        # 4. Compare positional value
        if arg1.node_type == ArgType.POSITIONAL:
            if not arg1.placeholder and not arg2.placeholder:   # If either has placeholder field, ignore comparison
                if set(arg1.values) != set(arg2.values):
                    return False
        
        return True
    
    def _extract_parameter_values(self, source_node: CommandNode, mapping_node: CommandNode) -> Dict[str, str]:
        """Extract parameter values from source command node"""
        param_values = {}
        
        # Recursively traverse nodes to extract parameters
        def extract_from_node(source_node: CommandNode, mapping_node: CommandNode):
            # Compare and extract parameters one by one
            for source_arg, mapping_arg in zip(source_node.arguments, mapping_node.arguments):
                if mapping_arg.placeholder:
                    # Extract parameter value
                    param_name = mapping_arg.placeholder
                    if source_arg.values:
                        param_values[param_name] = " ".join(source_arg.values)
                        debug(f"Extracted parameter {param_name} = '{param_values[param_name]}'")
            
            # Recursively process subcommands
            if source_node.subcommand and mapping_node.subcommand:
                extract_from_node(source_node.subcommand, mapping_node.subcommand)
        
        extract_from_node(source_node, mapping_node)
        debug(f"Parameter extraction completed: {param_values}")
        return param_values

    def _deserialize_command_node(self, serialized_node: Dict[str, Any]) -> CommandNode:
        """Deserialize CommandNode"""
        return CommandNode.from_dict(serialized_node)


# Convenience function
def create_cmd_mapping(mapping_config: Dict[str, Any]) -> CmdMapping:
    """
    Create command mapper instance
    
    Args:
        mapping_config: Mapping configuration data
        
    Returns:
        CmdMapping: Command mapper instance
    """
    return CmdMapping(mapping_config)