# test/test_parsers/test_getopt.py
import pytest
import sys
from pathlib import Path

from parsers.factory import ParserFactory
from parsers.types import ParserConfig, SyntaxTree, ArgNode, ArgType


class TestGetoptParser:
    """Test Getopt Parser"""
    
    def _create_pacman_config(self):
        """创建 pacman 配置"""
        return [
            ParserConfig(
                name="S",
                arg_name="sync_flag",
                type=ArgType.FLAG,
                short_opt="-S"
            ),
            ParserConfig(
                name="s", 
                arg_name="search_flag",
                type=ArgType.FLAG,
                short_opt="-s"
            ),
            ParserConfig(
                name="y",
                arg_name="refresh_flag", 
                type=ArgType.FLAG,
                short_opt="-y"
            ),
            ParserConfig(
                name="u",
                arg_name="upgrade_flag",
                type=ArgType.FLAG, 
                short_opt="-u"
            ),
            ParserConfig(
                name="cmd_arg",
                arg_name="targets",
                type=ArgType.VALUE,
                nargs="*"
            )
        ]
    
    def test_simple_command(self):
        """测试简单命令"""
        configs = self._create_pacman_config()
        parser = ParserFactory.create_parser("getopt", configs)
        
        result = parser.parse(["pacman", "-S"])
        
        assert result['command_name'] == "pacman"
        assert len(result['argument_nodes']) == 1
        assert result['argument_nodes'][0].name == "-S"
        assert result['argument_nodes'][0].type == ArgType.FLAG

    def test_command_with_targets(self):
        """测试带目标的命令"""
        configs = self._create_pacman_config()
        parser = ParserFactory.create_parser("getopt", configs)
        
        result = parser.parse(["pacman", "-S", "vim", "git"])
        
        assert result['command_name'] == "pacman"
        assert len(result['argument_nodes']) == 3
        assert result['argument_nodes'][0].name == "-S"
        assert result['argument_nodes'][1].name == "vim"
        assert result['argument_nodes'][1].type == ArgType.VALUE
        assert result['argument_nodes'][2].name == "git"
        assert result['argument_nodes'][2].type == ArgType.VALUE

    def test_combined_flags(self):
        """测试组合标志"""
        configs = self._create_pacman_config()
        parser = ParserFactory.create_parser("getopt", configs)
        
        result = parser.parse(["pacman", "-Syu"])
        
        assert result['command_name'] == "pacman"
        assert len(result['argument_nodes']) == 3
        assert result['argument_nodes'][0].name == "-S"
        assert result['argument_nodes'][1].name == "-y" 
        assert result['argument_nodes'][2].name == "-u"

    def test_unknown_option(self):
        """测试未知选项"""
        configs = self._create_pacman_config()
        parser = ParserFactory.create_parser("getopt", configs)
        
        # 未知选项应该报错
        with pytest.raises(ValueError, match="Unknown option: -X"):
            parser.parse(["pacman", "-X", "vim"])
            
    def test_extra_args(self):
        """测试额外参数（-- 分隔符）"""
        configs = self._create_pacman_config()
        parser = ParserFactory.create_parser("getopt", configs)
        
        result = parser.parse(["pacman", "-S", "vim", "--", "extra", "args"])
        
        assert result['command_name'] == "pacman"
        assert result['extra_content'] == "extra args"
        assert len(result['argument_nodes']) == 2
        assert result['argument_nodes'][0].name == "-S"
        assert result['argument_nodes'][1].name == "vim"

    def test_option_with_value(self):
        """测试带值的选项"""
        configs = [
            ParserConfig(
                name="output",
                arg_name="output_path",
                type=ArgType.OPTION_NEEDS_VALUE,
                short_opt="-o",
                long_opt="--output",
                nargs=1
            )
        ]
        
        parser = ParserFactory.create_parser("getopt", configs)
        result = parser.parse(["command", "-o", "file.txt"])
        
        assert result['command_name'] == "command"
        assert len(result['argument_nodes']) == 2
        assert result['argument_nodes'][0].name == "-o"
        assert result['argument_nodes'][0].type == ArgType.OPTION_NEEDS_VALUE
        assert result['argument_nodes'][1].name == "output_path"
        assert result['argument_nodes'][1].type == ArgType.VALUE
        assert result['argument_nodes'][1].values == ["file.txt"]

    def test_combined_flags_behavior(self):
        """测试组合标志的行为 - S 和 s 是同级关系"""
        configs = [
            ParserConfig(
                name="S",
                arg_name="sync_flag", 
                type=ArgType.FLAG,
                short_opt="-S"
            ),
            ParserConfig(
                name="s",
                arg_name="search_flag",
                type=ArgType.FLAG,
                short_opt="-s"
            ),
            ParserConfig(
                name="cmd_arg",
                arg_name="targets",
                type=ArgType.VALUE,
                nargs="*"
            )
        ]
        
        parser = ParserFactory.create_parser("getopt", configs)
        result = parser.parse(["pacman", "-Ss", "vim"])
        
        assert result['command_name'] == "pacman"
        # -Ss 应该展开为 -S -s，所以有3个参数节点
        assert len(result['argument_nodes']) == 3
        assert result['argument_nodes'][0].name == "-S"
        assert result['argument_nodes'][0].type == ArgType.FLAG
        assert result['argument_nodes'][1].name == "-s"
        assert result['argument_nodes'][1].type == ArgType.FLAG
        assert result['argument_nodes'][2].name == "vim"
        assert result['argument_nodes'][2].type == ArgType.VALUE