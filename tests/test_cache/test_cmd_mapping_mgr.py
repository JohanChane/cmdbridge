#!/usr/bin/env python3
"""
Test command mapping manager core functionality - Fixed version with separate config and cache dirs
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cmdbridge.cache.cmd_mapping_mgr import CmdMappingMgr
from cmdbridge.config.path_manager import PathManager
from cmdbridge.cache.parser_config_mgr import ParserConfigCacheMgr
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount
import tomli_w


def setup_test_configs():
    """Set up test configurations with separate config and cache directories under same parent"""
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
    
    # Create test domain and operation group configurations
    domain_dir = path_manager.get_operation_domain_dir_of_config("test_package")
    domain_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operation group configuration file
    group_config = {
        "operations": {
            "install_remote": {
                "cmd_format": "apt install {pkgs}"
            },
            "list_installed": {
                "cmd_format": "apt list --installed"
            }
        }
    }
    
    group_file = domain_dir / "apt.toml"
    with open(group_file, 'wb') as f:
        tomli_w.dump(group_config, f)
    
    # Create program parser configuration directory
    parser_config_dir = path_manager.program_parser_config_dir
    parser_config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create apt parser configuration
    apt_parser_config = {
        "apt": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "apt"
            },
            "arguments": [
                {
                    "name": "help",
                    "opt": ["-h", "--help"],
                    "nargs": "0"
                }
            ],
            "sub_commands": [
                {
                    "name": "install",
                    "arguments": [
                        {
                            "name": "pkgs",
                            "nargs": "+"
                        }
                    ]
                },
                {
                    "name": "list", 
                    "arguments": [
                        {
                            "name": "installed",
                            "opt": ["--installed"],
                            "nargs": "0"
                        }
                    ]
                }
            ]
        }
    }
    
    apt_parser_file = parser_config_dir / "apt.toml"
    with open(apt_parser_file, 'wb') as f:
        tomli_w.dump(apt_parser_config, f)
    
    # Generate parser configuration cache
    parser_cache_mgr = ParserConfigCacheMgr()
    parser_cache_mgr.generate_parser_config_cache()
    
    return parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager


def create_mock_parser_config():
    """Create mock parser configuration for unit tests"""
    return ParserConfig(
        parser_type=ParserType.ARGPARSE,
        program_name="apt",
        arguments=[
            ArgumentConfig(
                name="pkgs",
                opt=[],
                nargs=ArgumentCount("+"),
                required=False
            ),
            ArgumentConfig(
                name="config_path", 
                opt=["--config"],
                nargs=ArgumentCount("1"),
                required=False
            )
        ],
        sub_commands=[]
    )


def test_program_extraction():
    """Test program name extraction functionality"""
    print("=== Testing Program Name Extraction ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # Test various command formats
    test_cases = [
        ("apt install {pkgs}", "apt"),
        ("pacman -S {pkgs}", "pacman"),
        ("docker container ls", "docker"),
        ("git commit -m '{message}'", "git"),
        ("", None),
        ("   ", None),
    ]
    
    for cmd_format, expected in test_cases:
        result = mapping_mgr._extract_program_from_cmd_format(cmd_format)
        assert result == expected, f"For '{cmd_format}', expected '{expected}', but got '{result}'"
    
    print("✅ Program name extraction test passed")


def test_example_command_generation():
    """Test example command generation functionality"""
    print("\n=== Testing Example Command Generation ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # Create mock parser configuration
    parser_config = create_mock_parser_config()
    
    # Test command format parsing
    cmd_format = "apt install {pkgs} --config {config_path}"
    example_cmd = mapping_mgr._generate_example_command(cmd_format, parser_config)
    
    # Verify generated example command
    assert len(example_cmd) >= 3
    assert example_cmd[0] == "apt"
    assert example_cmd[1] == "install"
    
    # Check if it contains placeholders
    has_placeholders = any("__param_" in part for part in example_cmd)
    assert has_placeholders, "Example command should contain placeholders"
    
    print("✅ Example command generation test passed")


def test_param_example_values():
    """Test parameter example value generation"""
    print("\n=== Testing Parameter Example Value Generation ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # Create mock parser configuration
    parser_config = create_mock_parser_config()
    
    # Test single-value parameter
    single_values = mapping_mgr._generate_param_example_values("config_path", parser_config)
    assert len(single_values) == 1
    assert "__param_config_path__" in single_values[0]
    
    # Test multi-value parameter
    multi_values = mapping_mgr._generate_param_example_values("pkgs", parser_config)
    assert len(multi_values) == 2
    assert all("__param_pkgs__" in value for value in multi_values)
    
    # Test non-existent parameter (using default value)
    default_values = mapping_mgr._generate_param_example_values("nonexistent", parser_config)
    assert len(default_values) == 1
    assert "__param_nonexistent__" in default_values[0]
    
    print("✅ Parameter example value generation test passed")


def test_mapping_structure():
    """Test mapping data structure"""
    print("\n=== Testing Mapping Data Structure ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_configs()
    
    try:
        # Create mapping manager
        mapping_mgr = CmdMappingMgr("test_package", "apt")
        
        # Generate mapping data
        mapping_data = mapping_mgr.create_mappings()
        
        # Verify returned data structure
        assert "program_mappings" in mapping_data
        assert "cmd_to_operation" in mapping_data
        
        # Verify program mapping structure
        program_mappings = mapping_data["program_mappings"]
        assert isinstance(program_mappings, dict)
        assert "apt" in program_mappings  # Should have apt program mappings
        
        # Verify cmd_to_operation structure
        cmd_to_operation = mapping_data["cmd_to_operation"]
        assert isinstance(cmd_to_operation, dict)
        assert "apt" in cmd_to_operation  # Should have apt operation group
        
        print("✅ Mapping data structure test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_file_writing():
    """Test file writing functionality"""
    print("\n=== Testing File Writing ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_configs()
    
    try:
        # Create mapping manager
        mapping_mgr = CmdMappingMgr("test_package", "apt")
        
        # Generate mapping data
        mapping_data = mapping_mgr.create_mappings()
        
        # Write to files
        mapping_mgr.write_to()
        
        # Verify cache directory was created
        cache_dir = path_manager.get_cmd_mappings_domain_dir_of_cache("test_package")
        assert cache_dir.exists()
        
        # Verify program mapping files were created
        program_file = path_manager.get_cmd_mappings_group_program_path_of_cache(
            "test_package", "apt", "apt"
        )
        assert program_file.exists()
        
        # Verify cmd_to_operation file was created
        cmd_to_operation_file = path_manager.get_cmd_to_operation_path("test_package")
        assert cmd_to_operation_file.exists()
        
        # Verify files are actually in the cache directory, not config directory
        assert str(cache_dir).startswith(str(cache_temp_dir)), "Cache files should be in cache directory"
        
        print("✅ File writing test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_operation_processing():
    """Test operation processing functionality"""
    print("\n=== Testing Operation Processing ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_configs()
    
    try:
        # Create mapping manager
        mapping_mgr = CmdMappingMgr("test_package", "apt")
        
        # Generate mapping data
        mapping_data = mapping_mgr.create_mappings()
        
        # Verify operations were processed
        program_mappings = mapping_data["program_mappings"]
        apt_mappings = program_mappings.get("apt", {})
        command_mappings = apt_mappings.get("command_mappings", [])
        
        # Should have at least one command mapping
        assert len(command_mappings) > 0
        
        # Verify operation names
        operation_names = [mapping["operation"] for mapping in command_mappings]
        assert "install_remote" in operation_names or "list_installed" in operation_names
        
        # Verify command node structure
        for mapping in command_mappings:
            assert "cmd_node" in mapping
            assert "operation" in mapping
            assert "cmd_format" in mapping
        
        print("✅ Operation processing test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def test_directory_separation():
    """Test that config and cache directories are properly separated under same parent"""
    print("\n=== Testing Directory Separation ===")
    
    parent_temp_dir, config_temp_dir, cache_temp_dir, path_manager = setup_test_configs()
    
    try:
        # Verify directories are different but under same parent
        assert config_temp_dir != cache_temp_dir, "Config and cache directories should be different"
        assert config_temp_dir.parent == cache_temp_dir.parent, "Config and cache should be under same parent"
        
        # Verify PathManager uses correct directories
        assert str(path_manager.config_dir) == str(config_temp_dir)
        assert str(path_manager.cache_dir) == str(cache_temp_dir)
        
        # Verify config files are in config directory
        config_file = path_manager.get_operation_group_path_of_config("test_package", "apt")
        assert str(config_file).startswith(str(config_temp_dir)), "Config files should be in config directory"
        
        # Verify cache files are in cache directory
        cache_file = path_manager.get_cmd_mappings_domain_dir_of_cache("test_package")
        assert str(cache_file).startswith(str(cache_temp_dir)), "Cache files should be in cache directory"
        
        print("✅ Directory separation test passed")
        
    finally:
        import shutil
        shutil.rmtree(parent_temp_dir)


def main():
    """Run all tests"""
    print("Starting command mapping manager core functionality tests...\n")
    
    try:
        test_program_extraction()
        test_param_example_values()
        test_example_command_generation()
        test_mapping_structure()
        test_file_writing()
        test_operation_processing()
        test_directory_separation()
        
        print("\n🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())