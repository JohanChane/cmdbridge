#!/usr/bin/env python3
"""
OperationMappingMgr pytest 测试程序

测试操作映射创建器的核心功能，包括：
1. 领域配置加载和解析
2. 操作到程序映射生成
3. 命令格式收集和分组
4. 分离文件生成
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

from cmdbridge.cache.operation_mapping_mgr import OperationMappingMgr, create_operation_mappings_for_domain
from cmdbridge.config.path_manager import PathManager
from log import set_level, LogLevel


class TestOperationMappingMgr:
    """OperationMappingMgr 测试类"""
    
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
        
        # 创建领域基础文件
        base_config = {
            "operations": {
                "install_remote": {
                    "description": "Install packages from remote repositories",
                    "args": ["pkgs"]
                },
                "search_remote": {
                    "description": "Search packages in remote repositories", 
                    "args": ["query"]
                },
                "list_installed": {
                    "description": "List installed packages",
                    "args": []
                },
                "install_with_config": {
                    "description": "Install packages using config file",
                    "args": ["pkgs", "config_path"]
                }
            }
        }
        
        base_file = self.path_manager.get_domain_base_config_path("package")
        with open(base_file, 'wb') as f:
            tomli_w.dump(base_config, f)
        print(f"✅ 创建领域基础文件: {base_file}")
        
        # 创建 apt.toml 配置文件
        apt_config = {
            "operations": {
                "install_remote.apt": {
                    "cmd_format": "apt install {pkgs}"
                },
                "search_remote.apt": {
                    "cmd_format": "apt search {query}"
                },
                "list_installed.apt": {
                    "cmd_format": "apt list --installed"
                },
                "install_with_config.apt": {
                    "cmd_format": "apt install {pkgs} --config {config_path}",
                    "final_cmd_format": "apt-custom-install {pkgs} {config_path}"
                }
            }
        }
        
        apt_file = package_domain_dir / "apt.toml"
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_config, f)
        print(f"✅ 创建 apt 配置: {apt_file}")
        
        # 创建 pacman.toml 配置文件
        pacman_config = {
            "operations": {
                "install_remote.pacman": {
                    "cmd_format": "pacman -S {pkgs}"
                },
                "search_remote.pacman": {
                    "cmd_format": "pacman -Ss {query}"
                },
                "list_installed.pacman": {
                    "cmd_format": "pacman -Q"
                }
            }
        }
        
        pacman_file = package_domain_dir / "pacman.toml"
        with open(pacman_file, 'wb') as f:
            tomli_w.dump(pacman_config, f)
        print(f"✅ 创建 pacman 配置: {pacman_file}")
        
        # 创建 process.domain 目录和配置文件（测试多领域）
        process_domain_dir = self.path_manager.get_operation_domain_dir_of_config("process")
        process_domain_dir.mkdir(parents=True, exist_ok=True)
        
        process_base_config = {
            "operations": {
                "grep_log": {
                    "description": "Grep logs with level and message",
                    "args": ["log_files", "log_level", "log_msg"]
                }
            }
        }
        
        process_base_file = self.path_manager.get_domain_base_config_path("process")
        with open(process_base_file, 'wb') as f:
            tomli_w.dump(process_base_config, f)
        print(f"✅ 创建 process 领域基础文件: {process_base_file}")
        
        process_config = {
            "operations": {
                "grep_log.process": {
                    "cmd_format": "cat {log_files} | grep -i '{log_level}' | grep -i '{log_msg}'"
                }
            }
        }
        
        process_file = process_domain_dir / "process.toml"
        with open(process_file, 'wb') as f:
            tomli_w.dump(process_config, f)
        print(f"✅ 创建 process 配置: {process_file}")
    
    def test_basic_mapping_creation(self):
        """测试基本映射创建"""
        print("\n=== 测试基本映射创建 ===")
        
        # 创建映射管理器
        creator = OperationMappingMgr("package")
        
        # 创建映射
        mapping_data = creator.create_mappings()
        
        # 验证返回数据结构
        assert "operation_to_program" in mapping_data
        assert "command_formats_by_group" in mapping_data
        
        operation_to_program = mapping_data["operation_to_program"]
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # 验证操作到程序映射
        assert "install_remote" in operation_to_program
        assert "apt" in operation_to_program["install_remote"]
        assert "pacman" in operation_to_program["install_remote"]
        
        # 验证命令格式分组
        assert "apt" in command_formats_by_group
        assert "pacman" in command_formats_by_group
        
        print(f"✅ 基本映射创建测试通过")
        print(f"   操作到程序映射: {len(operation_to_program)} 个操作")
        print(f"   命令格式分组: {len(command_formats_by_group)} 个操作组")
    
    def test_operation_to_program_mapping(self):
        """测试操作到程序映射的详细结构"""
        print("\n=== 测试操作到程序映射 ===")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        operation_to_program = mapping_data["operation_to_program"]
        
        # 验证 install_remote 操作
        assert "install_remote" in operation_to_program
        install_remote_mapping = operation_to_program["install_remote"]
        
        assert "apt" in install_remote_mapping
        assert "pacman" in install_remote_mapping
        
        # 验证程序列表
        assert "apt" in install_remote_mapping["apt"]
        assert "pacman" in install_remote_mapping["pacman"]
        
        print(f"✅ 操作到程序映射测试通过")
        print(f"   install_remote 支持的程序组: {list(install_remote_mapping.keys())}")
    
    def test_command_formats_by_group(self):
        """测试命令格式分组"""
        print("\n=== 测试命令格式分组 ===")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # 验证 apt 操作组
        assert "apt" in command_formats_by_group
        apt_formats = command_formats_by_group["apt"]
        
        assert "apt" in apt_formats
        apt_commands = apt_formats["apt"]
        
        # 验证命令格式
        assert "install_remote" in apt_commands
        assert apt_commands["install_remote"] == "apt install {pkgs}"
        
        assert "search_remote" in apt_commands
        assert apt_commands["search_remote"] == "apt search {query}"
        
        # 验证 final_cmd_format
        assert "install_with_config_final" in apt_commands
        assert apt_commands["install_with_config_final"] == "apt-custom-install {pkgs} {config_path}"
        
        print(f"✅ 命令格式分组测试通过")
        print(f"   apt 操作组包含 {len(apt_commands)} 个命令格式")
    
    def test_program_extraction(self):
        """测试程序名提取"""
        print("\n=== 测试程序名提取 ===")
        
        creator = OperationMappingMgr("package")
        
        # 测试正常命令格式
        config_with_cmd = {"cmd_format": "apt install {pkgs}"}
        program_name = creator._extract_program_from_cmd_format(config_with_cmd)
        assert program_name == "apt"
        
        # 测试 final_cmd_format
        config_with_final = {"final_cmd_format": "custom-tool --option {value}"}
        program_name = creator._extract_program_from_cmd_format(config_with_final)
        assert program_name == "custom-tool"
        
        # 测试空配置
        config_empty = {}
        program_name = creator._extract_program_from_cmd_format(config_empty)
        assert program_name is None
        
        # 测试空命令格式
        config_empty_cmd = {"cmd_format": ""}
        program_name = creator._extract_program_from_cmd_format(config_empty_cmd)
        assert program_name is None
        
        print(f"✅ 程序名提取测试通过")
    
    def test_file_generation(self):
        """测试文件生成功能"""
        print("\n=== 测试文件生成功能 ===")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 验证缓存文件是否生成
        operation_to_program_file = self.path_manager.get_operation_to_program_path("package")
        assert operation_to_program_file.exists(), f"operation_to_program 文件应该存在: {operation_to_program_file}"
        
        # 验证操作组目录和文件
        apt_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert apt_commands_file.exists(), f"apt 命令文件应该存在: {apt_commands_file}"
        
        pacman_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "pacman", "pacman" 
        )
        assert pacman_commands_file.exists(), f"pacman 命令文件应该存在: {pacman_commands_file}"
        
        print(f"✅ 文件生成测试通过")
        print(f"   生成文件: {operation_to_program_file.name}")
        print(f"   生成文件: {apt_commands_file.name}")
        print(f"   生成文件: {pacman_commands_file.name}")
    
    def test_multiple_domains(self):
        """测试多领域支持"""
        print("\n=== 测试多领域支持 ===")
        
        # 测试 package 领域
        package_creator = OperationMappingMgr("package")
        package_data = package_creator.create_mappings()
        assert "operation_to_program" in package_data
        assert "install_remote" in package_data["operation_to_program"]
        
        # 测试 process 领域
        process_creator = OperationMappingMgr("process")
        process_data = process_creator.create_mappings()
        assert "operation_to_program" in process_data
        assert "grep_log" in process_data["operation_to_program"]
        
        print(f"✅ 多领域支持测试通过")
        print(f"   package 领域: {len(package_data['operation_to_program'])} 个操作")
        print(f"   process 领域: {len(process_data['operation_to_program'])} 个操作")
    
    def test_convenience_function(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        
        # 使用便捷函数创建映射
        success = create_operation_mappings_for_domain("package")
        assert success
        
        # 验证文件是否生成
        operation_to_program_file = self.path_manager.get_operation_to_program_path("package")
        assert operation_to_program_file.exists()
        
        print(f"✅ 便捷函数测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试不存在的领域
        creator = OperationMappingMgr("nonexistent")
        mapping_data = creator.create_mappings()
        
        # 应该返回空字典而不是抛出异常
        assert mapping_data == {}
        
        print(f"✅ 错误处理测试通过")
    
    def test_operation_name_extraction(self):
        """测试操作名提取逻辑"""
        print("\n=== 测试操作名提取逻辑 ===")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        operation_to_program = mapping_data["operation_to_program"]
        
        # 验证操作名提取（移除操作组后缀）
        expected_operations = ["install_remote", "search_remote", "list_installed", "install_with_config"]
        
        for expected_op in expected_operations:
            assert expected_op in operation_to_program, f"操作 {expected_op} 应该在映射中"
        
        # 验证没有带后缀的操作名
        for operation_name in operation_to_program.keys():
            assert "." not in operation_name, f"操作名不应该包含点号: {operation_name}"
        
        print(f"✅ 操作名提取测试通过")
        print(f"   提取的操作: {list(operation_to_program.keys())}")
    
    def test_final_cmd_format_handling(self):
        """测试 final_cmd_format 处理"""
        print("\n=== 测试 final_cmd_format 处理 ===")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # 验证 apt 操作组中的 final_cmd_format
        apt_formats = command_formats_by_group["apt"]["apt"]
        
        assert "install_with_config" in apt_formats
        assert "install_with_config_final" in apt_formats
        assert apt_formats["install_with_config_final"] == "apt-custom-install {pkgs} {config_path}"
        
        print(f"✅ final_cmd_format 处理测试通过")


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestOperationMappingMgr()
    
    try:
        test_instance.setup()
        
        # 运行各个测试方法
        test_methods = [
            test_instance.test_basic_mapping_creation,
            test_instance.test_operation_to_program_mapping,
            test_instance.test_command_formats_by_group,
            test_instance.test_program_extraction,
            test_instance.test_file_generation,
            test_instance.test_multiple_domains,
            test_instance.test_convenience_function,
            test_instance.test_error_handling,
            test_instance.test_operation_name_extraction,
            test_instance.test_final_cmd_format_handling,
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