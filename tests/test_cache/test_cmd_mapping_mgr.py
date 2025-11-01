#!/usr/bin/env python3
"""
测试命令映射管理器核心功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cmdbridge.cache.cmd_mapping_mgr import CmdMappingMgr
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount
import tomli_w


def setup_test_configs():
    """设置测试配置"""
    # 创建临时目录结构
    temp_dir = tempfile.mkdtemp()
    
    # 初始化 PathManager
    path_manager = PathManager(
        config_dir=temp_dir,
        cache_dir=temp_dir
    )
    
    # 创建测试领域和操作组配置
    domain_dir = path_manager.get_operation_domain_dir_of_config("test_package")
    domain_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建操作组配置文件
    group_config = {
        "operations": {
            "install_remote": {
                "cmd_format": "apt install {pkgs}"
            },
            "list_installed": {
                "cmd_format": "apt list --installed"
            }
        }
    }
    
    group_file = domain_dir / "apt.toml"
    with open(group_file, 'wb') as f:
        tomli_w.dump(group_config, f)
    
    return temp_dir, path_manager


def create_mock_parser_config():
    """创建模拟的解析器配置"""
    return ParserConfig(
        parser_type=ParserType.ARGPARSE,
        program_name="apt",
        arguments=[
            ArgumentConfig(
                name="pkgs",
                opt=[],
                nargs=ArgumentCount("+"),
                required=False
            ),
            ArgumentConfig(
                name="config_path", 
                opt=["--config"],
                nargs=ArgumentCount("1"),
                required=False
            )
        ],
        sub_commands=[]
    )


def test_program_extraction():
    """测试程序名提取功能"""
    print("=== 测试程序名提取 ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # 测试各种命令格式
    test_cases = [
        ("apt install {pkgs}", "apt"),
        ("pacman -S {pkgs}", "pacman"),
        ("docker container ls", "docker"),
        ("git commit -m '{message}'", "git"),
        ("", None),
        ("   ", None),
    ]
    
    for cmd_format, expected in test_cases:
        result = mapping_mgr._extract_program_from_cmd_format(cmd_format)
        assert result == expected, f"对于 '{cmd_format}'，期望 '{expected}'，但得到 '{result}'"
    
    print("✅ 程序名提取测试通过")


def test_example_command_generation():
    """测试示例命令生成功能"""
    print("\n=== 测试示例命令生成 ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # 创建模拟的解析器配置
    parser_config = create_mock_parser_config()
    
    # 测试命令格式解析
    cmd_format = "apt install {pkgs} --config {config_path}"
    example_cmd = mapping_mgr._generate_example_command(cmd_format, parser_config)
    
    # 验证生成的示例命令
    assert len(example_cmd) >= 3
    assert example_cmd[0] == "apt"
    assert example_cmd[1] == "install"
    
    # 检查是否包含占位符
    has_placeholders = any("__param_" in part for part in example_cmd)
    assert has_placeholders, "示例命令应该包含占位符"
    
    print("✅ 示例命令生成测试通过")


def test_param_example_values():
    """测试参数示例值生成"""
    print("\n=== 测试参数示例值生成 ===")
    
    mapping_mgr = CmdMappingMgr("test", "test")
    
    # 创建模拟的解析器配置
    parser_config = create_mock_parser_config()
    
    # 测试单值参数
    single_values = mapping_mgr._generate_param_example_values("config_path", parser_config)
    assert len(single_values) == 1
    assert "__param_config_path__" in single_values[0]
    
    # 测试多值参数
    multi_values = mapping_mgr._generate_param_example_values("pkgs", parser_config)
    assert len(multi_values) == 2
    assert all("__param_pkgs__" in value for value in multi_values)
    
    # 测试不存在的参数（使用默认值）
    default_values = mapping_mgr._generate_param_example_values("nonexistent", parser_config)
    assert len(default_values) == 1
    assert "__param_nonexistent__" in default_values[0]
    
    print("✅ 参数示例值生成测试通过")


def test_mapping_structure():
    """测试映射数据结构"""
    print("\n=== 测试映射数据结构 ===")
    
    temp_dir, path_manager = setup_test_configs()
    
    try:
        # 创建映射管理器
        mapping_mgr = CmdMappingMgr("test_package", "apt")
        
        # 生成映射数据
        mapping_data = mapping_mgr.create_mappings()
        
        # 验证返回的数据结构
        assert "program_mappings" in mapping_data
        assert "cmd_to_operation" in mapping_data
        
        # 验证程序映射结构
        program_mappings = mapping_data["program_mappings"]
        assert isinstance(program_mappings, dict)
        
        # 验证 cmd_to_operation 结构
        cmd_to_operation = mapping_data["cmd_to_operation"]
        assert isinstance(cmd_to_operation, dict)
        
        print("✅ 映射数据结构测试通过")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_file_writing():
    """测试文件写入功能"""
    print("\n=== 测试文件写入 ===")
    
    temp_dir, path_manager = setup_test_configs()
    
    try:
        # 创建映射管理器
        mapping_mgr = CmdMappingMgr("test_package", "apt")
        
        # 生成映射数据
        mapping_data = mapping_mgr.create_mappings()
        
        # 写入文件
        mapping_mgr.write_to()
        
        # 验证缓存目录是否创建
        cache_dir = path_manager.get_cmd_mappings_domain_dir_of_cache("test_package")
        assert cache_dir.exists()
        
        print("✅ 文件写入测试通过")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("开始测试命令映射管理器核心功能...\n")
    
    try:
        test_program_extraction()
        test_param_example_values()
        test_example_command_generation()
        test_mapping_structure()
        test_file_writing()
        
        print("\n🎉 所有核心功能测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())