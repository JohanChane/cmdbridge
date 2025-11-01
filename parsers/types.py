from enum import Enum
from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass, field


# === Argument Configuration ===
# Parser type
class ParserType(Enum):
    GETOPT = "getopt"
    ARGPARSE = "argparse"

# Argument configuration
@dataclass
class ArgumentCount:
    """Argument count specification"""
    spec: str  # argparse-style nargs specification
    
    def __init__(self, spec: str):
        """Initialize argument count specification"""
        # Validate nargs string
        valid_specs = {'?', '*', '+', '0'}
        if (spec not in valid_specs and 
            not spec.isdigit() and 
            not self._is_valid_range(spec)):
            raise ValueError(f"Unsupported nargs value: {spec}. Supported formats: ?, *, +, 0, numbers, or number ranges")
        
        self.spec = spec
    
    def _is_valid_range(self, spec: str) -> bool:
        """Check if it's a valid number range format, e.g., '1..3'"""
        if '..' in spec:
            parts = spec.split('..')
            if len(parts) == 2:
                return parts[0].isdigit() and (parts[1].isdigit() or parts[1] == '')
        return False
    
    def __str__(self) -> str:
        return self.spec
    
    def is_flag(self) -> bool:
        """Check if it's a flag argument (no parameters)"""
        return self.spec == '0'
    
    def validate_count(self, actual_count: int) -> bool:
        """Validate if actual argument count meets requirements"""
        if self.spec == '?':
            return actual_count <= 1
        elif self.spec == '*':
            return True  # Any number
        elif self.spec == '+':
            return actual_count >= 1
        elif self.spec.isdigit():
            return actual_count == int(self.spec)
        elif self.spec == '0':
            return actual_count == 0
        elif '..' in self.spec:
            # Handle range format, e.g., '1..3' or '1..'
            parts = self.spec.split('..')
            min_count = int(parts[0])
            max_count = int(parts[1]) if parts[1].isdigit() else None
            
            if actual_count < min_count:
                return False
            if max_count is not None and actual_count > max_count:
                return False
            return True
        else:
            # Default case, argparse default is 1
            return actual_count == 1
    
    def is_required(self) -> bool:
        """Check if it's a required parameter based on nargs"""
        # Only nargs='+' or numbers > 0 are required
        return self.spec == '+' or (self.spec.isdigit() and int(self.spec) > 0)
    
    def get_exact_count(self) -> Optional[int]:
        if self.spec not in ["?", "*", "+"]:
            return int(self.spec)
        return None
    
# Common presets
ArgumentCount.ZERO = ArgumentCount('0')           # No arguments (flag)
ArgumentCount.ZERO_OR_ONE = ArgumentCount('?')    # Optional argument
ArgumentCount.ZERO_OR_MORE = ArgumentCount('*')   # Zero or more
ArgumentCount.ONE_OR_MORE = ArgumentCount('+')    # One or more

# Argument configuration
@dataclass
class ArgumentConfig:
    """Argument configuration"""
    name: str                    # Argument name
    opt: List[str]              # Option name list (e.g., ["-h", "--help"])
    nargs: ArgumentCount        # Argument count specification
    required: bool = False      # Whether it's a required argument
    description: Optional[str] = None  # Argument description
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            "name": self.name,
            "opt": self.opt,
            "nargs": str(self.nargs),
            "required": self.required,
        }
        # Only include non-None description
        if self.description is not None:
            result["description"] = self.description
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArgumentConfig':
        """Deserialize from dictionary"""
        return cls(
            name=data["name"],
            opt=data["opt"],
            nargs=ArgumentCount(data["nargs"]),
            required=data.get("required", False),
            description=data.get("description")  # Allow None
        )

    def is_flag(self) -> bool:
        """Check if it's a flag argument"""
        return self.nargs.is_flag()
        
    def is_positional(self) -> bool:
        """Check if it's a positional argument"""
        if not self.opt:
            return True
        
        # Get valid options (non-empty strings)
        valid_options = [opt for opt in self.opt if opt and opt.strip()]
        return len(valid_options) == 0

    def is_option(self) -> bool:
        """Check if it's an option argument"""
        if self.is_flag():
            return False
        
        # Get valid options (non-empty strings)
        valid_options = [opt for opt in self.opt if opt and opt.strip()]
        return len(valid_options) > 0
    
    def accepts_values(self) -> bool:
        """Check if it accepts values"""
        return not self.is_flag()
    
    def get_expected_count(self) -> ArgumentCount:
        """Get expected argument count"""
        return self.nargs

    def validate_count(self, actual_count: int) -> bool:
        """Validate if actual argument count meets requirements"""
        return self.nargs.validate_count(actual_count)
    
    def is_required(self) -> bool:
        """Check if it's a required argument"""
        return self.required
    
    def matches_option(self, option_name: str) -> bool:
        """Check if option name matches this configuration"""
        # Skip empty strings, only match actual option names
        for opt in self.opt:
            if opt and opt == option_name:
                return True
        return False
    
    def get_primary_option_name(self) -> Optional[str]:
        """Get primary option name

        Selection rules:
        1. Prefer long argument names (options containing '--')
        2. If no long argument names, return short argument name (containing '-') (if multiple, return first)
        3. If no valid option names, return None

        Returns:
            Optional[str]: Primary option name
        """
        # 1. Find and return first long argument name (starting with '--')
        for opt in self.opt:
            if opt and opt.startswith('--') and opt.strip():
                return opt

        # 2. Find and return first short argument name (starting with '-')
        for opt in self.opt:
            if opt and opt.startswith('-') and not opt.startswith('--') and opt.strip():
                return opt

        # 3. If no valid option names found, return None
        return None

