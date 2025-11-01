"""
Cache Manager - Unified management of command mapping and operation mapping cache data
"""

import os
import tomli
from typing import List, Dict, Any, Optional
from pathlib import Path
from log import debug, info, warning, error
from ..config.path_manager import PathManager


class CacheMgr:
    """Cache Manager - Provides unified cache data access interface"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheMgr, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize cache manager"""
        if self._initialized:
            return
            
        self.path_manager = PathManager.get_instance()
        self._cache_data = {}
        self._loaded_domains = set()
        self._initialized = True
        
        debug("Initializing CacheMgr")
    
    @classmethod
    def get_instance(cls) -> 'CacheMgr':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (mainly for testing)"""
        cls._instance = None
    
    def get_domains(self) -> List[str]:
        """
        Get all available domain names
        
        Returns:
            List[str]: Domain name list
        """
        return self.path_manager.get_domains_from_config()
    
    def get_operation_groups(self, domain: str) -> List[str]:
        """
        Get all operation group names for specified domain
        
        Args:
            domain: Domain name
            
        Returns:
            List[str]: Operation group name list
        """
        return self.path_manager.get_operation_groups_from_config(domain)
    
    def get_all_operation_groups(self, domain: Optional[str] = None) -> List[str]:
        """
        Get all operation group names
        
        Args:
            domain: Optional, specify domain name
            
        Returns:
            List[str]: Operation group name list
        """
        if domain:
            return self.get_operation_groups(domain)
        else:
            return self.path_manager.get_all_operation_groups_from_config()
    
    def get_cmd_mappings(self, domain: str, group_name: str) -> Dict[str, Any]:
        """
        Get command mapping configuration for specified domain and program group
        
        Args:
            domain: Domain name
            group_name: Program group name
            
        Returns:
            Dict[str, Any]: Command mapping configuration data
        """
        cache_key = f"{domain}.{group_name}"
        
        if cache_key not in self._cache_data:
            try:
                # Get all programs for this operation group from cmd_to_operation.toml
                cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path(domain)
                if not cmd_to_operation_file.exists():
                    self._cache_data[cache_key] = {}
                    return self._cache_data[cache_key]
                
                with open(cmd_to_operation_file, 'rb') as f:
                    cmd_to_operation_data = tomli.load(f)
                
                # Get all programs for this operation group
                programs = cmd_to_operation_data.get("cmd_to_operation", {}).get(group_name, {}).get("programs", [])
                if not programs:
                    self._cache_data[cache_key] = {}
                    return self._cache_data[cache_key]
                
                # Load command mappings for all programs
                group_mappings = {}
                for program_name in programs:
                    program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
                        domain, group_name, program_name
                    )
                    if program_file.exists():
                        try:
                            with open(program_file, 'rb') as f:
                                program_data = tomli.load(f)
                            # Merge program data
                            group_mappings.update(program_data)
                        except Exception as e:
                            error(f"Failed to load program command file {program_file}: {e}")
                
                self._cache_data[cache_key] = group_mappings
                debug(f"Loaded command mapping cache: {cache_key}, containing programs: {programs}")
                
            except Exception as e:
                error(f"Failed to load command mapping cache: {e}")
                self._cache_data[cache_key] = {}
        
        return self._cache_data[cache_key]
    
    def get_operation_mappings(self, domain: str) -> Dict[str, Any]:
        """
        Get operation mapping configuration for specified domain
        
        Args:
            domain: Domain name
            
        Returns:
            Dict[str, Any]: Operation mapping configuration data
        """
        cache_key = f"operation_mappings.{domain}"
        
        if cache_key not in self._cache_data:
            # Load operation to program mapping
            op_to_program_file = self.path_manager.get_operation_to_program_path(domain)  # Use new path
            operation_to_program = {}
            
            if op_to_program_file.exists():
                try:
                    with open(op_to_program_file, 'rb') as f:
                        data = tomli.load(f)
                    operation_to_program = data.get("operation_to_program", {})
                    debug(f"Loaded operation to program mapping: {domain}")
                except Exception as e:
                    error(f"Failed to load operation to program mapping {op_to_program_file}: {e}")
            
            # Load command formats for all programs (new structure)
            command_formats = {}
            cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache(domain)
            
            # Traverse all operation group directories
            for group_dir in cache_dir.iterdir():
                if group_dir.is_dir():
                    group_name = group_dir.name
                    # Traverse all program command files in operation group directory
                    for command_file in group_dir.glob("*_commands.toml"):
                        program_name = command_file.stem.replace("_commands", "")
                        try:
                            with open(command_file, 'rb') as f:
                                data = tomli.load(f)
                            if program_name not in command_formats:
                                command_formats[program_name] = {}
                            command_formats[program_name].update(data.get("commands", {}))
                            debug(f"Loaded {group_name}/{program_name} command formats: {len(data.get('commands', {}))} commands")
                        except Exception as e:
                            error(f"Failed to load command format file {command_file}: {e}")
            
            self._cache_data[cache_key] = {
                "operation_to_program": operation_to_program,
                "command_formats": command_formats
            }
        
        return self._cache_data[cache_key]
    
    def get_operation_to_program_mapping(self, domain: str) -> Dict[str, List[str]]:
        """
        Get operation to program mapping relationship
        
        Args:
            domain: Domain name
            
        Returns:
            Dict[str, List[str]]: Mapping from operation name to supported program list
        """
        operation_mappings = self.get_operation_mappings(domain)
        return operation_mappings.get("operation_to_program", {})
    
    def get_command_formats(self, domain: str, program_name: str) -> Dict[str, str]:
        """
        Get command formats for specified program
        
        Args:
            domain: Domain name
            program_name: Program name
            
        Returns:
            Dict[str, str]: Mapping from operation name to command format
        """
        operation_mappings = self.get_operation_mappings(domain)
        command_formats = operation_mappings.get("command_formats", {})
        return command_formats.get(program_name, {})
    
    def get_supported_operations(self, domain: str, program_name: str) -> List[str]:
        """
        Get all operations supported by program
        
        Args:
            domain: Domain name
            program_name: Program name
            
        Returns:
            List[str]: Supported operation name list
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        supported_ops = []
        
        for op_name, programs in operation_to_program.items():
            if program_name in programs:
                supported_ops.append(op_name)
        
        return sorted(supported_ops)
    
    def get_supported_programs(self, domain: str, operation_name: str) -> List[str]:
        """
        Get all programs supporting the operation
        
        Args:
            domain: Domain name
            operation_name: Operation name
            
        Returns:
            List[str]: Supported program name list
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        return operation_to_program.get(operation_name, [])
    
    def is_operation_supported(self, domain: str, operation_name: str, program_name: str) -> bool:
        """
        Check if operation supports specified program
        
        Args:
            domain: Domain name
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            bool: Whether supported
        """
        supported_programs = self.get_supported_programs(domain, operation_name)
        return program_name in supported_programs
    
    def get_command_format(self, domain: str, operation_name: str, program_name: str) -> Optional[str]:
        """
        Get command format for specified operation and program
        
        Args:
            domain: Domain name
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            Optional[str]: Command format string, returns None if not exists
        """
        command_formats = self.get_command_formats(domain, program_name)
        return command_formats.get(operation_name)
    
    def get_final_command_format(self, domain: str, operation_name: str, program_name: str) -> Optional[str]:
        """
        Get final command format (final_cmd_format)
        
        Args:
            domain: Domain name
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            Optional[str]: final_cmd_format string, returns None if not exists
        """
        command_formats = self.get_command_formats(domain, program_name)
        return command_formats.get(f"{operation_name}_final")
    
    def get_all_operations(self, domain: str) -> List[str]:
        """
        Get all available operation names
        
        Args:
            domain: Domain name
            
        Returns:
            List[str]: All operation name list
        """
        operation_to_program = self.get_operation_to_program_mapping(domain)
        return sorted(list(operation_to_program.keys()))
    
    def get_all_programs(self, domain: str) -> List[str]:
        """
        Get all available program names
        
        Args:
            domain: Domain name
            
        Returns:
            List[str]: All program name list
        """
        operation_mappings = self.get_operation_mappings(domain)
        command_formats = operation_mappings.get("command_formats", {})
        return sorted(list(command_formats.keys()))
    
    def get_operation_parameters(self, domain: str, operation_name: str, program_name: str) -> List[str]:
        """
        Get operation parameter list
        
        Args:
            domain: Domain name
            operation_name: Operation name
            program_name: Program name
            
        Returns:
            List[str]: Parameter name list
        """
        cmd_format = self.get_command_format(domain, operation_name, program_name)
        if not cmd_format:
            return []
        
        # Extract parameters from command format
        import re
        params = re.findall(r'\{(\w+)\}', cmd_format)
        return params
    
    def refresh_cache(self, domain: Optional[str] = None) -> bool:
        """
        Refresh cache data
        
        Args:
            domain: Optional, specify domain name, if None refresh all domains
            
        Returns:
            bool: Whether refresh succeeded
        """
        try:
            if domain:
                # Refresh cache for specified domain
                if domain in self._cache_data:
                    del self._cache_data[domain]
                if f"operation_mappings.{domain}" in self._cache_data:
                    del self._cache_data[f"operation_mappings.{domain}"]
                debug(f"Refreshed cache for domain: {domain}")
            else:
                # Refresh all cache
                self._cache_data.clear()
                debug("Refreshed all cache data")
            
            return True
        except Exception as e:
            error(f"Failed to refresh cache: {e}")
            return False
    
    def cache_exists(self, domain: str, cache_type: str = "cmd_mappings") -> bool:
        """
        Check if cache exists
        
        Args:
            domain: Domain name
            cache_type: Cache type, 'cmd_mappings' or 'operation_mappings'
            
        Returns:
            bool: Whether cache exists
        """
        if cache_type == "cmd_mappings":
            # Check if any command mapping cache files exist
            cache_dir = self.path_manager.get_cmd_mappings_domain_of_cache(domain)
            return cache_dir.exists() and any(cache_dir.glob("*.toml"))
        elif cache_type == "operation_mappings":
            # Check operation mapping cache file
            cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache(domain)
            op_to_program_file = cache_dir / "operation_to_program.toml"
            return op_to_program_file.exists()
        else:
            return False
    
    def get_cache_stats(self, domain: str) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Args:
            domain: Domain name
            
        Returns:
            Dict[str, Any]: Cache statistics
        """
        stats = {
            "domain": domain,
            "cmd_mappings_exists": self.cache_exists(domain, "cmd_mappings"),
            "operation_mappings_exists": self.cache_exists(domain, "operation_mappings"),
            "operation_groups": [],
            "operations_count": 0,
            "programs_count": 0
        }
        
        if self.cache_exists(domain, "cmd_mappings"):
            groups = self.get_operation_groups(domain)
            stats["operation_groups"] = groups
            stats["groups_count"] = len(groups)
        
        if self.cache_exists(domain, "operation_mappings"):
            operations = self.get_all_operations(domain)
            programs = self.get_all_programs(domain)
            stats["operations_count"] = len(operations)
            stats["programs_count"] = len(programs)
        
        return stats

    def remove_cmd_mapping(self, domain_name: str = None) -> bool:
        """Refresh command mapping cache (compatibility method)"""
        return self.path_manager.rm_cmd_mappings_dir(domain_name)

    def remove_operation_mapping(self, domain_name: str = None) -> bool:
        """Delete operation mapping cache"""
        return self.path_manager.rm_operation_mappings_dir(domain_name)

    def remove_parser_config_cache(self) -> bool:
        """Delete parser configuration cache"""
        return self.path_manager.rm_program_parser_config_dir()

    def remove_all_cache(self) -> bool:
        """Delete all cache"""
        return self.path_manager.rm_all_cache_dirs()
    
    def merge_all_domain_configs(self) -> bool:
        """Merge all domain configurations
        
        Generate operation_mapping.toml file for each domain
        
        Returns:
            bool: Whether merge succeeded
        """
        try:
            domains = self.path_manager.get_domains_from_config()
            success_count = 0
            
            for domain in domains:
                domain_config_dir = self.path_manager.get_operation_domain_dir_of_config(domain)
                if domain_config_dir.exists():
                    # Here call generation method in CmdBridge
                    # In actual implementation, may need to move generation logic to ConfigUtils
                    debug(f"Processing domain configuration: {domain}")
                    success_count += 1
                else:
                    warning(f"Domain configuration directory does not exist: {domain_config_dir}")
            
            debug(f"Merged {success_count}/{len(domains)} domain configurations")
            return success_count > 0
            
        except Exception as e:
            error(f"Failed to merge domain configurations: {e}")
            return False