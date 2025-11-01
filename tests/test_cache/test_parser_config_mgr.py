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
    """Set up test parser configuration"""
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()
    
    # Initialize PathManager
    path_manager = PathManager(
        config_dir=temp_dir,
        cache_dir=temp_dir
    )
    
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
    
    # Write configuration file
    config_file = parser_config_dir / "test_program.toml"
    with open(config_file, 'wb') as f:
        tomli_w.dump(test_parser_config, f)
    
    return temp_dir, path_manager


def test_cache_generation_and_loading():
    """Test cache generation and loading functionality"""
    print("=== Testing Cache Generation and Loading ===")
    
    temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # Create cache manager
        cache_mgr = ParserConfigCacheMgr()
        
        # Generate cache
        cache_mgr.generate_parser_config_cache()
        
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
        shutil.rmtree(temp_dir)


def test_cache_file_content():
    """Test cache file content"""
    print("\n=== Testing Cache File Content ===")
    
    temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # Create cache manager
        cache_mgr = ParserConfigCacheMgr()
        
        # Generate cache
        cache_mgr.generate_parser_config_cache()
        
        # Verify cache file content
        cache_file = path_manager.get_parser_config_path_of_cache("test_program")
        assert cache_file.exists()
        
        with open(cache_file, 'rb') as f:
            cached_data = tomli.load(f)
        
        # Verify basic structure
        assert "parser_type" in cached_data
        assert "program_name" in cached_data
        assert "arguments" in cached_data
        
        print("✅ Cache file content test passed")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run all tests"""
    print("Starting parser configuration cache manager core functionality tests...\n")
    
    try:
        test_cache_generation_and_loading()
        test_cache_file_content()
        
        print("\n🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())