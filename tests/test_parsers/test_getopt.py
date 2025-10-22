"""
getopt 解析器测试
"""

import pytest
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from parsers.getopt_parser import GetoptParser
from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType, ArgumentConfig, ArgumentCount

import log

class TestGetoptParser:
    """getopt 解析器测试类"""
    
    def _create_pacman_config(self):
        """创建 pacman 配置"""
        return ParserConfig(
            parser_type=ParserType.GETOPT,
            program_name="pacman",
            arguments=[
                ArgumentConfig(name="sync", opt=["-S", "--sync"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="refresh", opt=["-y", "--refresh"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="noconfirm", opt=["--noconfirm"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="config", opt=["--config"], nargs=ArgumentCount('1'), required=True),  # 必需参数
                ArgumentConfig(name="targets", opt=[], nargs=ArgumentCount.ONE_OR_MORE, required=True),  # 必需参数
            ]
        )
    
    def test_parse_simple_flags(self):
        """测试解析简单标志"""
        config = self._create_pacman_config()
        parser = GetoptParser(config)
        
        args = ["pacman", "-S", "-y", "--noconfirm"]
        result = parser.parse(args)
        
        assert result.name == "pacman"
        assert len(result.arguments) == 3
        
        # 检查标志
        assert result.arguments[0].node_type == ArgType.FLAG
        assert result.arguments[0].option_name == "-S"
        
        assert result.arguments[1].node_type == ArgType.FLAG
        assert result.arguments[1].option_name == "-y"
        
        assert result.arguments[2].node_type == ArgType.FLAG
        assert result.arguments[2].option_name == "--noconfirm"
    
    def test_parse_repeated_flags(self):
        """测试解析重复的标志"""
        config = ParserConfig(
            parser_type=ParserType.GETOPT,
            program_name="pacman",
            arguments=[
                ArgumentConfig(name="sync", opt=["-S", "--sync"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="refresh", opt=["-y", "--refresh"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="noconfirm", opt=["--noconfirm"], nargs=ArgumentCount.ZERO),
            ]
        )
        parser = GetoptParser(config)
        
        # 测试重复标志 -Syy
        args = ["pacman", "-Syy"]
        result = parser.parse(args)
        
        assert result.name == "pacman"
        assert len(result.arguments) == 2
        
        # 检查标志和重复次数
        sync_flag = next(arg for arg in result.arguments if arg.option_name == "-S")
        refresh_flag = next(arg for arg in result.arguments if arg.option_name == "-y")
        
        assert sync_flag.node_type == ArgType.FLAG
        assert sync_flag.repeat == 1
        
        assert refresh_flag.node_type == ArgType.FLAG
        assert refresh_flag.repeat == 2
        
        # 测试混合重复标志
        args = ["pacman", "-S", "-y", "-y", "--noconfirm"]
        result = parser.parse(args)
        
        assert result.name == "pacman"
        assert len(result.arguments) == 3
        
        sync_flag = next(arg for arg in result.arguments if arg.option_name == "-S")
        refresh_flag = next(arg for arg in result.arguments if arg.option_name == "-y")
        noconfirm_flag = next(arg for arg in result.arguments if arg.option_name == "--noconfirm")
        
        assert sync_flag.repeat == 1
        assert refresh_flag.repeat == 2
        assert noconfirm_flag.repeat == 1
    
    def test_parse_with_configuration(self):
        """测试使用配置解析"""
        config = self._create_pacman_config()
        parser = GetoptParser(config)
        
        args = ["pacman", "-S", "--config", "custom.conf", "vim", "git"]
        result = parser.parse(args)
        
        assert result.name == "pacman"
        assert len(result.arguments) == 3
        
        # 检查同步标志
        assert result.arguments[0].node_type == ArgType.FLAG
        assert result.arguments[0].option_name == "-S"
        
        # 检查配置选项
        assert result.arguments[1].node_type == ArgType.OPTION
        assert result.arguments[1].option_name == "--config"
        assert result.arguments[1].values == ["custom.conf"]
        
        # 检查位置参数（目标包）
        assert result.arguments[2].node_type == ArgType.POSITIONAL
        assert result.arguments[2].option_name == "targets"
        assert result.arguments[2].values == ["vim", "git"]
    
    def test_parse_combined_flags_with_config(self):
        """测试使用配置解析组合标志"""
        config = ParserConfig(
            parser_type=ParserType.GETOPT,
            program_name="tar",
            arguments=[
                ArgumentConfig(name="gzip", opt=["-z"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="extract", opt=["-x"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="verbose", opt=["-v"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="file", opt=["-f"], nargs=ArgumentCount('1')),  # 必须有1个值
                ArgumentConfig(name="target", opt=[], nargs=ArgumentCount.ZERO_OR_ONE),
            ]
        )
        parser = GetoptParser(config)
        
        args = ["tar", "-zxvf", "archive.tar.gz"]
        result = parser.parse(args)
        
        assert result.name == "tar"
        
        # 检查组合标志被正确解析
        found_flags = {
            arg.option_name: arg for arg in result.arguments 
            if arg.node_type == ArgType.FLAG
        }
        
        # 应该只有 -z, -x, -v 是标志
        assert "-z" in found_flags
        assert "-x" in found_flags  
        assert "-v" in found_flags
        # -f 不是标志，是选项，所以不应该在 found_flags 中
        
        # 检查 -f 选项
        found_options = {
            arg.option_name: arg for arg in result.arguments 
            if arg.node_type == ArgType.OPTION
        }
        assert "-f" in found_options
        assert found_options["-f"].values == ["archive.tar.gz"]
    
    def test_parse_tar_with_separator_and_paths(self):
        """测试解析 tar 命令带分隔符和路径参数"""
        config = ParserConfig(
            parser_type=ParserType.GETOPT,
            program_name="tar",
            arguments=[
                ArgumentConfig(name="gzip", opt=["-z"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="extract", opt=["-x"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="verbose", opt=["-v"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="file", opt=["-f"], nargs=ArgumentCount('1')),  # 必须有1个值
                ArgumentConfig(name="targets", opt=[], nargs=ArgumentCount.ZERO_OR_MORE),  # 额外参数
            ]
        )
        parser = GetoptParser(config)
        
        args = ["tar", "-zxvf", "foo.tar.gz", "--", "path_1", "path_2"]
        result = parser.parse(args)
        
        assert result.name == "tar"
        # 修正：应该是 6 个参数（3个标志 + 1个选项 + 2个额外参数）
        assert len(result.arguments) == 6
        
        # 检查组合标志
        found_flags = {
            arg.option_name: arg for arg in result.arguments 
            if arg.node_type == ArgType.FLAG
        }
        
        assert "-z" in found_flags
        assert "-x" in found_flags  
        assert "-v" in found_flags
        
        # 检查 -f 选项
        found_options = {
            arg.option_name: arg for arg in result.arguments 
            if arg.node_type == ArgType.OPTION
        }
        assert "-f" in found_options
        assert found_options["-f"].values == ["foo.tar.gz"]
        
        # 检查额外参数（在 -- 之后）
        extra_args = [
            arg for arg in result.arguments 
            if arg.node_type == ArgType.EXTRA
        ]
        assert len(extra_args) == 2
        assert extra_args[0].values == ["path_1"]
        assert extra_args[1].values == ["path_2"]
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_validate_command(self):
        """测试命令验证"""
        config = self._create_pacman_config()
        parser = GetoptParser(config)
        
        # 有效命令 - 应该包含所有必需参数
        args = ["pacman", "-S", "--config", "custom.conf", "vim", "git"]
        result = parser.parse(args)
        assert parser.validate(result) == True
        
        # 缺少必需参数（config 是必需的）
        args = ["pacman", "-S", "vim"]
        result = parser.parse(args)
        assert parser.validate(result) == False  # 这应该是 False
        
        # 缺少必需参数（targets 是 ONE_OR_MORE）
        args = ["pacman", "-S"]
        result = parser.parse(args)
        assert parser.validate(result) == False


if __name__ == "__main__":
    log.set_level(log.LogLevel.DEBUG)
    pytest.main([__file__, "-v"])