# test/test_parsers/test_factory.py
import pytest
import sys
from pathlib import Path

from parsers.factory import ParserFactory
from parsers.types import ParserConfig, ArgType


class TestParserFactory:
    """Test Parser Factory"""
    
    def test_create_getopt_parser(self):
        """测试创建 Getopt 解析器"""
        configs = [
            ParserConfig(
                name="S",
                arg_name="sync_flag",
                type=ArgType.FLAG,
                short_opt="-S"
            )
        ]
        
        parser = ParserFactory.create_parser("getopt", configs)
        result = parser.parse(["pacman", "-S"])
        
        assert result['command_name'] == "pacman"
        assert len(result['argument_nodes']) == 1
        assert result['argument_nodes'][0].name == "-S"

    def test_invalid_parser_type(self):
        """测试无效的解析器类型"""
        configs = []
        
        with pytest.raises(ValueError, match="Unsupported parser type"):
            ParserFactory.create_parser("invalid_type", configs)

    def test_complex_config_conversion(self):
        """测试复杂配置转换"""
        raw_configs = [
            {
                'name': 'install',
                'arg': 'targets',
                'is_sub_cmd': True,
                'nargs': '*'
            },
            {
                'name': 'help',
                'long_opt': '--help', 
                'arg': 'help',
                'is_flag': True
            }
        ]
        
        configs = ParserFactory._convert_configs(raw_configs)
        
        assert len(configs) == 2
        assert configs[0].name == 'install'
        assert configs[0].type == ArgType.SUB_CMD
        assert configs[1].name == 'help'
        assert configs[1].type == ArgType.FLAG

    def test_getopt_unknown_option_error(self):
        """测试 Getopt 解析器对未知选项报错"""
        configs = [
            ParserConfig(
                name="help",
                arg_name="help",
                type=ArgType.FLAG,
                short_opt="-h"
            )
        ]
        
        parser = ParserFactory.create_parser("getopt", configs)
        
        # 未知选项应该报错
        with pytest.raises(ValueError, match="Unknown option: -X"):
            parser.parse(["command", "-X"])