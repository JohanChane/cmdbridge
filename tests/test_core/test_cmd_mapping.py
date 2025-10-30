#!/usr/bin/env python3
"""
CmdMapping 测试 - 修复完整版
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import tomli_w
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.core.cmd_mapping import CmdMapping
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig

import log

class TestCmdMapping:
    """CmdMapping 测试类 - 修复完整版"""
    
    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 重置 PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # 创建测试配置
        self._create_test_config()
    
    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_test_config(self):
        """创建测试配置 - 修复版本"""
        # 创建缓存目录
        cache_dir = self.path_manager.get_cmd_mappings_domain_dir_of_cache("package")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 cmd_to_operation 文件
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
        
        # 创建 apt 命令映射 - 使用正确的子命令结构
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
        
        # 创建 pacman 命令映射
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
        """创建 apt 解析器配置 - 修复版本"""
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
                            opt=[],  # 位置参数
                            nargs=ArgumentCount.ONE_OR_MORE
                        )
                    ]
                ),
                SubCommandConfig(
                    name="search",
                    arguments=[
                        ArgumentConfig(
                            name="query",
                            opt=[],  # 位置参数
                            nargs=ArgumentCount.ONE_OR_MORE
                        )
                    ]
                ),
                SubCommandConfig(
                    name="update",
                    arguments=[]  # 无参数
                )
            ]
        )
    
    def _create_pacman_parser_config(self) -> ParserConfig:
        """创建 pacman 解析器配置"""
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
                    opt=[],  # 位置参数
                    nargs=ArgumentCount.ONE_OR_MORE
                )
            ],
            sub_commands=[]
        )
    
    def test_load_from_cache(self):
        """测试从缓存加载"""
        # 测试加载存在的程序
        mapping = CmdMapping.load_from_cache("package", "apt")
        assert mapping is not None
        assert "apt" in mapping.mapping_config
        
        command_mappings = mapping.mapping_config["apt"]["command_mappings"]
        assert len(command_mappings) == 3
        
        # 测试加载不存在的程序
        nonexistent = CmdMapping.load_from_cache("package", "nonexistent")
        assert nonexistent.mapping_config == {}
    
    def test_basic_command_mapping(self):
        """测试基本命令映射"""
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
        """测试搜索命令映射"""
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
        """测试无参数命令"""
        mapping = CmdMapping.load_from_cache("package", "apt")
        parser_config = self._create_apt_parser_config()
        
        result = mapping.map_to_operation(
            source_cmdline=["apt", "update"],
            source_parser_config=parser_config,
            dst_operation_group="apt"
        )
        
        assert result is not None
        assert result["operation_name"] == "update"
        assert result["params"] == {}  # 无参数
    
    def test_pacman_command_mapping(self):
        """测试 pacman 命令映射"""
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
        """测试便捷函数"""
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


# 移除 run_tests() 函数，直接使用 pytest
if __name__ == "__main__":
    # 设置日志级别
    log.set_level(log.LogLevel.DEBUG)
    
    # 直接运行 pytest
    import pytest
    pytest.main([__file__, "-v", "-s"])