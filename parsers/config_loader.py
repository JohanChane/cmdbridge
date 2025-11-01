"""
Configuration Loader - Load program parser configurations from TOML configuration data
Supports id and include_arguments_and_subcmds features, uses preprocessing to resolve dependencies
"""

from typing import Dict, Any, Optional, List
import tomli
from .types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig


class ConfigLoader:
    """Configuration loader"""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize configuration loader
        
        Args:
            config_data: TOML parsed configuration data
        """
        self.config_data = config_data
        self._id_templates = {}  # Store subcommand templates with ids (preprocessed)
    
    def load_parser_config(self, program_name: str) -> ParserConfig:
        """
        Load parser configuration for specified program
        
        Args:
            program_name: Program name
            
        Returns:
            ParserConfig: Parser configuration object
            
        Raises:
            ValueError: Configuration format error
        """
        return self._parse_config_data(program_name, self.config_data)
    
    def _parse_config_data(self, program_name: str, config_data: dict) -> ParserConfig:
        """Parse configuration data into ParserConfig object"""
        # Check if program configuration exists
        if program_name not in config_data:
            raise ValueError(f"Missing {program_name} section in configuration file")
        
        program_config = config_data[program_name]
        
        # Get parser configuration section
        if "parser_config" not in program_config:
            raise ValueError(f"Missing {program_name}.parser_config section in configuration file")
        
        parser_section = program_config["parser_config"]
        
        # Parse parser type
        parser_type_str = parser_section.get("parser_type")
        if not parser_type_str:
            parser_type_str = "argparse"    # default parser
        
        try:
            parser_type = ParserType(parser_type_str)
        except ValueError:
            raise ValueError(f"Unsupported parser type: {parser_type_str}")
        
        # Parse program name
        config_program_name = parser_section.get("program_name", program_name)
        
        # Step 1: Collect all subcommand nodes with ids
        self._collect_id_templates(program_config)
        
        # Step 2: Preprocess id subcommand nodes, recursively parse include_arguments_and_subcmds
        self._preprocess_id_templates()
        
        # Parse global arguments
        arguments = []
        if "arguments" in program_config:
            arguments = self._parse_arguments(program_config["arguments"])
        
        # Step 3: Parse subcommands, handle include_arguments_and_subcmds
        sub_commands = []
        if "sub_commands" in program_config:
            sub_commands = self._parse_sub_commands(program_config["sub_commands"])
        
        return ParserConfig(
            parser_type=parser_type,
            program_name=config_program_name,
            arguments=arguments,
            sub_commands=sub_commands
        )
    
    def _collect_id_templates(self, program_config: dict):
        """Step 1: Collect all subcommand nodes with ids"""
        if "sub_commands" not in program_config:
            return
        
        def collect_recursive(sub_commands_data: list):
            for sub_cmd_data in sub_commands_data:
                if "id" in sub_cmd_data:
                    template_id = sub_cmd_data["id"]
                    # Deep copy original data
                    self._id_templates[template_id] = sub_cmd_data.copy()
                
                # Recursively collect nested subcommands
                if "sub_commands" in sub_cmd_data:
                    collect_recursive(sub_cmd_data["sub_commands"])
        
        collect_recursive(program_config["sub_commands"])
    
    def _preprocess_id_templates(self):
        """Step 2: Preprocess id subcommand nodes, recursively parse include_arguments_and_subcmds"""
        processed = set()
        
        def preprocess_template(template_id: str):
            if template_id in processed:
                return
            
            template_data = self._id_templates[template_id]
            
            # If template has include_arguments, recursively process
            if "include_arguments_and_subcmds" in template_data:
                referenced_id = template_data["include_arguments_and_subcmds"]
                
                # Ensure referenced template is preprocessed
                if referenced_id in self._id_templates:
                    preprocess_template(referenced_id)
                    
                    # Copy referenced template content
                    referenced_template = self._id_templates[referenced_id]
                    
                    # Copy arguments
                    if "arguments" in referenced_template:
                        template_data["arguments"] = referenced_template["arguments"].copy()
                    
                    # Copy sub_commands
                    if "sub_commands" in referenced_template:
                        template_data["sub_commands"] = referenced_template["sub_commands"].copy()
                    
                    # Copy description (if exists)
                    if "description" in referenced_template:
                        template_data["description"] = referenced_template["description"]
                
                # Remove include_arguments, mark as processed
                template_data.pop("include_arguments_and_subcmds", None)
            
            processed.add(template_id)
        
        # Preprocess all templates
        for template_id in list(self._id_templates.keys()):
            preprocess_template(template_id)
    
    def _parse_arguments(self, arguments_data: list) -> list[ArgumentConfig]:
        """Parse argument configuration list"""
        arguments = []
        
        for arg_data in arguments_data:
            # Parse nargs
            nargs_str = arg_data.get("nargs")
            if not nargs_str:
                raise ValueError("Missing nargs in argument configuration")
            
            # Create ArgumentCount (will automatically validate nargs string)
            nargs = ArgumentCount(nargs_str)
            
            # Parse required (optional, default false)
            required = arg_data.get("required", False)
            
            argument = ArgumentConfig(
                name=arg_data.get("name", ""),
                opt=arg_data.get("opt", []),
                nargs=nargs,
                required=required,
                description=arg_data.get("description")
            )
            arguments.append(argument)
        
        return arguments
    
    def _parse_sub_commands(self, sub_commands_data: list) -> list[SubCommandConfig]:
        """Step 3: Parse subcommands, handle include_arguments_and_subcmds"""
        sub_commands = []
        
        for sub_cmd_data in sub_commands_data:
            sub_command = self._parse_single_sub_command(sub_cmd_data)
            sub_commands.append(sub_command)
        
        return sub_commands

    def _parse_single_sub_command(self, sub_cmd_data: dict) -> SubCommandConfig:
        """Parse single subcommand configuration"""
        # Get final configuration data
        final_data = self._get_final_sub_command_data(sub_cmd_data)
        
        # Create base object
        sub_command = SubCommandConfig(
            name=final_data["name"],
            alias=final_data.get("alias", []),
            arguments=[],
            sub_commands=[],
            description=final_data.get("description")
        )
        
        # Replace fields that need parsing
        sub_command.arguments = self._parse_arguments(final_data.get("arguments", []))
        sub_command.sub_commands = self._parse_sub_commands(final_data.get("sub_commands", []))
        
        return sub_command

    def _get_final_sub_command_data(self, sub_cmd_data: dict) -> dict:
        """Get final subcommand configuration data (handle template references)"""
        if "include_arguments_and_subcmds" not in sub_cmd_data:
            return sub_cmd_data
        
        template_id = sub_cmd_data["include_arguments_and_subcmds"]
        if template_id not in self._id_templates:
            raise ValueError(f"Template not found: {template_id}")
        
        # Merge configurations
        template_data = self._id_templates[template_id].copy()
        final_data = {**template_data, **sub_cmd_data}
        
        # Clean up template-specific fields
        final_data.pop("id", None)
        final_data.pop("include_arguments_and_subcmds", None)
        
        return final_data


# Convenience functions
def load_parser_config_from_data(config_data: Dict[str, Any], program_name: str) -> ParserConfig:
    """
    Convenience function: Load parser configuration for specified program from configuration data
    
    Args:
        config_data: TOML parsed configuration data
        program_name: Program name
        
    Returns:
        ParserConfig: Parser configuration object
    """
    loader = ConfigLoader(config_data)
    return loader.load_parser_config(program_name)


def load_parser_config_from_file(config_file: str, program_name: str) -> ParserConfig:
    """
    Convenience function: Load parser configuration for specified program from configuration file
    
    Args:
        config_file: Configuration file path
        program_name: Program name
        
    Returns:
        ParserConfig: Parser configuration object
    """
    with open(config_file, 'rb') as f:
        config_data = tomli.load(f)
    
    return load_parser_config_from_data(config_data, program_name)