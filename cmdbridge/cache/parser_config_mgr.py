import tomli
import tomli_w
from typing import Dict, Any
from pathlib import Path

from parsers.config_loader import load_parser_config_from_file
from parsers.types import ParserConfig
from log import debug, info, warning, error
from ..config.path_manager import PathManager


class ParserConfigCacheMgr:
    """Parser Configuration Cache Manager"""
    
    def __init__(self):
        self.path_manager = PathManager.get_instance()
    
    def generate_parser_config_cache(self):
        """Generate preprocessed parameter configuration cache for all programs"""
        source_dir = self.path_manager.program_parser_config_dir
        cache_dir = self.path_manager.get_parser_config_dir_of_cache()
        
        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        for config_file in source_dir.glob("*.toml"):
            program_name = config_file.stem
            try:
                # Use ConfigLoader to load and preprocess configuration
                parser_config = load_parser_config_from_file(str(config_file), program_name)
                
                # Use object's serialization method
                serialized_data = parser_config.to_dict()
                
                # Store to cache directory
                cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
                with open(cache_file, 'wb') as f:
                    tomli_w.dump(serialized_data, f)
                    
                info(f"✅ Generated parser configuration cache for {program_name}")
                
            except Exception as e:
                error(f"❌ Failed to generate parser configuration cache for {program_name}: {e}")
                raise
    
    def load_from_cache(self, program_name: str) -> ParserConfig:
        """Load preprocessed ParserConfig object from cache"""
        cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
        
        if not cache_file.exists():
            raise ValueError(f"Parser configuration cache for {program_name} not found, please run 'cache refresh' first")
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = tomli.load(f)
            
            # Use class's deserialization method
            return ParserConfig.from_dict(cached_data)
            
        except Exception as e:
            error(f"Failed to load parser configuration cache for {program_name}: {e}")
            raise
    
    def cache_exists(self, program_name: str) -> bool:
        """Check if parser configuration cache exists for specified program"""
        cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
        return cache_file.exists()