@dataclass
class SubCommandConfig:
    """Subcommand configuration"""
    name: str                                           # Subcommand name
    alias: List[str] = field(default_factory=list)      # Subcommand aliases. e.g., `brew list/ls -v pkg`
    arguments: List[ArgumentConfig] = field(default_factory=list)  # Subcommand arguments
    sub_commands: List['SubCommandConfig'] = field(default_factory=list)  # Nested subcommands
    description: Optional[str] = None      # Subcommand description
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            "name": self.name,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "sub_commands": [sub_cmd.to_dict() for sub_cmd in self.sub_commands],
        }

        # Only include non-empty alias
        if self.alias:
            result["alias"] = self.alias

        # Only include non-None description
        if self.description is not None:
            result["description"] = self.description
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubCommandConfig':
        """Deserialize from dictionary"""
        return cls(
            name=data["name"],
            alias=data.get("alias", []),
            arguments=[ArgumentConfig.from_dict(arg_data) for arg_data in data["arguments"]],
            sub_commands=[SubCommandConfig.from_dict(sub_cmd_data) for sub_cmd_data in data["sub_commands"]],
            description=data.get("description")  # Allow None
        )
    
    def find_argument(self, option_name: str) -> Optional[ArgumentConfig]:
        """Find argument configuration by option name"""
        for arg in self.arguments:
            if arg.matches_option(option_name):
                return arg
        return None

    def get_positional_arg_config(self) -> Optional[ArgumentConfig]:
        for arg in self.arguments:
            if arg.is_positional():
                return arg
        return None

    def matches_subcmd_name(self, subcmd_name: str) -> bool:
        """Check if subcommand name matches (including aliases)"""
        if subcmd_name == self.name:
            return True
        
        if subcmd_name in self.alias:
            return True
        
        return False

@dataclass
class ParserConfig:
    """Parser configuration"""
    parser_type: ParserType                # Parser type
    program_name: str                      # Program name
    arguments: List[ArgumentConfig] = field(default_factory=list)  # Global arguments
    sub_commands: List[SubCommandConfig] = field(default_factory=list)  # Subcommands
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "parser_type": self.parser_type.value,
            "program_name": self.program_name,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "sub_commands": [sub_cmd.to_dict() for sub_cmd in self.sub_commands]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParserConfig':
        """Deserialize from dictionary"""
        parser_type_str = data.get("parser_type")
        if parser_type_str:
            parser_type = ParserType(parser_type_str)
        else:
            parser_type = ParserType.ARGPARSE
        
        return cls(
            parser_type=parser_type,
            program_name=data.get("program_name", ""),  # Required field but provide default value
            arguments=[ArgumentConfig.from_dict(arg_data) for arg_data in data.get("arguments", [])],
            sub_commands=[SubCommandConfig.from_dict(sub_cmd_data) for sub_cmd_data in data.get("sub_commands", [])]
        )
    
    def find_argument(self, opt_name: str) -> Optional[ArgumentConfig]:
        """Find argument configuration by option name"""
        for arg in self.arguments:
            if arg.matches_option(opt_name):
                return arg
        return None
    
    def find_subcommand(self, name: str) -> Optional[SubCommandConfig]:
        """Find subcommand configuration by name"""
        for sub_cmd in self.sub_commands:
            if sub_cmd.name == name:
                return sub_cmd
        return None
    
    def get_positional_arguments(self) -> List[ArgumentConfig]:
        """Get all positional arguments"""
        return [arg for arg in self.arguments if arg.is_positional()]

