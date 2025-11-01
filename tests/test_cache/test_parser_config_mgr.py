#!/usr/bin/env python3
"""
Test parser configuration cache manager core functionality
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cmdbridge.cache.parser_config_mgr import ParserConfigCacheMgr
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType
import tomli_w
import tomli


def setup_test_parser_config():
    """Set up test parser configuration with separate config and cache directories"""
    # Create a parent temporary directory
    parent_temp_dir = tempfile.mkdtemp()
    
    # Create separate subdirectories for config and cache under the same parent
    config_temp_dir = Path(parent_temp_dir) / "config"
    cache_temp_dir = Path(parent_temp_dir) / "cache"
    
    config_temp_dir.mkdir(parents=True, exist_ok=True)
    cache_temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize PathManager with separate directories under same parent
    PathManager.reset_instance()
    path_manager = PathManager(
        config_dir=str(config_temp_dir),
        cache_dir=str(cache_temp_dir)
    )
    
    print(f"Test parent dir: {parent_temp_dir}")
    print(f"Test config dir: {config_temp_dir}")
    print(f"Test cache dir: {cache_temp_dir}")
    
    # Create program parser configuration directory
    parser_config_dir = path_manager.program_parser_config_dir
    parser_config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test parser configuration
    test_parser_config = {
        "test_program": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "test_program"
            },
            "arguments": [
                {
                    "name": "help",
                    "opt": ["-h", "--help"],
                    "nargs": "0"
                }
            ]
        }
    }
    
    # Write configuration file (in config directory)
    config_file = parser_config_dir / "test_program.toml"
    with open(config_file, 'wb') as f:
        tomli_w.dump(test_parser_config, f)
    
    return parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager


def test_cache_generation_and_loading():
    """Test cache generation and loading functionality"""
    print("=== Testing Cache Generation and Loading ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # Create cache manager
        cache_mgr = ParserConfigCacheMgr()
        
        # Generate cache (should create files in cache directory)
        cache_mgr.generate_parser_config_cache()
        
        # Verify cache directory structure was created
        cache_dir = path_manager.get_parser_config_dir_of_cache()
        assert cache_dir.exists(), "Cache directory should exist"
        assert str(cache_dir).startswith(str(cache_temp_dir)), "Cache directory should be in cache_temp_dir"
        
        # Load configuration from cache
        parser_config = cache_mgr.load_from_cache("test_program")
        
        # Verify loaded configuration object
        assert isinstance(parser_config, ParserConfig)
        assert parser_config.parser_type == ParserType.ARGPARSE
        assert parser_config.program_name == "test_program"
        assert len(parser_config.arguments) == 1
        
        print("✅ Cache generation and loading test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_cache_file_content():
    """Test cache file content"""
    print("\n=== Testing Cache File Content ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # Create cache manager
        cache_mgr = ParserConfigCacheMgr()
        
        # Generate cache
        cache_mgr.generate_parser_config_cache()
        
        # Verify cache file content
        cache_file = path_manager.get_parser_config_path_of_cache("test_program")
        assert cache_file.exists(), "Cache file should exist"
        
        # Verify cache file is in cache directory, not config directory
        assert str(cache_file).startswith(str(cache_temp_dir)), "Cache file should be in cache directory"
        assert not str(cache_file).startswith(str(config_temp_dir)), "Cache file should not be in config directory"
        
        with open(cache_file, 'rb') as f:
            cached_data = tomli.load(f)
        
        # Verify basic structure
        assert "parser_type" in cached_data
        assert "program_name" in cached_data
        assert "arguments" in cached_data
        
        print("✅ Cache file content test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_directory_separation():
    """Test that config and cache directories are properly separated"""
    print("\n=== Testing Directory Separation ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # Verify directories are different but under same parent
        assert config_temp_dir != cache_temp_dir, "Config and cache directories should be different"
        assert config_temp_dir.parent == cache_temp_dir.parent, "Config and cache should be under same parent"
        
        # Verify PathManager uses correct directories
        assert str(path_manager.config_dir) == str(config_temp_dir)
        assert str(path_manager.cache_dir) == str(cache_temp_dir)
        
        # Verify config files are in config directory
        config_file = path_manager.get_program_parser_path_of_config("test_program")
        assert str(config_file).startswith(str(config_temp_dir)), "Config files should be in config directory"
        
        # Verify cache files are in cache directory (after cache generation)
        cache_mgr = ParserConfigCacheMgr()
        cache_mgr.generate_parser_config_cache()
        
        cache_file = path_manager.get_parser_config_path_of_cache("test_program")
        assert str(cache_file).startswith(str(cache_temp_dir)), "Cache files should be in cache directory"
        
        print("✅ Directory separation test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_cache_exists_check():
    """Test cache existence checking"""
    print("\n=== Testing Cache Existence Check ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_parser_config()
    
    try:
        cache_mgr = ParserConfigCacheMgr()
        
        # Initially cache should not exist
        assert not cache_mgr.cache_exists("test_program"), "Cache should not exist before generation"
        
        # Generate cache
        cache_mgr.generate_parser_config_cache()
        
        # Now cache should exist
        assert cache_mgr.cache_exists("test_program"), "Cache should exist after generation"
        
        # Test non-existent program
        assert not cache_mgr.cache_exists("nonexistent_program"), "Non-existent program cache should not exist"
        
        print("✅ Cache existence check test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def main():
    """Run all tests"""
    print("Starting parser configuration cache manager core functionality tests...\n")
    
    try:
        test_cache_generation_and_loading()
        test_cache_file_content()
        test_directory_separation()
        test_cache_exists_check()
        
        print("\n🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())