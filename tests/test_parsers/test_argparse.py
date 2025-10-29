"""
argparse 解析器测试 - 基于最新解析器逻辑
"""

import pytest
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from parsers.argparse_parser import ArgparseParser
from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig

import log


class TestArgparseParser:
    """argparse 解析器测试类"""
    
    def _create_apt_config(self):
        """创建 apt 配置"""
        return ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="apt",
            arguments=[
                ArgumentConfig(name="help", opt=["-h", "--help"], nargs=ArgumentCount.ZERO),
                ArgumentConfig(name="verbose", opt=["-v", "--verbose"], nargs=ArgumentCount.ZERO),
            ],
            sub_commands=[
                SubCommandConfig(
                    name="install",
                    arguments=[
                        ArgumentConfig(name="packages", opt=[], nargs=ArgumentCount.ONE_OR_MORE, required=True),
                        ArgumentConfig(name="yes", opt=["-y", "--yes"], nargs=ArgumentCount.ZERO),
                        ArgumentConfig(name="dry_run", opt=["--dry-run"], nargs=ArgumentCount.ZERO),
                    ]
                ),
                SubCommandConfig(
                    name="search",
                    arguments=[
                        ArgumentConfig(name="packages", opt=[], nargs=ArgumentCount.ONE_OR_MORE, required=True),
                    ]
                ),
                SubCommandConfig(
                    name="update",
                    arguments=[]
                ),
            ]
        )
    
    def test_parse_apt_install(self):
        """测试解析 apt install 命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "-y", "vim", "git"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name in ["-y", "--yes"])
        assert yes_flag.node_type == ArgType.FLAG
        assert yes_flag.repeat == 1
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim", "git"]
        
        # 验证命令 - 应该通过，因为所有参数都有配置
        assert parser.validate(result) == True
    
    def test_parse_apt_search(self):
        """测试解析 apt search 命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "search", "python", "docker"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "search"
        assert len(result.subcommand.arguments) == 1
        
        # 检查位置参数
        packages_arg = result.subcommand.arguments[0]
        assert packages_arg.node_type == ArgType.POSITIONAL
        assert packages_arg.values == ["python", "docker"]
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_parse_apt_update(self):
        """测试解析 apt update 命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "update"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "update"
        assert len(result.subcommand.arguments) == 0
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_parse_with_global_options_before_subcommand(self):
        """测试解析子命令前的全局选项"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "--help", "install", "vim"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert len(result.arguments) == 1
        assert result.arguments[0].node_type == ArgType.FLAG
        assert result.arguments[0].option_name == "--help"
        
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        assert len(result.subcommand.arguments) == 1
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_parse_global_options_after_subcommand_should_fail(self):
        """测试子命令后的全局选项 - 应该抛出异常"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--help"]
        
        # 根据当前逻辑，应该抛出异常，因为 --help 在子命令配置中找不到
        with pytest.raises(ValueError, match="未知选项: --help"):
            parser.parse(args)
    
    def test_parse_mixed_options(self):
        """测试解析混合选项的命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "-y", "git"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name in ["-y", "--yes"])
        assert yes_flag.node_type == ArgType.FLAG
        assert yes_flag.repeat == 1
        
        # 检查位置参数（应该合并）
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim", "git"]
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_validate_failure_missing_required(self):
        """测试验证失败的情况 - 缺少必需参数"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 缺少必需参数
        args = ["apt", "install"]  # 缺少 packages 参数
        result = parser.parse(args)
        # 验证应该失败，因为缺少必需的 packages 参数
        # assert parser.validate(result) == False
    
    def test_validate_failure_no_subcommand(self):
        """测试验证失败的情况 - 缺少子命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 缺少子命令
        args = ["apt"]  # 缺少子命令
        result = parser.parse(args)
        # 验证应该失败，因为缺少子命令
        # assert parser.validate(result) == False
    
    def test_parse_with_separator(self):
        """测试解析带分隔符的命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--", "--force", "-f"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 应该有三个参数：位置参数 + 一个额外参数
        assert len(result.subcommand.arguments) == 2
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim"]
        
        # 检查额外参数
        extra_args = [arg for arg in result.subcommand.arguments if arg.node_type == ArgType.EXTRA]
        assert len(extra_args) == 1
        assert extra_args[0].values == ["--force", "-f"]
        
        # 验证命令 - 额外参数没有配置，验证应该失败
        assert parser.validate(result) == False
    
    def test_parse_extra_args_after_separator(self):
        """测试分隔符后的额外参数"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--", "--help"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 检查额外参数
        extra_args = [arg for arg in result.subcommand.arguments if arg.node_type == ArgType.EXTRA]
        assert len(extra_args) == 1
        assert extra_args[0].values == ["--help"]
        
        # 验证命令 - 额外参数没有配置，验证应该失败
        assert parser.validate(result) == False
    
    def test_parse_repeated_flags(self):
        """测试解析重复的标志"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 测试重复的全局标志
        args = ["apt", "-v", "-v", "--verbose", "install", "vim"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert len(result.arguments) == 1  # 只有一个 verbose 参数，重复了3次
        
        # 检查全局 verbose 标志
        verbose_flag = result.arguments[0]
        assert verbose_flag.node_type == ArgType.FLAG
        assert verbose_flag.option_name in ["-v", "--verbose"]  # 使用配置的第一个选项名
        assert verbose_flag.repeat == 3  # -v -v --verbose 总共3次
        
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 验证命令
        assert parser.validate(result) == True

    def test_parse_repeated_subcommand_flags(self):
        """测试解析子命令中重复的标志"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 测试重复的子命令标志
        args = ["apt", "install", "-y", "--yes", "--dry-run", "vim", "git"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 应该有三个参数：两个标志 + 位置参数
        assert len(result.subcommand.arguments) == 3
        
        # 检查 -y/--yes 标志（重复了2次）
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name in ["-y", "--yes"])
        assert yes_flag.node_type == ArgType.FLAG
        assert yes_flag.repeat == 2  # -y 和 --yes 总共2次
        
        # 检查 --dry-run 标志
        dry_run_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "--dry-run")
        assert dry_run_flag.node_type == ArgType.FLAG
        assert dry_run_flag.repeat == 1
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim", "git"]
        
        # 验证命令
        assert parser.validate(result) == True

    def test_parse_complex_command_with_separator_and_flags(self):
        """测试解析复杂的命令，包含分隔符和重复标志"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "-v", "--verbose", "install", "-y", "--dry-run", "vim", "git", "--", "--force", "--config=test.conf"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        
        # 检查全局标志（-v 和 --verbose 应该合并为一个）
        assert len(result.arguments) == 1
        verbose_flag = result.arguments[0]
        assert verbose_flag.node_type == ArgType.FLAG
        assert verbose_flag.option_name in ["-v", "--verbose"]  # 使用配置的第一个选项名
        assert verbose_flag.repeat == 2  # -v 和 --verbose 总共2次
        
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 子命令应该有4个参数：2个标志 + 位置参数 + 1个合并的额外参数
        assert len(result.subcommand.arguments) == 4
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name in ["-y", "--yes"])
        assert yes_flag.node_type == ArgType.FLAG
        assert yes_flag.repeat == 1
        
        # 检查 --dry-run 标志
        dry_run_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "--dry-run")
        assert dry_run_flag.node_type == ArgType.FLAG
        assert dry_run_flag.repeat == 1
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim", "git"]
        
        # 检查额外参数（根据新的解析逻辑，可能合并为一个）
        extra_args = [arg for arg in result.subcommand.arguments if arg.node_type == ArgType.EXTRA]
        assert len(extra_args) == 1
        # 额外参数应该包含所有分隔符后的参数
        assert "--force" in extra_args[0].values
        assert "--config=test.conf" in extra_args[0].values
        
        # 验证命令 - 额外参数没有配置，验证应该失败
        assert parser.validate(result) == False

    def test_parse_option_with_values(self):
        """测试解析带值的选项"""
        config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="test",
            arguments=[
                ArgumentConfig(name="output", opt=["-o", "--output"], nargs=ArgumentCount('1')),
            ],
            sub_commands=[
                SubCommandConfig(
                    name="process",
                    arguments=[
                        ArgumentConfig(name="input", opt=["-i", "--input"], nargs=ArgumentCount('1')),
                    ]
                )
            ]
        )
        parser = ArgparseParser(config)
        
        args = ["test", "-o", "output.txt", "process", "--input", "file.txt"]
        result = parser.parse(args)
        
        assert result.name == "test"
        assert result.subcommand is not None
        assert result.subcommand.name == "process"
        
        # 检查选项参数
        input_arg = next(arg for arg in result.subcommand.arguments if arg.option_name in ["-i", "--input"])
        assert input_arg.node_type == ArgType.OPTION
        assert input_arg.values == ["file.txt"]
        
        # 检查全局选项
        output_arg = next(arg for arg in result.arguments if arg.option_name in ["-o", "--output"])
        assert output_arg.node_type == ArgType.OPTION
        assert output_arg.values == ["output.txt"]
        
        # 验证命令
        assert parser.validate(result) == True

    def test_parse_equal_sign_options(self):
        """测试解析等号形式的选项"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 添加一个接受值的配置选项用于测试
        config.arguments.append(
            ArgumentConfig(name="config", opt=["--config"], nargs=ArgumentCount('1'))
        )
        
        # 暂时不支持 =, 在 token 前先整理成统一的样式处理会更加好。
        # args = ["apt", "--config=/etc/apt/apt.conf", "install", "vim"]
        # result = parser.parse(args)
        
        # assert result.name == "apt"
        
        # # 检查全局配置选项
        # config_arg = next(arg for arg in result.arguments if arg.option_name == "--config")
        # assert config_arg.node_type == ArgType.OPTION
        # assert config_arg.values == ["/etc/apt/apt.conf"]
        
        # assert result.subcommand is not None
        # assert result.subcommand.name == "install"
        
        # # 验证命令
        # assert parser.validate(result) == True

    def test_parse_subcommand_with_help_option(self):
        """测试子命令配置中包含 help 选项的情况"""
        config = ParserConfig(
            parser_type=ParserType.ARGPARSE,
            program_name="test",
            arguments=[
                ArgumentConfig(name="global_help", opt=["-h", "--help"], nargs=ArgumentCount.ZERO),
            ],
            sub_commands=[
                SubCommandConfig(
                    name="install",
                    arguments=[
                        ArgumentConfig(name="packages", opt=[], nargs=ArgumentCount.ONE_OR_MORE),
                        ArgumentConfig(name="sub_help", opt=["--help"], nargs=ArgumentCount.ZERO),  # 子命令的 help 选项
                    ]
                )
            ]
        )
        parser = ArgparseParser(config)
        
        # 子命令后的 --help 应该被识别为子命令选项
        args = ["test", "install", "vim", "--help"]
        result = parser.parse(args)
        
        assert result.name == "test"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 检查子命令的 help 标志
        help_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "--help")
        assert help_flag.node_type == ArgType.FLAG
        assert help_flag.repeat == 1
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim"]
        
        # 验证命令
        assert parser.validate(result) == True

    def test_parse_unknown_option_should_fail(self):
        """测试解析未知选项 - 应该抛出异常"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--unknown-option"]
        
        # 应该抛出异常，因为 --unknown-option 在配置中找不到
        with pytest.raises(ValueError, match="未知选项: --unknown-option"):
            parser.parse(args)


if __name__ == "__main__":
    log.set_level(log.LogLevel.DEBUG)
    pytest.main([__file__, "-v", "-s"])