#!/usr/bin/env python3
"""
CmdMapping Tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import tomli_w
import sys

# Add project root directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.core.cmd_mapping import CmdMapping
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig

import log

class TestCmdMapping:
    """CmdMapping Test Class"""
    
    def setup_method(self):
        """Test setup"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Reset PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # Create test configuration
        self._create_test_config()
    
    def teardown_method(self):
        """Test cleanup"""
        shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_test_config(self):
        """Create test configuration"""
        # Create cache directory
        cache_dir = self.path_manager.get_cmd_mappings_domain_dir_of_cache("package")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cmd_to_operation file
        cmd_to_op = {
            "cmd_to_operation": {
                "apt": {
                    "programs": ["apt"]
                },
                "pacman": {
                    "programs": ["pacman"]
                }
            }
        }
        
        cmd_to_op_file = self.path_manager.get_cmd_to_operation_path("package")
        with open(cmd_to_op_file, 'wb') as f:
            tomli_w.dump(cmd_to_op, f)
        
        # Create apt command mapping - using correct subcommand structure
        apt_dir = self.path_manager.get_cmd_mappings_group_dir_of_cache("package", "apt")
        apt_dir.mkdir(parents=True, exist_ok=True)
        
        apt_mappings = {
            "command_mappings": [
                {
                    "operation": "install_remote",
                    "cmd_format": "apt install {pkgs}",
                    "cmd_node": {
                        "name": "apt",
                        "subcommand": {
                            "name": "install",
                            "arguments": [
                                {
                                    "node_type": "positional",
                                    "values": ["__param_pkgs__"],
                                    "placeholder": "pkgs"
                                }
                            ]
                        }
                    }
                },
                {
                    "operation": "search_remote",
                    "cmd_format": "apt search {query}",
                    "cmd_node": {
                        "name": "apt",
                        "subcommand": {
                            "name": "search",
                            "arguments": [
                                {
                                    "node_type": "positional",
                                    "values": ["__param_query__"],
                                    "placeholder": "query"
                                }
                            ]
                        }
                    }
                },
                {
                    "operation": "update",
                    "cmd_format": "apt update",
                    "cmd_node": {
                        "name": "apt",
                        "subcommand": {
                            "name": "update",
                            "arguments": []
                        }
                    }
                }
            ]
        }
        
        apt_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_mappings, f)
        
        # Create pacman command mapping
        pacman_dir = self.path_manager.get_cmd_mappings_group_dir_of_cache("package", "pacman")
        pacman_dir.mkdir(parents=True, exist_ok=True)
        
        pacman_mappings = {
            "command_mappings": [
                {
                    "operation": "install_remote",
                    "cmd_format": "pacman -S {pkgs}",
                    "cmd_node": {
                        "name": "pacman",
                        "arguments": [
                            {
                                "node_type": "flag",
                                "option_name": "-S",
                                "values": [],
                                "repeat": 1
                            },
                            {
                                "node_type": "positional",
                                "values": ["__param_pkgs__"],
                                "placeholder": "pkgs"
                            }
                        ]
                    }
                }
            ]
        }
        
        pacman_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
            "package", "pacman", "pacman"
        )
        with open(pacman_file, 'wb') as f:
            tomli_w.dump(pacman_mappings, f)
    
    def _create_apt_parser_config(self) -> ParserConfig:
        """Create apt parser configuration"""
        return ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="apt",
            arguments=[
                ArgumentConfig(
                    name="help",
                    opt=["-h", "--help"],
                    nargs=ArgumentCount.ZERO
                )
            ],
            sub_commands=[
                SubCommandConfig(
                    name="install",
                    arguments=[
                        ArgumentConfig(
                            name="packages",
                            opt=[],  # positional argument
                            nargs=ArgumentCount.ONE_OR_MORE
                        )
                    ]
                ),
                SubCommandConfig(
                    name="search",
                    arguments=[
                        ArgumentConfig(
                            name="query",
                            opt=[],  # positional argument
                            nargs=ArgumentCount.ONE_OR_MORE
                        )
                    ]
                ),
                SubCommandConfig(
                    name="update",
                    arguments=[]  # no arguments
                )
            ]
        )
    
    def _create_pacman_parser_config(self) -> ParserConfig:
        """Create pacman parser configuration"""
        return ParserConfig(
            parser_type=ParserType.GETOPT,
            program_name="pacman",
            arguments=[
                ArgumentConfig(
                    name="sync",
                    opt=["-S", ""],
                    nargs=ArgumentCount.ZERO
                ),
                ArgumentConfig(
                    name="packages",
                    opt=[],  # positional argument
                    nargs=ArgumentCount.ONE_OR_MORE
                )
            ],
            sub_commands=[]
        )
    
    def test_load_from_cache(self):
        """Test loading from cache"""
        # Test loading existing program
        mapping = CmdMapping.load_from_cache("package", "apt")
        assert mapping is not None
        assert "apt" in mapping.mapping_config
        
        command_mappings = mapping.mapping_config["apt"]["command_mappings"]
        assert len(command_mappings) == 3
        
        # Test loading non-existent program
        nonexistent = CmdMapping.load_from_cache("package", "nonexistent")
        assert nonexistent.mapping_config == {}
    
    def test_basic_command_mapping(self):
        """Test basic command mapping"""
        mapping = CmdMapping.load_from_cache("package", "apt")
        parser_config = self._create_apt_parser_config()
        
        result = mapping.map_to_operation(
            source_cmdline=["apt", "install", "vim", "git"],
            source_parser_config=parser_config,
            dst_operation_group="apt"
        )
        
        assert result is not None
        assert result["operation_name"] == "install_remote"
        assert result["params"]["pkgs"] == "vim git"
    
    def test_search_command_mapping(self):
        """Test search command mapping"""
        mapping = CmdMapping.load_from_cache("package", "apt")
        parser_config = self._create_apt_parser_config()
        
        result = mapping.map_to_operation(
            source_cmdline=["apt", "search", "python"],
            source_parser_config=parser_config,
            dst_operation_group="apt"
        )
        
        assert result is not None
        assert result["operation_name"] == "search_remote"
        assert result["params"]["query"] == "python"
    
    def test_no_parameters_command(self):
        """Test command without parameters"""
        mapping = CmdMapping.load_from_cache("package", "apt")
        parser_config = self._create_apt_parser_config()
        
        result = mapping.map_to_operation(
            source_cmdline=["apt", "update"],
            source_parser_config=parser_config,
            dst_operation_group="apt"
        )
        
        assert result is not None
        assert result["operation_name"] == "update"
        assert result["params"] == {}  # no parameters
    
    def test_pacman_command_mapping(self):
        """Test pacman command mapping"""
        mapping = CmdMapping.load_from_cache("package", "pacman")
        parser_config = self._create_pacman_parser_config()
        
        result = mapping.map_to_operation(
            source_cmdline=["pacman", "-S", "vim", "git"],
            source_parser_config=parser_config,
            dst_operation_group="pacman"
        )
        
        assert result is not None
        assert result["operation_name"] == "install_remote"
        assert result["params"]["pkgs"] == "vim git"
    
    def test_convenience_function(self):
        """Test convenience function"""
        from cmdbridge.core.cmd_mapping import create_cmd_mapping
        
        test_config = {
            "test_program": {
                "command_mappings": [
                    {
                        "operation": "test_op",
                        "cmd_format": "test {param}",
                        "cmd_node": {
                            "name": "test",
                            "arguments": [
                                {
                                    "node_type": "positional",
                                    "values": ["__param_param__"],
                                    "placeholder": "param"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        mapping = create_cmd_mapping(test_config)
        assert mapping is not None
        assert "test_program" in mapping.mapping_config


if __name__ == "__main__":
    # Set log level
    log.set_level(log.LogLevel.DEBUG)
    
    import pytest
    pytest.main([__file__, "-v", "-s"])