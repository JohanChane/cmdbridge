import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from log import debug, info, warning, error


class ConfigPathMgr:
    """Configuration Path Manager - Specifically manages configuration-related paths"""
    
    def __init__(self, base_config_dir: Path):
        """Initialize configuration path manager"""
        self._base_config_dir = base_config_dir
        self._program_parser_config_dir = base_config_dir / "program_parser_configs"
    
    def get_program_parser_path(self, program_name: str) -> Path:
        """Get program parser configuration file path"""
        return self._program_parser_config_dir / f"{program_name}.toml"
    
    def get_domain_base_path(self, domain_name: str) -> Path:
        """Get domain base configuration file path"""
        return self._base_config_dir / f"{domain_name}.domain.base.toml"
    
    def get_operation_domain_dir(self, domain_name: str) -> Path:
        """Get operation group file path in configuration directory"""
        return self._base_config_dir / f"{domain_name}.domain"
    
    def get_operation_group_path(self, domain_name: str, group_name: str) -> Path:
        """Get configuration file path for specific operation group"""
        return self.get_operation_domain_dir(domain_name) / f"{group_name}.toml"


class CachePathMgr:
    """Cache Path Manager - Specifically manages cache-related paths"""

    def __init__(self, base_cache_dir: Path):
        """Initialize cache path manager"""
        self._base_cache_dir = base_cache_dir
    
    def _operation_to_program_domain_dir(self, domain_name: str) -> Path:
        """Get operation group file path in cache directory"""
        return self._base_cache_dir / f"{domain_name}.domain"
    
    def get_operation_to_program_path(self, domain_name: str) -> Path:
        """Get operation to program mapping file path"""
        return self.get_operation_mappings_domain_dir(domain_name) / "operation_to_program.toml"
    
    def get_cmd_mappings_domain_dir(self, domain_name) -> Path:
        return self._base_cache_dir / "cmd_mappings" / f"{domain_name}.domain"
    
    def get_cmd_mappings_group_dir(self, domain_name: str, group_name: str) -> Path:
        """Get command mapping group directory path"""
        return self.get_cmd_mappings_domain_dir(domain_name) / group_name
    
    def get_cmd_mappings_group_program_path(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """Get command file path for specific program in command mapping group"""
        return self.get_cmd_mappings_group_dir(domain_name, group_name) / f"{program_name}_command.toml"
    
    def get_cmd_to_operation_path(self, domain_name: str) -> Path:
        """Get command to operation mapping file path"""
        return self.get_cmd_mappings_domain_dir(domain_name) / "cmd_to_operation.toml"
    
    def get_operation_mappings_domain_dir(self, domain_name) -> Path:
        return self._base_cache_dir / "operation_mappings" / f"{domain_name}.domain"
    
    def get_operation_mappings_group_dir(self, domain_name: str, group_name: str) -> Path:
        """Get operation mapping group directory path"""
        return self.get_operation_mappings_domain_dir(domain_name) / group_name
    
    def get_operation_mappings_group_program_path(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """Get command file path for specific program in operation mapping group"""
        return self.get_operation_mappings_group_dir(domain_name, group_name) / f"{program_name}_commands.toml"
    
    def get_operation_mappings_group_path(self, domain_name: str, group_name: str) -> Path:
        """Get operation mapping cache file path (compatibility method)"""
        return self.get_operation_mappings_domain_dir(domain_name) / f"{group_name}.toml"

    def get_parser_config_dir(self) -> Path:
        """Get parser configuration cache directory"""
        return self._base_cache_dir / "program_parser_configs"
    
    def get_parser_config_path(self, program_name: str) -> Path:
        """Get parser configuration cache file path for specified program"""
        return self.get_parser_config_dir() / f"{program_name}.toml"

class PathManager:
    """Path Manager - Unified management of configuration and cache directory paths (singleton pattern)"""
    
    _instance = None
    
    def __new__(cls, config_dir: Optional[str] = None, 
                cache_dir: Optional[str] = None,
                program_parser_config_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_dir: Optional[str] = None, 
                 cache_dir: Optional[str] = None,
                 program_parser_config_dir: Optional[str] = None):
        """
        Initialize path manager
        
        Args:
            config_dir: Configuration directory path, if None use default path
            cache_dir: Cache directory path, if None use default path
            program_parser_config_dir: Program parser configuration directory path, if None base on config_dir
        """
        if self._initialized:
            return
            
        # Set default paths
        self._config_dir = Path(
            config_dir or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        ) / "cmdbridge"
        
        self._cache_dir = Path(
            cache_dir or os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        ) / "cmdbridge"
        
        # Initialize internal path managers
        self._config_path_mgr = ConfigPathMgr(self._config_dir)
        self._cache_path_mgr = CachePathMgr(self._cache_dir)

        # Program parser configuration directory
        if program_parser_config_dir:
            self._program_parser_config_dir = Path(program_parser_config_dir)
        else:
            self._program_parser_config_dir = self._config_dir / "program_parser_configs"
        
        # Ensure directories exist
        self._ensure_directories()
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'PathManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (mainly for testing)"""
        cls._instance = None
    
    # Property accessors
    @property
    def config_dir(self) -> Path:
        """Get configuration directory path"""
        return self._config_dir
    
    @property
    def cache_dir(self) -> Path:
        """Get cache directory path"""
        return self._cache_dir
    
    @property
    def program_parser_config_dir(self) -> Path:
        """Get program parser configuration directory path"""
        return self._program_parser_config_dir
    
    def _ensure_directories(self) -> None:
        """Ensure necessary directories exist"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._program_parser_config_dir.mkdir(parents=True, exist_ok=True)

    def ensure_cache_directories(self, domain_name: str) -> None:
        """Ensure cache directory structure exists"""
        # Ensure command mapping directory exists
        cmd_mappings_dir = self._cache_dir / "cmd_mappings" / domain_name
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure domain cache directory exists
        domain_cache_dir = self._cache_dir / "domains" / f"{domain_name}.domain"
        domain_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_package_dir(self) -> Path:
        """
        Get package directory path
        
        Returns:
            Path: Package directory path
        """
        return Path(__file__).parent.parent.parent
    
    def get_default_configs_dir(self) -> Path:
        """
        Get default configuration directory path within package
        
        Returns:
            Path: Default configuration directory path
        """
        return self.get_package_dir() / "configs"
    
    def get_global_config_path(self) -> Path:
        """Get global configuration file path"""
        return self._config_dir / "config.toml"
    
    def get_program_parser_path_of_config(self, program_name: str) -> Path:
        """Get program parser configuration file path"""
        return self._config_path_mgr.get_program_parser_path(program_name)
    
    def get_domain_base_path_of_config(self, domain_name: str) -> Path:
        """Get domain base configuration file path"""
        return self._config_path_mgr.get_domain_base_path(domain_name)
    
    def get_operation_domain_dir_of_config(self, domain_name: str) -> Path:
        """Get configuration file path for specific operation group"""
        return self._config_path_mgr.get_operation_domain_dir(domain_name)
        
    def get_operation_group_path_of_config(self, domain_name: str, group_name: str) -> Path:
        """Get configuration file path for specific operation group"""
        return self._config_path_mgr.get_operation_group_path(domain_name, group_name)
    
    def get_parser_config_dir_of_cache(self) -> Path:
        """Get parser configuration cache directory"""
        return self._cache_path_mgr.get_parser_config_dir()
    
    def get_parser_config_path_of_cache(self, program_name: str) -> Path:
        """Get parser configuration cache file path for specified program"""
        return self._cache_path_mgr.get_parser_config_path(program_name)
    
    def get_operation_mappings_domain_dir_of_cache(self, domain_name: str) -> Path:
        """Get operation mapping cache file path"""
        return self._cache_path_mgr.get_operation_mappings_domain_dir(domain_name)
    
    def get_cmd_mappings_domain_dir_of_cache(self, domain_name: str) -> Path:
        """Get command mapping domain directory path"""
        return self._cache_path_mgr.get_cmd_mappings_domain_dir(domain_name)
    
    def get_cmd_mappings_domain_of_cache(self, domain_name: str) -> Path:
        """Get command mapping cache file path"""
        return self._cache_path_mgr.get_cmd_mappings_domain_dir(domain_name)
    
    def get_operation_to_program_path(self, domain_name: str) -> Path:
        """Get operation to program mapping file path"""
        return self._cache_path_mgr.get_operation_to_program_path(domain_name)
    
    def get_operation_mappings_group_dir_of_cache(self, domain_name: str, group_name: str) -> Path:
        """Get operation mapping group directory path"""
        return self._cache_path_mgr.get_operation_mappings_group_dir(domain_name, group_name)
    
    def get_operation_mappings_group_program_path_of_cache(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """Get command file path for specific program in operation mapping group"""
        return self._cache_path_mgr.get_operation_mappings_group_program_path(domain_name, group_name, program_name)
    
    def get_cmd_mappings_group_dir_of_cache(self, domain_name: str, group_name: str) -> Path:
        """Get command mapping group directory path"""
        return self._cache_path_mgr.get_cmd_mappings_group_dir(domain_name, group_name)
    
    def get_cmd_mappings_group_program_path_of_cache(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """Get command file path for specific program in command mapping group"""
        return self._cache_path_mgr.get_cmd_mappings_group_program_path(domain_name, group_name, program_name)
    
    def get_cmd_to_operation_path(self, domain_name: str) -> Path:
        """Get command to operation mapping file path"""
        return self._cache_path_mgr.get_cmd_to_operation_path(domain_name)
    
    def ensure_cmd_mappings_group_dir(self, domain_name: str, group_name: str) -> None:
        """Ensure command mapping group directory exists"""
        group_dir = self.get_cmd_mappings_group_dir_of_cache(domain_name, group_name)
        group_dir.mkdir(parents=True, exist_ok=True)

    def ensure_operation_mappings_group_dir(self, domain_name: str, group_name: str) -> None:
        """Ensure operation mapping group directory exists"""
        group_dir = self.get_operation_mappings_group_dir_of_cache(domain_name, group_name)
        group_dir.mkdir(parents=True, exist_ok=True)

    def ensure_cmd_mappings_domain_dir(self, domain_name: str) -> None:
        """Ensure command mapping domain directory exists"""
        cmd_mappings_dir = self.get_cmd_mappings_domain_dir_of_cache(domain_name)
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
    
    def domain_exists(self, domain_name: str) -> bool:
        """Check if domain exists"""
        domain_path = self.get_operation_domain_dir_of_config(domain_name)
        return domain_path.exists() and domain_path.is_dir()
    
    def operation_group_exists(self, domain_name: str, group_name: str) -> bool:
        """Check if operation group exists"""
        config_path = self.get_operation_group_path_of_config(domain_name, group_name)
        return config_path.exists()
    
    def program_parser_config_exists(self, program_name: str) -> bool:
        """Check if program parser configuration exists"""
        config_path = self.get_program_parser_path_of_config(program_name)
        return config_path.exists()
    
    def domain_base_config_exists(self, domain_name: str) -> bool:
        """Check if domain base configuration file exists"""
        return self.get_domain_base_path_of_config(domain_name).exists()

    def rm_cmd_mappings_dir(self, domain_name: Optional[str] = None) -> bool:
        """Delete command mapping directory"""
        try:
            if domain_name is None:
                # Delete all command mapping directories
                cmd_mappings_dir = self._cache_dir / "cmd_mappings"
                if cmd_mappings_dir.exists():
                    shutil.rmtree(cmd_mappings_dir)
                    debug(f"Deleted all command mapping directories: {cmd_mappings_dir}")
                return True
            else:
                # Delete command mapping directory for specified domain
                domain_cmd_mappings_dir = self.get_cmd_mappings_domain_dir_of_cache(domain_name)
                if domain_cmd_mappings_dir.exists():
                    shutil.rmtree(domain_cmd_mappings_dir)
                    debug(f"Deleted command mapping directory for {domain_name} domain: {domain_cmd_mappings_dir}")
                return True
        except Exception as e:
            error(f"Failed to delete command mapping directory: {e}")
            return False

    def rm_operation_mappings_dir(self, domain_name: Optional[str] = None) -> bool:
        """Delete operation mapping directory"""
        try:
            if domain_name is None:
                # Delete all operation mapping directories
                operation_mappings_dir = self._cache_dir / "operation_mappings"
                if operation_mappings_dir.exists():
                    shutil.rmtree(operation_mappings_dir)
                    debug(f"Deleted all operation mapping directories: {operation_mappings_dir}")
                return True
            else:
                # Delete operation mapping directory for specified domain
                domain_operation_mappings_dir = self.get_operation_mappings_domain_dir_of_cache(domain_name)
                if domain_operation_mappings_dir.exists():
                    shutil.rmtree(domain_operation_mappings_dir)
                    debug(f"Deleted operation mapping directory for {domain_name} domain: {domain_operation_mappings_dir}")
                return True
        except Exception as e:
            error(f"Failed to delete operation mapping directory: {e}")
            return False

    def rm_program_parser_config_dir(self) -> bool:
        """Delete program parser configuration cache directory"""
        try:
            parser_config_dir = self.get_parser_config_dir_of_cache()
            if parser_config_dir.exists():
                shutil.rmtree(parser_config_dir)
                debug(f"Deleted program parser configuration cache directory: {parser_config_dir}")
            return True
        except Exception as e:
            error(f"Failed to delete program parser configuration cache directory: {e}")
            return False

    def rm_all_cache_dirs(self) -> bool:
        """Delete all cache directories"""
        try:
            success1 = self.rm_cmd_mappings_dir()
            success2 = self.rm_operation_mappings_dir()
            success3 = self.rm_program_parser_config_dir()
            return success1 and success2 and success3
        except Exception as e:
            error(f"Failed to delete all cache directories: {e}")
            return False
        
    def get_domains_from_config(self) -> List[str]:
        """
        List all available domain names
        
        Returns:
            List[str]: Domain name list, e.g., ["package", "process"]
        """
        domains = []
        
        if not self._config_dir.exists():
            return domains
        
        # Find all *.domain directories
        for item in self._config_dir.iterdir():
            if item.is_dir() and item.name.endswith('.domain'):
                domain_name = item.name[:-7]  # Remove .domain suffix
                domains.append(domain_name)
        
        return sorted(domains)
    
    def get_operation_groups_from_config(self, domain_name: str) -> List[str]:
        """
        List all operation group names in specified domain
        
        Args:
            domain_name: Domain name
            
        Returns:
            List[str]: Operation group name list, e.g., ["apt", "pacman", "brew"]
        """
        groups = []
        domain_dir = self.get_operation_domain_dir_of_config(domain_name)
        
        if not domain_dir.exists():
            return groups
        
        # Find all .toml configuration files (exclude base.toml)
        for config_file in domain_dir.glob("*.toml"):
            group_name = config_file.stem
            groups.append(group_name)
        
        return sorted(groups)
    
    def get_all_operation_groups_from_config(self) -> List[str]:
        """
        List all operation group names in all domains
        
        Returns:
            List[str]: All operation group name list
        """
        all_groups = []
        domains = self.get_domains_from_config()
        
        for domain in domains:
            domain_groups = self.get_operation_groups_from_config(domain)
            all_groups.extend(domain_groups)
        
        return sorted(list(set(all_groups)))  # Deduplicate and sort
    
    def get_programs_from_parser_configs(self) -> List[str]:
        """
        List all available program parser configurations
        
        Returns:
            List[str]: Program name list, e.g., ["apt", "pacman", "apt-file"]
        """
        programs = []
        
        if not self._program_parser_config_dir.exists():
            return programs
        
        # Find all .toml configuration files
        for config_file in self._program_parser_config_dir.glob("*.toml"):
            program_name = config_file.stem
            programs.append(program_name)
        
        return sorted(programs)
    
    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        """Get domain for program group based on group name"""
        try:
            domains = self.get_domains_from_config()
            
            for domain in domains:
                groups = self.get_operation_groups_from_config(domain)
                if group_name in groups:
                    return domain
            return None
        except Exception:
            return None