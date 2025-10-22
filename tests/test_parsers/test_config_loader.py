"""
配置加载器测试
"""

import pytest
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from parsers.config_loader import ConfigLoader, load_parser_config_from_data, load_parser_config_from_file
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig


class TestConfigLoader:
    """配置加载器测试类"""
    
    def test_load_apt_config_from_data(self):
        """测试从数据加载 apt 配置"""
        print("🔧 开始测试：从数据加载 apt 配置")
        config_data = {
            "apt": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "apt"
                },
                "arguments": [
                    {
                        "name": "help",
                        "opt": ["-h", "--help"],
                        "nargs": "0"
                    }
                ],
                "sub_commands": [
                    {
                        "name": "install",
                        "arguments": [
                            {
                                "name": "packages",
                                "nargs": "+"
                            }
                        ]
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        config = loader.load_parser_config("apt")
        
        assert isinstance(config, ParserConfig)
        assert config.parser_type == ParserType.ARGPARSE
        assert config.program_name == "apt"
        assert len(config.arguments) == 1
        assert len(config.sub_commands) == 1
        assert config.sub_commands[0].name == "install"
        
        # 测试便捷函数
        config2 = load_parser_config_from_data(config_data, "apt")
        assert config2.program_name == "apt"
        print("✅ 从数据加载 apt 配置测试通过")
    
    def test_load_pacman_config_from_data(self):
        """测试从数据加载 pacman 配置"""
        print("🔧 开始测试：从数据加载 pacman 配置")
        config_data = {
            "pacman": {
                "parser_config": {
                    "parser_type": "getopt",
                    "program_name": "pacman"
                },
                "arguments": [
                    {
                        "name": "help",
                        "opt": ["-h", "--help"],
                        "nargs": "0"
                    },
                    {
                        "name": "targets",
                        "nargs": "+"
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        config = loader.load_parser_config("pacman")
        
        assert config.parser_type == ParserType.GETOPT
        assert config.program_name == "pacman"
        assert len(config.arguments) == 2
        
        help_arg = config.arguments[0]
        assert help_arg.name == "help"
        assert help_arg.opt == ["-h", "--help"]
        assert help_arg.nargs.spec == "0"
        print("✅ 从数据加载 pacman 配置测试通过")
    
    def test_missing_program_section(self):
        """测试缺少程序配置部分"""
        print("🔧 开始测试：缺少程序配置部分")
        config_data = {
            "other_program": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "other"
                }
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="配置文件中缺少 apt 部分"):
            loader.load_parser_config("apt")
        print("✅ 缺少程序配置部分测试通过")
    
    def test_missing_parser_config_section(self):
        """测试缺少解析器配置部分"""
        print("🔧 开始测试：缺少解析器配置部分")
        config_data = {
            "apt": {
                "arguments": [
                    {"name": "help", "opt": ["-h", "--help"], "nargs": "0"}
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="配置文件中缺少 apt.parser_config 部分"):
            loader.load_parser_config("apt")
        print("✅ 缺少解析器配置部分测试通过")
    
    def test_invalid_parser_type(self):
        """测试无效的解析器类型"""
        print("🔧 开始测试：无效的解析器类型")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "invalid_type",
                    "program_name": "test"
                }
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="不支持的解析器类型"):
            loader.load_parser_config("test")
        print("✅ 无效的解析器类型测试通过")
    
    def test_missing_parser_type(self):
        """测试缺少 parser_type 配置"""
        print("🔧 开始测试：缺少 parser_type 配置")
        config_data = {
            "test": {
                "parser_config": {
                    "program_name": "test"
                }
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="缺少 parser_type 配置"):
            loader.load_parser_config("test")
        print("✅ 缺少 parser_type 配置测试通过")
    
    def test_argument_missing_nargs(self):
        """测试参数配置缺少 nargs"""
        print("🔧 开始测试：参数配置缺少 nargs")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "test"
                },
                "arguments": [
                    {
                        "name": "help",
                        "opt": ["-h", "--help"]
                        # 缺少 nargs
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="参数配置中缺少 nargs"):
            loader.load_parser_config("test")
        print("✅ 参数配置缺少 nargs 测试通过")
    
    def test_invalid_nargs_value(self):
        """测试无效的 nargs 值"""
        print("🔧 开始测试：无效的 nargs 值")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "test"
                },
                "arguments": [
                    {
                        "name": "help",
                        "opt": ["-h", "--help"],
                        "nargs": "invalid"
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="不支持的 nargs 值"):
            loader.load_parser_config("test")
        print("✅ 无效的 nargs 值测试通过")
    
    def test_exactly_n_missing_count(self):
        """测试 nargs='n' 时缺少 count - 现在 'n' 是无效的"""
        print("🔧 开始测试：nargs='n' 时缺少 count")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "test"
                },
                "arguments": [
                    {
                        "name": "files",
                        "opt": ["-f", "--files"],
                        "nargs": "n"
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="不支持的 nargs 值"):
            loader.load_parser_config("test")
        print("✅ nargs='n' 时缺少 count 测试通过")
    
    def test_subcommand_missing_name(self):
        """测试子命令配置缺少 name"""
        print("🔧 开始测试：子命令配置缺少 name")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "test"
                },
                "sub_commands": [
                    {
                        # 缺少 name
                        "arguments": [
                            {"name": "packages", "nargs": "+"}
                        ]
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        
        with pytest.raises(ValueError, match="子命令配置中缺少 name"):
            loader.load_parser_config("test")
        print("✅ 子命令配置缺少 name 测试通过")
    
    def test_argument_with_required_field(self):
        """测试带 required 字段的参数配置"""
        print("🔧 开始测试：带 required 字段的参数配置")
        config_data = {
            "test": {
                "parser_config": {
                    "parser_type": "getopt",
                    "program_name": "test"
                },
                "arguments": [
                    {
                        "name": "required_arg",
                        "opt": ["-r", "--required"],
                        "nargs": "1",
                        "required": True
                    },
                    {
                        "name": "optional_arg", 
                        "opt": ["-o", "--optional"],
                        "nargs": "?",
                        "required": False
                    },
                    {
                        "name": "default_arg",
                        "opt": ["-d", "--default"],
                        "nargs": "*"
                        # 没有指定 required，应该默认为 False
                    }
                ]
            }
        }
        
        loader = ConfigLoader(config_data)
        config = loader.load_parser_config("test")
        
        assert len(config.arguments) == 3
        assert config.arguments[0].name == "required_arg"
        assert config.arguments[0].required == True
        assert config.arguments[1].name == "optional_arg" 
        assert config.arguments[1].required == False
        assert config.arguments[2].name == "default_arg"
        assert config.arguments[2].required == False  # 默认值
        print("✅ 带 required 字段的参数配置测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])