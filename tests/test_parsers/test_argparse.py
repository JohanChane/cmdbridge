# test/test_parsers/test_argparse.py
import sys
from pathlib import Path

from parsers.factory import ParserFactory
from parsers.types import ParserConfig, SyntaxTree, ArgNode, ArgType


class TestArgparseParser:
    """Test Argparse Parser"""
    
    def _create_apt_config(self):
        """创建 apt 配置"""
        return [
            ParserConfig(
                name="help",
                arg_name="help",
                type=ArgType.FLAG,
                long_opt="--help"
            ),
            ParserConfig(
                name="install",
                arg_name="targets", 
                type=ArgType.SUB_CMD,
                nargs="*"
            ),
            ParserConfig(
                name="search",
                arg_name="targets",
                type=ArgType.SUB_CMD, 
                nargs="*"
            ),
            ParserConfig(
                name="list",
                arg_name="targets",
                type=ArgType.SUB_CMD, 
                nargs="*",
                sub_args=[
                    ParserConfig(
                        name="installed",
                        arg_name="installed_only",
                        type=ArgType.FLAG,
                        long_opt="--installed"
                    )
                ]
            )
        ]
    
    def test_global_flag(self):
        """测试全局标志"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        result = parser.parse(["apt", "--help"])
        
        assert result['command_name'] == "apt"
        assert len(result['argument_nodes']) == 1
        assert result['argument_nodes'][0].name == "--help"
        assert result['argument_nodes'][0].type == ArgType.FLAG

    def test_sub_command(self):
        """测试子命令"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        result = parser.parse(["apt", "install", "vim", "git"])
        
        assert result['command_name'] == "apt"
        assert len(result['argument_nodes']) == 1
        sub_cmd = result['argument_nodes'][0]
        assert sub_cmd.name == "install"
        assert sub_cmd.type == ArgType.SUB_CMD
        assert sub_cmd.values == ["vim", "git"]

    def test_sub_command_with_flag(self):
        """测试带标志的子命令"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        result = parser.parse(["apt", "list", "--installed", "vim"])
        
        assert result['command_name'] == "apt"
        assert len(result['argument_nodes']) == 1
        sub_cmd = result['argument_nodes'][0]
        assert sub_cmd.name == "list"
        assert sub_cmd.type == ArgType.SUB_CMD
        assert sub_cmd.values == ["vim"]
        assert len(sub_cmd.args) == 1
        assert sub_cmd.args[0].name == "--installed"

    def test_sub_command_alias(self):
        """测试子命令别名"""
        configs = [
            ParserConfig(
                name="remove",
                arg_name="targets",
                type=ArgType.SUB_CMD,
                nargs="*",
                aliases=["rm", "uninstall"]
            )
        ]
        
        parser = ParserFactory.create_parser("argparse", configs)
        
        # 测试别名
        result = parser.parse(["apt", "rm", "vim"])
        assert result['command_name'] == "apt"
        assert result['argument_nodes'][0].name == "remove"
        assert result['argument_nodes'][0].values == ["vim"]

    def test_mixed_global_and_sub_command(self):
        """测试混合全局和子命令"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        result = parser.parse(["apt", "--help", "install"])
        
        assert result['command_name'] == "apt"
        assert len(result['argument_nodes']) == 2
        assert result['argument_nodes'][0].name == "--help"
        assert result['argument_nodes'][1].name == "install"

    def test_extra_args(self):
        """测试额外参数"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        result = parser.parse(["apt", "search", "vim", "--", "extra", "args"])
        
        assert result['command_name'] == "apt"
        assert result['extra_content'] == "extra args"
        assert len(result['argument_nodes']) == 1
        assert result['argument_nodes'][0].name == "search"

    def test_extra_args_with_unknown_option(self):
        """测试额外参数中包含未知选项（应该不影响）"""
        configs = self._create_apt_config()
        parser = ParserFactory.create_parser("argparse", configs)
        
        # -- 之后的未知选项应该被当作额外内容，不会报错
        result = parser.parse(["apt", "install", "vim", "--", "-X", "unknown"])
        
        assert result['command_name'] == "apt"
        assert result['extra_content'] == "-X unknown"
        assert len(result['argument_nodes']) == 1
        assert result['argument_nodes'][0].name == "install"

    def test_sub_command_with_sub_args(self):
        """测试子命令的子参数（只有 Argparse 有子参数概念）"""
        configs = [
            ParserConfig(
                name="install",
                arg_name="targets", 
                type=ArgType.SUB_CMD,
                nargs="*",
                sub_args=[
                    ParserConfig(
                        name="force",
                        arg_name="force_flag",
                        type=ArgType.FLAG,
                        long_opt="--force"
                    ),
                    ParserConfig(
                        name="dry_run",
                        arg_name="dry_run_flag", 
                        type=ArgType.FLAG,
                        long_opt="--dry-run"
                    )
                ]
            )
        ]
        
        parser = ParserFactory.create_parser("argparse", configs)
        result = parser.parse(["apt", "install", "vim", "--force", "--dry-run"])
        
        assert result['command_name'] == "apt"
        assert len(result['argument_nodes']) == 1
        sub_cmd = result['argument_nodes'][0]
        assert sub_cmd.name == "install"
        assert sub_cmd.type == ArgType.SUB_CMD
        assert sub_cmd.values == ["vim"]
        assert len(sub_cmd.args) == 2
        assert sub_cmd.args[0].name == "--force"
        assert sub_cmd.args[1].name == "--dry-run"