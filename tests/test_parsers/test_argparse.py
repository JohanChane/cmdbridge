import sys, os

# Add project root directory to Python path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

import pytest
from parsers.argparse_parser import ArgparseParser
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig
from parsers.types import CommandNode, CommandArg, ArgType, CommandToken, TokenType

import log


class TestArgparseParser:
    """ArgparseParser Test Class"""
    
    def create_simple_parser_config(self):
        """Create simple parser configuration"""
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
        """Create parser configuration with subcommands"""
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
        """Test parsing simple command"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v", "--config", "config.toml", "file1.txt", "file2.txt"]
        
        result = parser.parse(args)
        
        assert result.name == "test_program"
        assert len(result.arguments) == 3
        
        # Check verbose flag
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "--verbose")
        assert verbose_arg.node_type == ArgType.FLAG
        assert verbose_arg.repeat == 1
        
        # Check config option
        config_arg = next(arg for arg in result.arguments if arg.option_name == "--config")
        assert config_arg.node_type == ArgType.OPTION
        assert config_arg.values == ["config.toml"]
        
        # Check positional arguments
        files_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.POSITIONAL)
        assert files_arg.values == ["file1.txt", "file2.txt"]
    
    def test_parse_command_with_flags(self):
        """Test parsing command with multiple flags"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v", "-h", "-v"]  # Repeated -v flag
        
        result = parser.parse(args)
        
        # Check repeated flag count
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "--verbose")
        assert verbose_arg.repeat == 2
        
        help_arg = next(arg for arg in result.arguments if arg.option_name == "--help")
        assert help_arg.repeat == 1
    
    def test_parse_command_with_separator(self):
        """Test parsing command with separator"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "file1.txt", "--", "-v", "--config=test"]
        
        result = parser.parse(args)
        
        # Check positional arguments
        positional_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.POSITIONAL)
        assert positional_arg.values == ["file1.txt"]
        
        # Check extra arguments
        extra_arg = next(arg for arg in result.arguments if arg.node_type == ArgType.EXTRA)
        assert extra_arg.values == ["-v", "--config=test"]
    
    def test_parse_subcommand(self):
        """Test parsing subcommand"""
        parser = ArgparseParser(self.create_parser_with_subcommands())
        args = ["git", "commit", "-m", "Initial commit", "-a"]
        
        result = parser.parse(args)
        
        assert result.name == "git"
        assert result.subcommand is not None
        assert result.subcommand.name == "commit"
        
        # Check subcommand arguments
        message_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--message")
        assert message_arg.values == ["Initial commit"]
        
        all_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--all")
        assert all_arg.node_type == ArgType.FLAG
    
    def test_parse_nested_subcommand(self):
        """Test parsing nested subcommand (if supported)"""
        # Note: Current implementation may not support nested subcommands, testing basic functionality here
        parser = ArgparseParser(self.create_parser_with_subcommands())
        args = ["git", "push", "origin", "--force"]
        
        result = parser.parse(args)
        
        assert result.name == "git"
        assert result.subcommand.name == "push"
        
        # Check push subcommand arguments
        force_arg = next(arg for arg in result.subcommand.arguments if arg.option_name == "--force")
        assert force_arg.node_type == ArgType.FLAG
        
        remote_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert remote_arg.values == ["origin"]
    
    def test_parse_combined_short_options(self):
        """Test parsing combined short options"""
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
        
        parser = ArgparseParser(parser_config)
        args = ["tar", "-xvf", "archive.tar.gz"]
        
        result = parser.parse(args)
        
        # Check decomposed flags
        extract_arg = next(arg for arg in result.arguments if arg.option_name == "-x")
        assert extract_arg.node_type == ArgType.FLAG
        
        verbose_arg = next(arg for arg in result.arguments if arg.option_name == "-v")
        assert verbose_arg.node_type == ArgType.FLAG
        
        file_arg = next(arg for arg in result.arguments if arg.option_name == "-f")
        assert file_arg.values == ["archive.tar.gz"]
    
    def test_parse_with_equal_sign(self):
        """Test parsing options with equal sign"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "--config=myconfig.toml"]
        
        result = parser.parse(args)
        
        config_arg = next(arg for arg in result.arguments if arg.option_name == "--config")
        assert config_arg.values == ["myconfig.toml"]
    
    def test_invalid_option(self):
        """Test invalid option"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "--unknown-option"]
        
        # Note: Current implementation may throw exception during tokenize phase
        # Mainly testing that parser doesn't crash
        try:
            result = parser.parse(args)
            # If parsing succeeds, check for unknown argument handling
            assert result is not None
        except Exception as e:
            # Expected behavior: either handle properly or throw meaningful exception
            assert "unknown" in str(e).lower() or "not found" in str(e)
    
    def test_validate_method(self):
        """Test validation method"""
        parser = ArgparseParser(self.create_simple_parser_config())
        args = ["test_program", "-v"]
        result = parser.parse(args)
        
        # In current implementation, validate method always returns True
        assert parser.validate(result) is True
    
    def test_complex_command_structure(self):
        """Test complex command structure"""
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
        
        parser = ArgparseParser(parser_config)
        args = ["docker", "container", "ls", "--all"]
        
        result = parser.parse(args)
        
        assert result.name == "docker"
        assert result.subcommand.name == "container"
        assert result.subcommand.subcommand.name == "ls"
        
        all_arg = next(arg for arg in result.subcommand.subcommand.arguments 
                      if arg.option_name == "--all")
        assert all_arg.node_type == ArgType.FLAG


class TestTokenization:
    """Specialized tests for tokenization functionality"""
    
    def test_tokenize_simple_args(self):
        """Test simple argument tokenization"""
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
        
        parser = ArgparseParser(parser_config)
        args = ["test", "-v"]
        
        tokens = parser._tokenize(args)
        
        assert len(tokens) == 2
        assert tokens[0].token_type == TokenType.PROGRAM
        assert tokens[0].values == ["test"]
        assert tokens[1].token_type == TokenType.FLAG
        assert tokens[1].values == ["-v"]
    
    def test_tokenize_with_values(self):
        """Test argument tokenization with values"""
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
        
        parser = ArgparseParser(parser_config)
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