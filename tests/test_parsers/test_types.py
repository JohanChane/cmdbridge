# test/test_parsers/test_types.py
import sys
from pathlib import Path

from parsers.types import ArgNode, SyntaxTree, ParserConfig, ArgType


class TestArgNode:
    """Test ArgNode"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        node = ArgNode(
            name="test",
            type=ArgType.FLAG,
            values=[],
            args=[],
            repeat=1,
            original_opt="--test"
        )
        assert node.name == "test"
        assert node.type == ArgType.FLAG
        assert node.values == []
        assert node.args == []
        assert node.repeat == 1

    def test_flag_node(self):
        """测试标志节点"""
        node = ArgNode(
            name="verbose",
            type=ArgType.FLAG,
            values=[],
            args=[],
            repeat=2,
            original_opt="-vv"
        )
        assert node.name == "verbose"
        assert node.type == ArgType.FLAG
        assert node.repeat == 2

    def test_sub_cmd_node(self):
        """测试子命令节点"""
        sub_arg = ArgNode(
            name="force",
            type=ArgType.FLAG,
            values=[],
            args=[],
            repeat=1,
            original_opt="--force"
        )
        
        node = ArgNode(
            name="install",
            type=ArgType.SUB_CMD,
            values=["vim", "git"],
            args=[sub_arg],
            repeat=1,
            original_opt="install"
        )
        
        assert node.name == "install"
        assert node.type == ArgType.SUB_CMD
        assert node.values == ["vim", "git"]
        assert len(node.args) == 1
        assert node.args[0].name == "force"


class TestSyntaxTree:
    """Test SyntaxTree"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        result = SyntaxTree(
            command_name="",
            argument_nodes=[],
            extra_content=None
        )
        assert result['command_name'] == ""
        assert result['argument_nodes'] == []
        assert result['extra_content'] is None

    def test_with_data(self):
        """测试带数据的创建"""
        arg_node = ArgNode(
            name="-S", 
            type=ArgType.FLAG,
            values=[],
            args=[],
            repeat=1,
            original_opt="-S"
        )
        result = SyntaxTree(
            command_name="pacman",
            argument_nodes=[arg_node],
            extra_content=None
        )
        assert result['command_name'] == "pacman"
        assert len(result['argument_nodes']) == 1
        # ArgNode 是 dataclass，使用 . 访问
        assert result['argument_nodes'][0].name == "-S"


class TestParserConfig:
    """Test ParserConfig"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        config = ParserConfig(
            name="help",
            arg_name="help",
            type=ArgType.FLAG,
            short_opt="-h",
            long_opt="--help"
        )
        assert config.name == "help"
        assert config.arg_name == "help"
        assert config.type == ArgType.FLAG
        assert config.short_opt == "-h"
        assert config.long_opt == "--help"

    def test_option_config(self):
        """测试选项配置"""
        config = ParserConfig(
            name="output",
            arg_name="output_path",
            type=ArgType.OPTION_NEEDS_VALUE,
            short_opt="-o",
            long_opt="--output",
            nargs=1
        )
        assert config.name == "output"
        assert config.type == ArgType.OPTION_NEEDS_VALUE
        assert config.nargs == 1

    def test_sub_command_config(self):
        """测试子命令配置"""
        sub_config = ParserConfig(
            name="force",
            arg_name="force_flag",
            type=ArgType.FLAG,
            long_opt="--force"
        )
        
        config = ParserConfig(
            name="install",
            arg_name="targets",
            type=ArgType.SUB_CMD,
            nargs="*",
            sub_args=[sub_config]
        )
        assert config.name == "install"
        assert config.type == ArgType.SUB_CMD
        assert config.nargs == "*"
        assert len(config.sub_args) == 1
        assert config.sub_args[0].name == "force"