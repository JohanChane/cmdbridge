#!/usr/bin/env python3
"""
测试配置加载器核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.config_loader import ConfigLoader, load_parser_config_from_data
from parsers.types import ParserType
import tempfile
import tomli_w


def test_basic_parser_config():
    """测试基本解析器配置加载"""
    print("=== 测试基本解析器配置 ===")
    
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
    parser_config = loader.load_parser_config("apt")
    
    # 验证基本属性
    assert parser_config.parser_type == ParserType.ARGPARSE
    assert parser_config.program_name == "apt"
    assert len(parser_config.arguments) == 1
    assert len(parser_config.sub_commands) == 1
    
    # 验证参数
    help_arg = parser_config.arguments[0]
    assert help_arg.name == "help"
    assert help_arg.opt == ["-h", "--help"]
    assert help_arg.nargs.spec == "0"
    assert help_arg.is_flag()
    
    # 验证子命令
    install_cmd = parser_config.sub_commands[0]
    assert install_cmd.name == "install"
    assert len(install_cmd.arguments) == 1
    assert install_cmd.arguments[0].name == "packages"
    assert install_cmd.arguments[0].nargs.spec == "+"
    
    print("✅ 基本解析器配置测试通过")


def test_id_and_include_functionality():
    """测试 ID 和 include_arguments_and_subcmds 功能"""
    print("\n=== 测试 ID 和 include 功能 ===")
    
    config_data = {
        "mufw": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "mufw"
            },
            "sub_commands": [
                {
                    "name": "allow",
                    "id": "subcmd_id_allow",
                    "arguments": [
                        {
                            "name": "port",
                            "opt": ["--port"],
                            "nargs": "1"
                        },
                        {
                            "name": "protocol", 
                            "opt": ["--proto"],
                            "nargs": "1"
                        }
                    ]
                },
                {
                    "name": "deny",
                    "include_arguments_and_subcmds": "subcmd_id_allow"
                }
            ]
        }
    }
    
    loader = ConfigLoader(config_data)
    parser_config = loader.load_parser_config("mufw")
    
    # 验证基本结构
    assert len(parser_config.sub_commands) == 2
    
    # 验证 allow 子命令
    allow_cmd = next(cmd for cmd in parser_config.sub_commands if cmd.name == "allow")
    assert len(allow_cmd.arguments) == 2
    assert allow_cmd.arguments[0].name == "port"
    assert allow_cmd.arguments[1].name == "protocol"
    
    # 验证 deny 子命令（应该包含 allow 的参数）
    deny_cmd = next(cmd for cmd in parser_config.sub_commands if cmd.name == "deny")
    assert len(deny_cmd.arguments) == 2
    assert deny_cmd.arguments[0].name == "port"
    assert deny_cmd.arguments[1].name == "protocol"
    
    print("✅ ID 和 include 功能测试通过")


def test_file_loading():
    """测试从文件加载配置"""
    print("\n=== 测试文件加载 ===")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
        config_data = {
            "file_test": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "file_test"
                },
                "arguments": [
                    {
                        "name": "file_arg",
                        "opt": ["-f", "--file"],
                        "nargs": "1"
                    }
                ]
            }
        }
        tomli_w.dump(config_data, f)
        temp_file = f.name
    
    try:
        # 使用便捷函数从文件加载
        from parsers.config_loader import load_parser_config_from_file
        parser_config = load_parser_config_from_file(temp_file, "file_test")
        
        assert parser_config.parser_type == ParserType.ARGPARSE
        assert parser_config.program_name == "file_test"
        assert len(parser_config.arguments) == 1
        assert parser_config.arguments[0].name == "file_arg"
        
        print("✅ 文件加载测试通过")
    finally:
        # 清理临时文件
        os.unlink(temp_file)


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 测试缺少程序配置
    config_data = {
        "other_program": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "other"
            }
        }
    }
    
    loader = ConfigLoader(config_data)
    try:
        loader.load_parser_config("nonexistent_program")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "缺少" in str(e)
        print("✅ 错误处理测试通过")


def main():
    """运行所有测试"""
    print("开始测试配置加载器核心功能...\n")
    
    try:
        test_basic_parser_config()
        test_id_and_include_functionality()
        test_file_loading()
        test_error_handling()
        
        print("\n🎉 所有核心功能测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())