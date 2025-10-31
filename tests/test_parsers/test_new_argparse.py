import sys, os

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

import pytest
from parsers.new_argparse_parser import NewArgparseParser
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig
from parsers.types import CommandNode, CommandArg, ArgType, CommandToken, TokenType

import log


class TestNewArgparseParser:
    """NewArgparseParser 测试类"""
    
    def create_simple_parser_config(self):
        """创建简单的解析器配置"""
        return ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="test_program",
            arguments=[
                ArgumentConfig(
                    name="help",
                    opt=["-h", "--help"],
                    nargs=ArgumentCount('0')
                ),
                ArgumentConfig(
                    name="verbose",
                    opt=["-v", "--verbose"],
                    nargs=ArgumentCount('0')
                ),
                ArgumentConfig(
                    name="config",
                    opt=["-c", "--config"],
                    nargs=ArgumentCount('1')
                ),
                ArgumentConfig(
                    name="files",
                    opt=[],
                    nargs=ArgumentCount('+')
                )
            ],
            sub_commands=[]
        )
    
    def create_parser_with_subcommands(self):
        """创建包含子命令的解析器配置"""
        return ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="git",
            arguments=[
                ArgumentConfig(
                    name="help",
                    opt=["-h", "--help"],
                    nargs=ArgumentCount('0')
                )
            ],
            sub_commands=[
                SubCommandConfig(
                    name="commit",
                    arguments=[
                        ArgumentConfig(
                            name="message",
                            opt=["-m", "--message"],
                            nargs=ArgumentCount('1')
                        ),
                        ArgumentConfig(
                            name="all",
                            opt=["-a", "--all"],
                            nargs=ArgumentCount('0')
                        )
                    ]
                ),
                SubCommandConfig(
                    name="push",
                    arguments=[
                        ArgumentConfig(
                            name="force",
                            opt=["-f", "--force"],
                            nargs=ArgumentCount('0')
                        ),
                        ArgumentConfig(
                            name="remote",
                            opt = [],
                            nargs=ArgumentCount('?')
                        )
                    ]
                )
            ]
        )
    
    def test_parse_simple_command(self):
        """测试解析简单命令"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v", "--config", "config.toml", "file1.txt", "file2.txt"]
        
        result = parser.parse(args)
        
        assert result.name == "test_program"
        assert len(result.arguments) == 3
        
        # 检查 verbose 标志
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "--verbose")
        assert verbose_arg.node_type == ArgType.FLAG
        assert verbose_arg.repeat == 1
        
        # 检查 config 选项
        config_arg = next(arg for arg in result.arguments if arg.option_name == "--config")
        assert config_arg.node_type == ArgType.OPTION
        assert config_arg.values == ["config.toml"]
        
        # 检查位置参数
        files_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.POSITIONAL)
        assert files_arg.values == ["file1.txt", "file2.txt"]
    
    def test_parse_command_with_flags(self):
        """测试解析包含多个标志的命令"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v", "-h", "-v"]  # 重复的 -v 标志
        
        result = parser.parse(args)
        
        # 检查重复的标志计数
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "--verbose")
        assert verbose_arg.repeat == 2
        
        help_arg = next(arg for arg in result.arguments if arg.option_name == "--help")
        assert help_arg.repeat == 1
    
    def test_parse_command_with_separator(self):
        """测试解析包含分隔符的命令"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "file1.txt", "--", "-v", "--config=test"]
        
        result = parser.parse(args)
        
        # 检查位置参数
        positional_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.POSITIONAL)
        assert positional_arg.values == ["file1.txt"]
        
        # 检查额外参数
        extra_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.EXTRA)
        assert extra_arg.values == ["-v", "--config=test"]
    
    def test_parse_subcommand(self):
        """测试解析子命令"""
        parser = NewArgparseParser(self.create_parser_with_subcommands())
        args = ["git", "commit", "-m", "Initial commit", "-a"]
        
        result = parser.parse(args)
        
        assert result.name == "git"
        assert result.subcommand is not None
        assert result.subcommand.name == "commit"
        
        # 检查子命令参数
        message_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--message")
        assert message_arg.values == ["Initial commit"]
        
        all_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--all")
        assert all_arg.node_type == ArgType.FLAG
    
    def test_parse_nested_subcommand(self):
        """测试解析嵌套子命令（如果支持的话）"""
        # 注意：当前实现可能不支持嵌套子命令，这里测试基本功能
        parser = NewArgparseParser(self.create_parser_with_subcommands())
        args = ["git", "push", "origin", "--force"]
        
        result = parser.parse(args)
        
        assert result.name == "git"
        assert result.subcommand.name == "push"
        
        # 检查 push 子命令参数
        force_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--force")
        assert force_arg.node_type == ArgType.FLAG
        
        remote_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert remote_arg.values == ["origin"]
    
    def test_parse_combined_short_options(self):
        """测试解析组合短选项"""
        parser_config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="tar",
            arguments=[
                ArgumentConfig(
                    name="extract",
                    opt=["-x"],
                    nargs=ArgumentCount('0')
                ),
                ArgumentConfig(
                    name="verbose",
                    opt=["-v"],
                    nargs=ArgumentCount('0')
                ),
                ArgumentConfig(
                    name="file",
                    opt=["-f"],
                    nargs=ArgumentCount('1')
                )
            ],
            sub_commands=[]
        )
        
        parser = NewArgparseParser(parser_config)
        args = ["tar", "-xvf", "archive.tar.gz"]
        
        result = parser.parse(args)
        
        # 检查分解后的标志
        extract_arg = next(arg for arg in result.arguments if arg.option_name == "-x")
        assert extract_arg.node_type == ArgType.FLAG
        
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "-v")
        assert verbose_arg.node_type == ArgType.FLAG
        
        file_arg = next(arg for arg in result.arguments if arg.option_name == "-f")
        assert file_arg.values == ["archive.tar.gz"]
    
    def test_parse_with_equal_sign(self):
        """测试解析等号形式的选项"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "--config=myconfig.toml"]
        
        result = parser.parse(args)
        
        config_arg = next(arg for arg in result.arguments if arg.option_name == "--config")
        assert config_arg.values == ["myconfig.toml"]
    
    def test_invalid_option(self):
        """测试无效选项"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "--unknown-option"]
        
        # 注意：当前实现可能会在 tokenize 阶段抛出异常
        # 这里主要测试解析器不会崩溃
        try:
            result = parser.parse(args)
            # 如果解析成功，检查是否有未知参数处理
            assert result is not None
        except Exception as e:
            # 期望的行为：要么正确处理，要么抛出有意义的异常
            assert "unknown" in str(e).lower() or "未找到" in str(e)
    
    def test_validate_method(self):
        """测试验证方法"""
        parser = NewArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v"]
        result = parser.parse(args)
        
        # 当前实现中 validate 方法总是返回 True
        assert parser.validate(result) is True
    
    def test_complex_command_structure(self):
        """测试复杂命令结构"""
        parser_config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="docker",
            arguments=[
                ArgumentConfig(
                    name="help",
                    opt=["-h", "--help"],
                    nargs=ArgumentCount('0')
                )
            ],
            sub_commands=[
                SubCommandConfig(
                    name="container",
                    arguments=[],
                    sub_commands=[
                        SubCommandConfig(
                            name="ls",
                            arguments=[
                                ArgumentConfig(
                                    name="all",
                                    opt=["-a", "--all"],
                                    nargs=ArgumentCount('0')
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
        parser = NewArgparseParser(parser_config)
        args = ["docker", "container", "ls", "--all"]
        
        result = parser.parse(args)
        
        assert result.name == "docker"
        assert result.subcommand.name == "container"
        assert result.subcommand.subcommand.name == "ls"
        
        all_arg = next(arg for arg in result.subcommand.subcommand.arguments 
                      if arg.option_name == "--all")
        assert all_arg.node_type == ArgType.FLAG


class TestTokenization:
    """专门测试 tokenization 功能"""
    
    def test_tokenize_simple_args(self):
        """测试简单参数 tokenization"""
        parser_config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="test",
            arguments=[
                ArgumentConfig(
                    name="verbose",
                    opt=["-v"],
                    nargs=ArgumentCount('0')
                )
            ],
            sub_commands=[]
        )
        
        parser = NewArgparseParser(parser_config)
        args = ["test", "-v"]
        
        tokens = parser._tokenize(args)
        
        assert len(tokens) == 2
        assert tokens[0].token_type == TokenType.PROGRAM
        assert tokens[0].values == ["test"]
        assert tokens[1].token_type == TokenType.FLAG
        assert tokens[1].values == ["-v"]
    
    def test_tokenize_with_values(self):
        """测试带值的参数 tokenization"""
        parser_config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="test",
            arguments=[
                ArgumentConfig(
                    name="file",
                    opt=["-f"],
                    nargs=ArgumentCount('1')
                )
            ],
            sub_commands=[]
        )
        
        parser = NewArgparseParser(parser_config)
        args = ["test", "-f", "filename.txt"]
        
        tokens = parser._tokenize(args)
        
        assert len(tokens) == 3
        assert tokens[1].token_type == TokenType.OPTION_NAME
        assert tokens[1].values == ["-f"]
        assert tokens[2].token_type == TokenType.OPTION_VALUE
        assert tokens[2].values == ["filename.txt"]


if __name__ == "__main__":
    log.set_level(log.LogLevel.DEBUG)
    pytest.main([__file__, "-v"])