#!/usr/bin/env python3
"""
Test command mapping manager core functionality
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cmdbridge.cache.cmd_mapping_mgr import CmdMappingMgr
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount
import tomli_w


def setup_test_configs():
    """Set up test configurations"""
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()
    
    # Initialize PathManager
    path_manager = PathManager(
        config_dir=temp_dir,
        cache_dir=temp_dir
    )
    
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
    
    return temp_dir, path_manager


def create_mock_parser_config():
    """Create mock parser configuration"""
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
    
    temp_dir, path_manager = setup_test_configs()
    
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
        
        # Verify cmd_to_operation structure
        cmd_to_operation = mapping_data["cmd_to_operation"]
        assert isinstance(cmd_to_operation, dict)
        
        print("✅ Mapping data structure test passed")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_file_writing():
    """Test file writing functionality"""
    print("\n=== Testing File Writing ===")
    
    temp_dir, path_manager = setup_test_configs()
    
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
        
        print("✅ File writing test passed")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run all tests"""
    print("Starting command mapping manager core functionality tests...\n")
    
    try:
        test_program_extraction()
        test_param_example_values()
        test_example_command_generation()
        test_mapping_structure()
        test_file_writing()
        
        print("\n🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())