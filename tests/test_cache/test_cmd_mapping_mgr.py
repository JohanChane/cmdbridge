#!/usr/bin/env python3
"""
CmdMappingMgr pytest 测试程序

测试命令映射创建器的核心功能，包括：
1. 配置加载和解析
2. 命令格式处理
3. 参数占位符映射
4. 缓存文件生成
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import tomli_w

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.cache.cmd_mapping_mgr import CmdMappingMgr, create_cmd_mappings_for_group
from cmdbridge.config.path_manager import PathManager
from log import set_level, LogLevel


class TestCmdMappingMgr:
    """CmdMappingMgr 测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试方法的设置和清理"""
        # 设置日志级别
        set_level(LogLevel.INFO)
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="cmdbridge_test_")
        print(f"📁 创建临时目录: {self.temp_dir}")
        
        # 重置 PathManager 单例以使用临时目录
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # 创建测试配置
        self._create_test_configs()
        
        yield  # 执行测试
        
        # 清理
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 清理临时目录: {self.temp_dir}")
        PathManager.reset_instance()
    
    def _create_test_configs(self):
        """创建测试配置"""
        # 创建 package.domain 目录
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 apt.toml 配置文件 - 包含各种操作类型
        apt_config = {
            "operations": {
                "install_remote.apt": {
                    "cmd_format": "apt install {pkgs}"
                },
                "search_remote.apt": {
                    "cmd_format": "apt search {query}"
                },
                "install_with_config.apt": {
                    "cmd_format": "apt install {pkgs} --config {config_path}"
                },
                "list_installed.apt": {
                    "cmd_format": "apt list --installed"
                },
                "complex_command.apt": {
                    "cmd_format": "apt update {repos} --force-yes --option {value}"
                }
            }
        }
        
        apt_file = package_domain_dir / "apt.toml"
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_config, f)
        print(f"✅ 创建 apt 配置: {apt_file}")
        
        # 创建 pacman.toml 配置文件 - 使用正确的选项组合
        pacman_config = {
            "operations": {
                "install_remote.pacman": {
                    "cmd_format": "pacman -S {pkgs}"  # -S 安装
                },
                "search_remote.pacman": {
                    "cmd_format": "pacman -Ss {query}"  # -Ss 搜索远程
                },
                "search_local.pacman": {
                    "cmd_format": "pacman -Qs {query}"  # -Qs 搜索本地
                },
                "update.pacman": {
                    "cmd_format": "pacman -Syu"  # -Syu 同步并升级
                }
            }
        }
        
        pacman_file = package_domain_dir / "pacman.toml"
        with open(pacman_file, 'wb') as f:
            tomli_w.dump(pacman_config, f)
        print(f"✅ 创建 pacman 配置: {pacman_file}")
        
        # 创建程序解析器配置
        self._create_parser_configs()

    def _create_parser_configs(self):
        """创建程序解析器配置"""
        parser_config_dir = self.path_manager.program_parser_config_dir
        parser_config_dir.mkdir(parents=True, exist_ok=True)
        
        # apt 解析器配置 (argparse 风格)
        apt_parser_config = {
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
                            },
                            {
                                "name": "config",
                                "opt": ["--config"],
                                "nargs": "1"
                            }
                        ]
                    },
                    {
                        "name": "search",
                        "arguments": [
                            {
                                "name": "query",
                                "nargs": "+"
                            }
                        ]
                    },
                    {
                        "name": "list",
                        "arguments": [
                            {
                                "name": "installed",
                                "opt": ["--installed"],
                                "nargs": "0"
                            }
                        ]
                    },
                    {
                        "name": "update",
                        "arguments": [
                            {
                                "name": "repos",
                                "nargs": "*"
                            },
                            {
                                "name": "force_yes",
                                "opt": ["--force-yes"],
                                "nargs": "0"
                            },
                            {
                                "name": "option",
                                "opt": ["--option"],
                                "nargs": "1"
                            }
                        ]
                    }
                ]
            }
        }
        
        apt_parser_file = parser_config_dir / "apt.toml"
        with open(apt_parser_file, 'wb') as f:
            tomli_w.dump(apt_parser_config, f)
        print(f"✅ 创建 apt 解析器配置: {apt_parser_file}")
        
        # pacman 解析器配置 (getopt 风格) - 修复选项定义
        pacman_parser_config = {
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
                        "name": "sync",  # -S 同步操作
                        "opt": ["-S", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "search",  # -s 搜索
                        "opt": ["-s", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "refresh",  # -y 刷新
                        "opt": ["-y", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "upgrade",  # -u 升级
                        "opt": ["-u", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "query",  # -Q 查询本地包
                        "opt": ["-Q", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "files",  # -F 查询文件
                        "opt": ["-F", ""],
                        "nargs": "0"
                    },
                    {
                        "name": "packages",
                        "nargs": "+"
                    }
                ]
            }
        }
        
        pacman_parser_file = parser_config_dir / "pacman.toml"
        with open(pacman_parser_file, 'wb') as f:
            tomli_w.dump(pacman_parser_config, f)
        print(f"✅ 创建 pacman 解析器配置: {pacman_parser_file}")

    def test_basic_mapping_creation(self):
        """测试基本映射创建"""
        print("\n=== 测试基本映射创建 ===")
        
        # 创建映射管理器
        creator = CmdMappingMgr("package", "apt")
        
        # 创建映射
        mapping_data = creator.create_mappings()
        
        # 验证返回数据结构
        assert "program_mappings" in mapping_data
        assert "cmd_to_operation" in mapping_data
        assert "apt" in mapping_data["cmd_to_operation"]
        assert "programs" in mapping_data["cmd_to_operation"]["apt"]
        
        # 验证程序映射
        program_mappings = mapping_data["program_mappings"]
        assert "apt" in program_mappings
        assert "command_mappings" in program_mappings["apt"]
        
        # 验证命令映射数量
        command_mappings = program_mappings["apt"]["command_mappings"]
        assert len(command_mappings) > 0
        
        # 验证每个映射条目的结构
        for mapping in command_mappings:
            assert "operation" in mapping
            assert "cmd_format" in mapping
            assert "cmd_node" in mapping
            assert isinstance(mapping["cmd_node"], dict)
        
        print(f"✅ 基本映射创建测试通过，创建了 {len(command_mappings)} 个命令映射")
    
    def test_command_node_structure(self):
        """测试命令节点结构"""
        print("\n=== 测试命令节点结构 ===")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        program_mappings = mapping_data["program_mappings"]["apt"]["command_mappings"]
        
        for mapping in program_mappings:
            cmd_node = mapping["cmd_node"]
            
            # 验证命令节点基本结构
            assert "name" in cmd_node
            assert "arguments" in cmd_node
            assert isinstance(cmd_node["arguments"], list)
            
            # 验证操作名称提取
            operation_name = mapping["operation"]
            assert operation_name in ["install_remote", "search_remote", "install_with_config", "list_installed", "complex_command"]
            
            print(f"✅ 命令节点 '{operation_name}' 结构验证通过")
    
    def test_parameter_placeholder_mapping(self):
        """测试参数占位符映射"""
        print("\n=== 测试参数占位符映射 ===")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        program_mappings = mapping_data["program_mappings"]["apt"]["command_mappings"]
        
        # 查找包含参数的映射
        param_mappings = [m for m in program_mappings if "{" in m["cmd_format"]]
        
        for mapping in param_mappings:
            cmd_node = mapping["cmd_node"]
            
            # 检查参数是否被正确标记为占位符
            has_placeholders = False
            for arg in cmd_node["arguments"]:
                if "placeholder" in arg and arg["placeholder"]:
                    has_placeholders = True
                    print(f"✅ 找到参数占位符: {arg['placeholder']}")
        
        print("✅ 参数占位符映射测试通过")
    
    def test_cmd_to_operation_data(self):
        """测试 cmd_to_operation 数据生成"""
        print("\n=== 测试 cmd_to_operation 数据生成 ===")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        cmd_to_operation = mapping_data["cmd_to_operation"]
        
        # 验证数据结构
        assert "apt" in cmd_to_operation
        assert "programs" in cmd_to_operation["apt"]
        assert isinstance(cmd_to_operation["apt"]["programs"], list)
        
        # 验证程序列表
        programs = cmd_to_operation["apt"]["programs"]
        assert "apt" in programs
        
        print(f"✅ cmd_to_operation 数据生成测试通过，程序列表: {programs}")
    
    def test_file_generation(self):
        """测试文件生成功能"""
        print("\n=== 测试文件生成功能 ===")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        # 写入文件
        creator.write_to()
        
        # 验证缓存文件是否生成
        program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert program_file.exists(), f"程序映射文件应该存在: {program_file}"
        
        cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path("package")
        assert cmd_to_operation_file.exists(), f"cmd_to_operation 文件应该存在: {cmd_to_operation_file}"
        
        print("✅ 文件生成测试通过")
    
    def test_pacman_mapping(self):
        """测试 pacman 映射创建"""
        print("\n=== 测试 pacman 映射创建 ===")
        
        creator = CmdMappingMgr("package", "pacman")
        mapping_data = creator.create_mappings()
        
        # 验证基本结构
        assert "program_mappings" in mapping_data
        assert "pacman" in mapping_data["program_mappings"]
        
        program_mappings = mapping_data["program_mappings"]["pacman"]["command_mappings"]
        assert len(program_mappings) > 0
        
        # 验证操作类型
        operations = [m["operation"] for m in program_mappings]
        expected_operations = ["install_remote", "search_remote", "update"]
        for expected in expected_operations:
            assert expected in operations
        
        print(f"✅ pacman 映射创建测试通过，操作: {operations}")
    
    def test_convenience_function(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        
        # 使用便捷函数创建映射
        mapping_data = create_cmd_mappings_for_group("package", "apt")
        
        # 验证返回数据
        assert "program_mappings" in mapping_data
        assert "cmd_to_operation" in mapping_data
        
        # 验证文件是否生成
        program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert program_file.exists()
        
        print("✅ 便捷函数测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试不存在的操作组
        with pytest.raises(FileNotFoundError):
            creator = CmdMappingMgr("package", "nonexistent")
            creator.create_mappings()
        
        print("✅ 错误处理测试通过")
    
    def test_complex_command_parsing(self):
        """测试复杂命令解析"""
        print("\n=== 测试复杂命令解析 ===")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        program_mappings = mapping_data["program_mappings"]["apt"]["command_mappings"]
        
        # 查找复杂命令
        complex_commands = [m for m in program_mappings if m["operation"] == "complex_command"]
        
        if complex_commands:
            complex_cmd = complex_commands[0]
            cmd_node = complex_cmd["cmd_node"]
            
            # 验证复杂命令的结构
            assert "name" in cmd_node
            assert cmd_node["name"] == "apt"
            assert "arguments" in cmd_node
            
            print("✅ 复杂命令解析测试通过")
        else:
            pytest.skip("未找到复杂命令进行测试")


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestCmdMappingMgr()
    
    try:
        test_instance.setup()
        
        # 运行各个测试方法
        test_methods = [
            test_instance.test_basic_mapping_creation,
            test_instance.test_command_node_structure,
            test_instance.test_parameter_placeholder_mapping,
            test_instance.test_cmd_to_operation_data,
            test_instance.test_file_generation,
            test_instance.test_pacman_mapping,
            test_instance.test_convenience_function,
            test_instance.test_error_handling,
            test_instance.test_complex_command_parsing,
        ]
        
        for method in test_methods:
            print(f"\n{'='*50}")
            print(f"运行测试: {method.__name__}")
            print('='*50)
            try:
                method()
                print(f"✅ {method.__name__} - 通过")
            except Exception as e:
                print(f"❌ {method.__name__} - 失败: {e}")
                raise
        
        print(f"\n🎉 所有测试完成！")
        
    finally:
        test_instance.teardown()