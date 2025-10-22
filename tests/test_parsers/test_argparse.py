"""
argparse 解析器测试
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
        assert len(result.subcommand.arguments) == 2
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "-y")
        assert yes_flag.node_type == ArgType.FLAG
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if not arg.option_name)
        assert packages_arg.node_type == ArgType.POSITIONAL
        assert packages_arg.values == ["vim", "git"]
        
        # 验证命令
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
    
    def test_parse_with_global_options(self):
        """测试解析带全局选项的命令"""
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
    
    def test_parse_mixed_options(self):
        """测试解析混合选项的命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "-y", "git"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        assert len(result.subcommand.arguments) == 2
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "-y")
        assert yes_flag.node_type == ArgType.FLAG
        
        # 检查位置参数（应该合并）
        packages_arg = next(arg for arg in result.subcommand.arguments if not arg.option_name)
        assert packages_arg.node_type == ArgType.POSITIONAL
        assert packages_arg.values == ["vim", "git"]
        
        # 验证命令
        assert parser.validate(result) == True
    
    def test_validate_failure(self):
        """测试验证失败的情况"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        # 缺少必需参数
        args = ["apt", "install"]
        result = parser.parse(args)
        assert parser.validate(result) == False
        
        # 缺少子命令
        args = ["apt"]
        result = parser.parse(args)
        assert parser.validate(result) == False
    
    def test_parse_with_separator(self):
        """测试解析带分隔符的命令"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--", "--force", "-f"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 应该有三个参数：位置参数 + 两个额外参数
        assert len(result.subcommand.arguments) == 3
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim"]
        
        # 检查额外参数
        extra_args = [arg for arg in result.subcommand.arguments if arg.node_type == ArgType.EXTRA]
        assert len(extra_args) == 2
        assert extra_args[0].values == ["--force"]
        assert extra_args[1].values == ["-f"]
        
        # 验证命令
        assert parser.validate(result) == True
    
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
        verbose_flag = next(arg for arg in result.arguments if arg.option_name in ["-v", "--verbose"])
        assert verbose_flag.node_type == ArgType.FLAG
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
        assert verbose_flag.option_name in ["-v", "--verbose"]
        assert verbose_flag.repeat == 2  # -v 和 --verbose 总共2次
        
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        
        # 子命令应该有5个参数：2个标志 + 位置参数 + 2个独立额外参数
        assert len(result.subcommand.arguments) == 5
        
        # 检查 -y 标志
        yes_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "-y")
        assert yes_flag.node_type == ArgType.FLAG
        assert yes_flag.repeat == 1
        
        # 检查 --dry-run 标志
        dry_run_flag = next(arg for arg in result.subcommand.arguments if arg.option_name == "--dry-run")
        assert dry_run_flag.node_type == ArgType.FLAG
        assert dry_run_flag.repeat == 1
        
        # 检查位置参数
        packages_arg = next(arg for arg in result.subcommand.arguments if arg.node_type == ArgType.POSITIONAL)
        assert packages_arg.values == ["vim", "git"]
        
        # 检查额外参数（应该保持独立）
        extra_args = [arg for arg in result.subcommand.arguments if arg.node_type == ArgType.EXTRA]
        assert len(extra_args) == 2
        assert extra_args[0].values == ["--force"]           # 独立额外参数
        assert extra_args[1].values == ["--config=test.conf"] # 独立额外参数
        
        # 验证命令
        assert parser.validate(result) == True

    def test_parse_global_options_after_subcommand(self):
        """测试子命令后的全局选项"""
        config = self._create_apt_config()
        parser = ArgparseParser(config)
        
        args = ["apt", "install", "vim", "--help"]
        result = parser.parse(args)
        
        assert result.name == "apt"
        
        # --help 是全局选项，应该在根节点
        assert len(result.arguments) == 1
        help_flag = result.arguments[0]
        assert help_flag.node_type == ArgType.FLAG
        assert help_flag.option_name == "--help"
        
        assert result.subcommand is not None
        assert result.subcommand.name == "install"
        assert len(result.subcommand.arguments) == 1
        
        # 验证命令
        assert parser.validate(result) == True


if __name__ == "__main__":
    log.set_level(log.LogLevel.DEBUG)
    pytest.main([__file__, "-v"])