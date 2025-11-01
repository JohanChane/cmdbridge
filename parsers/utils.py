from typing import List
from .types import CommandNode, CommandArg
from log import debug

class Utils:
    @staticmethod
    def print_command_tree(node: CommandNode, level: int = 0):
        """Print command tree structure (for debugging)"""
        indent = "  " * level
        debug(f"{indent}└── {node.name}")
        
        # Print current node's arguments
        for arg in node.arguments:
            arg_info = Utils._format_command_arg(arg)
            debug(f"{indent}    ├── {arg_info}")
        
        # Recursively print subcommands
        if node.subcommand:
            Utils.print_command_tree(node.subcommand, level + 1)

    @staticmethod
    def _format_command_arg(arg: CommandArg) -> str:
        """Format CommandArg into readable string"""
        parts = []
        
        # Argument type
        parts.append(f"type={arg.node_type.value}")
        
        # Option name (if any)
        if arg.option_name:
            parts.append(f"option='{arg.option_name}'")
        
        # Values (if any)
        if arg.values:
            parts.append(f"values={arg.values}")
        
        # Repeat count (if flag)
        if arg.repeat and arg.repeat > 1:
            parts.append(f"repeat={arg.repeat}")
        
        # Placeholder marker (if any)
        if hasattr(arg, 'is_placeholder') and arg.is_placeholder:
            parts.append("placeholder=True")
        
        return f"CommandArg({', '.join(parts)})"

    @staticmethod
    def normalize_command_line(args: List[str]) -> List[str]:
        """
        Preprocess command line, unify styles
        
        Processing rules:
        1. Decompose combined short options: -zxvf -> -z -x -v -f
        2. Separate equals form: --config=bar -> --config bar
        3. Do not process strings after -- separator
        4. Keep other arguments unchanged
        
        Args:
            args: Original command line argument list
            
        Returns:
            List[str]: Normalized command line argument list
        """
        if not args:
            return []
        
        normalized_args = []
        found_separator = False  # Whether separator has been found
        
        for arg in args:
            if not arg:
                continue
                
            if arg == "--":
                # Separator, everything after this is not processed
                normalized_args.append(arg)
                found_separator = True
                debug(f"Found separator '--', subsequent arguments will not be processed")
                continue
            
            if found_separator:
                # All arguments after separator remain unchanged
                normalized_args.append(arg)
                debug(f"After separator, keep as is: {arg}")
                continue
                
            if arg.startswith("--") and "=" in arg:
                # Handle equals form for long options: --config=bar -> --config bar
                opt_name, opt_value = arg.split("=", 1)
                normalized_args.append(opt_name)
                normalized_args.append(opt_value)
                debug(f"Separated equals form: {arg} -> {opt_name} {opt_value}")
                
            elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
                # Handle combined short options: -zxvf -> -z -x -v -f
                # Don't rely on configuration, directly decompose all characters
                decomposed = Utils._decompose_short_options(arg)
                normalized_args.extend(decomposed)
                debug(f"Decomposed combined short options: {arg} -> {decomposed}")
                
            else:
                # Other cases remain unchanged
                normalized_args.append(arg)
                debug(f"Keep as is: {arg}")
        
        return normalized_args
    
    @staticmethod
    def _decompose_short_options(combined_option: str) -> List[str]:
        """
        Decompose combined short options
        
        Args:
            combined_option: Combined short option, e.g., "-zxvf"
            
        Returns:
            List[str]: Decomposed option list, e.g., ["-z", "-x", "-v", "-f"]
        """
        if len(combined_option) <= 2:
            return [combined_option]
        
        # Extract option characters (remove leading "-")
        option_chars = combined_option[1:]
        decomposed = []
        
        # Simple decomposition: all characters as independent flags
        # In actual usage, options that accept arguments usually don't appear in the middle of combined options
        # For example: -f in tar -zxvf file.tar.gz should appear separately at the end
        for char in option_chars:
            decomposed.append(f"-{char}")
        
        debug(f"Decomposed combined short options: {combined_option} -> {decomposed}")
        return decomposed