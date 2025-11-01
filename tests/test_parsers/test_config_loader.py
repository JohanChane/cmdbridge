#!/usr/bin/env python3
"""
Test configuration loader core functionality
"""

import sys
import os
from pathlib import Path

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.config_loader import ConfigLoader, load_parser_config_from_data
from parsers.types import ParserType
import tempfile
import tomli_w


def test_basic_parser_config():
    """Test basic parser configuration loading"""
    print("=== Testing Basic Parser Configuration ===")
    
    config_data = {
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
                            "name": "packages",
                            "nargs": "+"
                        }
                    ]
                }
            ]
        }
    }
    
    loader = ConfigLoader(config_data)
    parser_config = loader.load_parser_config("apt")
    
    # Verify basic properties
    assert parser_config.parser_type == ParserType.ARGPARSE
    assert parser_config.program_name == "apt"
    assert len(parser_config.arguments) == 1
    assert len(parser_config.sub_commands) == 1
    
    # Verify arguments
    help_arg = parser_config.arguments[0]
    assert help_arg.name == "help"
    assert help_arg.opt == ["-h", "--help"]
    assert help_arg.nargs.spec == "0"
    assert help_arg.is_flag()
    
    # Verify subcommands
    install_cmd = parser_config.sub_commands[0]
    assert install_cmd.name == "install"
    assert len(install_cmd.arguments) == 1
    assert install_cmd.arguments[0].name == "packages"
    assert install_cmd.arguments[0].nargs.spec == "+"
    
    print("✅ Basic parser configuration test passed")


def test_id_and_include_functionality():
    """Test ID and include_arguments_and_subcmds functionality"""
    print("\n=== Testing ID and Include Functionality ===")
    
    config_data = {
        "mufw": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "mufw"
            },
            "sub_commands": [
                {
                    "name": "allow",
                    "id": "subcmd_id_allow",
                    "arguments": [
                        {
                            "name": "port",
                            "opt": ["--port"],
                            "nargs": "1"
                        },
                        {
                            "name": "protocol", 
                            "opt": ["--proto"],
                            "nargs": "1"
                        }
                    ]
                },
                {
                    "name": "deny",
                    "include_arguments_and_subcmds": "subcmd_id_allow"
                }
            ]
        }
    }
    
    loader = ConfigLoader(config_data)
    parser_config = loader.load_parser_config("mufw")
    
    # Verify basic structure
    assert len(parser_config.sub_commands) == 2
    
    # Verify allow subcommand
    allow_cmd = next(cmd for cmd in parser_config.sub_commands if cmd.name == "allow")
    assert len(allow_cmd.arguments) == 2
    assert allow_cmd.arguments[0].name == "port"
    assert allow_cmd.arguments[1].name == "protocol"
    
    # Verify deny subcommand (should include allow's arguments)
    deny_cmd = next(cmd for cmd in parser_config.sub_commands if cmd.name == "deny")
    assert len(deny_cmd.arguments) == 2
    assert deny_cmd.arguments[0].name == "port"
    assert deny_cmd.arguments[1].name == "protocol"
    
    print("✅ ID and include functionality test passed")


def test_file_loading():
    """Test loading configuration from file"""
    print("\n=== Testing File Loading ===")
    
    # Create temporary configuration file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
        config_data = {
            "file_test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "file_test"
                },
                "arguments": [
                    {
                        "name": "file_arg",
                        "opt": ["-f", "--file"],
                        "nargs": "1"
                    }
                ]
            }
        }
        tomli_w.dump(config_data, f)
        temp_file = f.name
    
    try:
        # Use convenience function to load from file
        from parsers.config_loader import load_parser_config_from_file
        parser_config = load_parser_config_from_file(temp_file, "file_test")
        
        assert parser_config.parser_type == ParserType.ARGPARSE
        assert parser_config.program_name == "file_test"
        assert len(parser_config.arguments) == 1
        assert parser_config.arguments[0].name == "file_arg"
        
        print("✅ File loading test passed")
    finally:
        # Clean up temporary file
        os.unlink(temp_file)


def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Test missing program configuration
    config_data = {
        "other_program": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "other"
            }
        }
    }
    
    loader = ConfigLoader(config_data)
    try:
        loader.load_parser_config("nonexistent_program")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "missing" in str(e).lower() or "missing" in str(e)
        print("✅ Error handling test passed")


def main():
    """Run all tests"""
    print("Starting configuration loader core functionality tests...\n")
    
    try:
        test_basic_parser_config()
        test_id_and_include_functionality()
        test_file_loading()
        test_error_handling()
        
        print("\n🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())