# === CommandToken ===
class TokenType(Enum):
    """Command line token types"""
    PROGRAM = "program"                 # Program name (e.g., git, pacman, apt)
    SUBCOMMAND = "subcommand"           # Subcommand name (e.g., commit, install, search)
    POSITIONAL_ARG = "positional_arg"   # Positional argument (non-option)
    OPTION_NAME = "option_name"         # Option name (-o/--output)
    OPTION_VALUE = "option_value"       # Option value
    FLAG = "flag"                       # Boolean flag
    SEPARATOR = "separator"             # Separator (--)
    EXTRA_ARG = "extra_arg"             # Arguments after separator

@dataclass
class CommandToken:
    """Command line token
    
    Represents a syntactic node in command line parsing.
    
    Attributes:
        token_type: Type of token, defined in TokenType enum
        values: List of values for this token
        original_text: Original command line string for debugging,
                      auto-generated from values if not provided
    """
    token_type: TokenType
    values: List[str]
    original_text: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.original_text is None and self.values:
            self.original_text = " ".join(self.values)
    
    def __str__(self) -> str:
        """String representation of the token"""
        return f"CommandToken(type={self.token_type.value}, values={self.values}, original='{self.original_text}')"
    
    def is_program(self) -> bool:
        """Check if this is a program token"""
        return self.token_type == TokenType.PROGRAM
    
    def is_subcommand(self) -> bool:
        """Check if this is a subcommand token"""
        return self.token_type == TokenType.SUBCOMMAND
    
    def is_flag(self) -> bool:
        """Check if this is a flag token"""
        return self.token_type == TokenType.FLAG
    
    def is_option_name(self) -> bool:
        return self.token_type == TokenType.OPTION_NAME
    
    def is_option_value(self) -> bool:
        return self.token_type == TokenType.OPTION_VALUE

    def is_positional_arg(self) -> bool:
        return  self.token_type == TokenType.POSITIONAL_ARG

    def is_separator(self) -> bool:
        return  self.token_type == TokenType.SEPARATOR
    
    def is_extra_arg(self) -> bool:
        return  self.token_type == TokenType.EXTRA_ARG
    
    def get_first_value(self) -> Optional[str]:
        """Get the first value if exists"""
        return self.values[0] if self.values else None
    
    def get_joined_values(self, separator: str = " ") -> str:
        """Join all values with separator into a single string"""
        return separator.join(self.values)
    
    def set_option_name(self, arg_config: ArgumentConfig):
        self.values = [arg_config.get_primary_option_name()]

# === Command Tree ===
class ArgType(Enum):
    """Command tree node types"""
    POSITIONAL = "positional"
    OPTION = "option"
    FLAG = "flag"
    EXTRA = "extra"

@dataclass
class CommandArg:
    """Command argument in tree structure"""
    node_type: ArgType
    option_name: Optional[str] = None   # flag values go here
    values: List[str] = field(default_factory=list)
    repeat: Optional[int] = None
    placeholder: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            "node_type": self.node_type.value,
            "values": self.values.copy(),
        }
        
        # Only include non-None fields
        if self.option_name is not None:
            result["option_name"] = self.option_name
        if self.repeat is not None:
            result["repeat"] = self.repeat
        if self.placeholder is not None:
            result["placeholder"] = self.placeholder
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandArg':
        """Deserialize from dictionary"""
        return cls(
            node_type=ArgType(data["node_type"]),
            option_name=data.get("option_name"),
            values=data.get("values", []),
            repeat=data.get("repeat"),
            placeholder=data.get("placeholder")  # Deserialize placeholder
        )

@dataclass
class CommandNode:
    """Command tree node - tree structure where subcommands create child nodes"""
    name: str
    arguments: List[CommandArg] = field(default_factory=list)  # Arguments for current node
    subcommand: Optional['CommandNode'] = None                # Subcommand node (tree expansion)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            "name": self.name,
            "arguments": [arg.to_dict() for arg in self.arguments],
        }
        
        # Only include non-None subcommand
        if self.subcommand is not None:
            result["subcommand"] = self.subcommand.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandNode':
        """Deserialize from dictionary"""
        arguments = [CommandArg.from_dict(arg_data) for arg_data in data.get("arguments", [])]
        
        node = cls(
            name=data["name"],
            arguments=arguments
        )
        
        # Recursively deserialize subcommand
        if "subcommand" in data and data["subcommand"] is not None:
            node.subcommand = cls.from_dict(data["subcommand"])
            
        return node