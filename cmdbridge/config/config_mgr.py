import os, sys
from pathlib import Path
from typing import List, Dict, Any, Optional
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli
import shutil

from cmdbridge.config.path_manager import PathManager
from log import debug, info, warning, error


class ConfigMgr:
    """Configuration utility class - Manages configuration and cache directories, contains all functionality implementation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigMgr, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialize configuration utility
        """
        if self._initialized:
            return
            
        # Directly use PathManager singleton
        self.path_manager = PathManager.get_instance()
        debug("Initializing ConfigMgr")
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'ConfigMgr':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (mainly for testing)"""
        cls._instance = None
    
    def init_config(self) -> bool:
        """Initialize user configuration"""
        try:
            # Get default configuration path within package
            default_configs_dir = self.path_manager.get_default_configs_dir()
            
            # Check if default configuration exists
            if not default_configs_dir.exists():
                error(f"Default configuration directory does not exist: {default_configs_dir}")
                return False
            
            info(f"Initializing configuration directory: {self.path_manager.config_dir}")
            info(f"Initializing cache directory: {self.path_manager.cache_dir}")
            
            # Copy domain base files
            base_files = list(default_configs_dir.glob("*.domain.base.toml"))
            if base_files:
                info("Copying domain base files...")
                for base_file in base_files:
                    dest_file = self.path_manager.config_dir / base_file.name
                    if dest_file.exists():
                        info(f"  Skipping existing: {base_file.name}")
                    else:
                        shutil.copy2(base_file, dest_file)
                        info(f"  Copied: {base_file.name}")
            else:
                warning("No domain base files found")
            
            # Copy domain configuration directories
            domain_dirs = list(default_configs_dir.glob("*.domain"))
            if domain_dirs:
                info("Copying domain configuration directories...")
                for domain_dir in domain_dirs:
                    # Check if it's a directory (exclude .domain.base.toml files)
                    if domain_dir.is_dir():
                        dest_domain_dir = self.path_manager.get_operation_domain_dir_of_config(domain_dir.stem)
                        if dest_domain_dir.exists():
                            info(f"  Skipping existing: {domain_dir.name}")
                        else:
                            shutil.copytree(domain_dir, dest_domain_dir)
                            info(f"  Copied: {domain_dir.name}")
            else:
                warning("No domain configuration directories found")
            
            # Copy program_parser_configs
            parser_configs_dir = default_configs_dir / "program_parser_configs"
            if parser_configs_dir.exists():
                dest_parser_dir = self.path_manager.program_parser_config_dir
                
                # Ensure target directory exists
                dest_parser_dir.mkdir(parents=True, exist_ok=True)
                
                info(f"Copying parser configurations from {parser_configs_dir} to {dest_parser_dir}")
                
                # Copy all .toml files
                config_files = list(parser_configs_dir.glob("*.toml"))
                if config_files:
                    copied_count = 0
                    for config_file in config_files:
                        dest_file = dest_parser_dir / config_file.name
                        if not dest_file.exists():
                            shutil.copy2(config_file, dest_file)
                            info(f"  Copied: {config_file.name}")
                            copied_count += 1
                        else:
                            info(f"  Skipping existing: {config_file.name}")
                    
                    info(f"Parser configuration copy completed: {copied_count} files")
                else:
                    warning(f"No .toml files found in source directory: {parser_configs_dir}")
            else:
                error(f"Source parser configuration directory does not exist: {parser_configs_dir}")
                return False
            
            # Copy config.toml
            default_config_file = default_configs_dir / "config.toml"
            if default_config_file.exists():
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    shutil.copy2(default_config_file, dest_config_file)
                    info("  Copied: config.toml")
                else:
                    info("  Skipping existing: config.toml")
            else:
                # Create default config.toml
                default_config = """[global_settings]"""
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    with open(dest_config_file, 'w') as f:
                        f.write(default_config)
                    info("  Created default: config.toml")
            
            # Copy README
            readme_files = list(default_configs_dir.glob("README*"))
            if readme_files:
                info("Copying README files...")
                for readme_file in readme_files:
                    dest_readme_file = self.path_manager.config_dir / readme_file.name
                    if not dest_readme_file.exists():
                        shutil.copy2(readme_file, dest_readme_file)
                        info(f"  Copied: {readme_file.name}")
                    else:
                        info(f"  Skipping existing: {readme_file.name}")
            else:
                info("No README files found, skipping copy")

            return True
        except Exception as e:
            error(f"Configuration initialization failed: {e}")
            return False