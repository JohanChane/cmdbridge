#!/usr/bin/env python3
"""
OperationMappingMgr 核心功能测试 - 修复版
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import tomli_w
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.cache.operation_mapping_mgr import OperationMappingMgr, create_operation_mappings_for_domain
from cmdbridge.config.path_manager import PathManager


class TestOperationMappingMgrSimple:
    """OperationMappingMgr 简化测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp(prefix="cmdbridge_test_")
        
        # 重置 PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # 创建最小化测试配置
        self._create_minimal_config()
    
    def teardown_method(self):
        """测试清理"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_minimal_config(self):
        """创建最小化测试配置"""
        # 创建 package.domain 目录
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建领域基础文件
        base_config = {
            "operations": {
                "install": {
                    "description": "Install packages",
                    "args": ["pkgs"]
                },
                "search": {
                    "description": "Search packages", 
                    "args": ["query"]
                },
                "update": {
                    "description": "Update packages",
                    "args": []
                }
            }
        }
        
        base_file = self.path_manager.get_domain_base_config_path("package")
        with open(base_file, 'wb') as f:
            tomli_w.dump(base_config, f)
        
        # 创建 apt.toml 配置文件
        apt_config = {
            "operations": {
                "install.apt": {
                    "cmd_format": "apt install {pkgs}"
                },
                "search.apt": {
                    "cmd_format": "apt search {query}"
                },
                "update.apt": {
                    "cmd_format": "apt update"
                }
            }
        }
        
        apt_file = package_domain_dir / "apt.toml"
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_config, f)
        
        # 创建 pacman.toml 配置文件
        pacman_config = {
            "operations": {
                "install.pacman": {
                    "cmd_format": "pacman -S {pkgs}"
                },
                "search.pacman": {
                    "cmd_format": "pacman -Ss {query}"
                }
            }
        }
        
        pacman_file = package_domain_dir / "pacman.toml"
        with open(pacman_file, 'wb') as f:
            tomli_w.dump(pacman_config, f)
    
    def test_basic_mapping_creation(self):
        """测试基本映射创建"""
        print("🧪 测试基本映射创建...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 验证返回数据结构
        assert "operation_to_program" in mapping_data
        assert "command_formats_by_group" in mapping_data
        
        operation_to_program = mapping_data["operation_to_program"]
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # 验证基本操作映射
        assert "install" in operation_to_program
        assert "search" in operation_to_program
        assert "update" in operation_to_program
        
        # 验证操作组
        assert "apt" in command_formats_by_group
        assert "pacman" in command_formats_by_group
        
        print("✅ 基本映射创建测试通过")
    
    def test_operation_to_program_structure(self):
        """测试操作到程序映射结构"""
        print("🧪 测试操作到程序映射结构...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        operation_to_program = mapping_data["operation_to_program"]
        
        # 验证 install 操作的映射
        assert "install" in operation_to_program
        install_mapping = operation_to_program["install"]
        
        assert "apt" in install_mapping
        assert "pacman" in install_mapping
        
        # 验证程序列表
        assert "apt" in install_mapping["apt"]
        assert "pacman" in install_mapping["pacman"]
        
        print("✅ 操作到程序映射结构测试通过")
    
    def test_command_formats_collection(self):
        """测试命令格式收集"""
        print("🧪 测试命令格式收集...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # 验证 apt 操作组的命令格式
        assert "apt" in command_formats_by_group
        apt_formats = command_formats_by_group["apt"]
        
        assert "apt" in apt_formats
        apt_commands = apt_formats["apt"]
        
        # 验证命令格式内容
        assert "install" in apt_commands
        assert apt_commands["install"] == "apt install {pkgs}"
        assert "search" in apt_commands
        assert apt_commands["search"] == "apt search {query}"
        assert "update" in apt_commands
        assert apt_commands["update"] == "apt update"
        
        print("✅ 命令格式收集测试通过")
    
    def test_file_generation(self):
        """测试文件生成 - 修复版"""
        print("🧪 测试文件生成...")
        
        # 使用便捷函数创建映射，它会自动生成文件
        success = create_operation_mappings_for_domain("package")
        assert success
        
        # 验证主要文件是否生成
        operation_to_program_file = self.path_manager.get_operation_to_program_path("package")
        assert operation_to_program_file.exists(), f"operation_to_program 文件应该存在: {operation_to_program_file}"
        
        # 验证操作组文件
        apt_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert apt_commands_file.exists(), f"apt 命令文件应该存在: {apt_commands_file}"
        
        pacman_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "pacman", "pacman"
        )
        assert pacman_commands_file.exists(), f"pacman 命令文件应该存在: {pacman_commands_file}"
        
        print("✅ 文件生成测试通过")
    
    def test_program_name_extraction(self):
        """测试程序名提取"""
        print("🧪 测试程序名提取...")
        
        creator = OperationMappingMgr("package")
        
        # 测试正常命令格式
        config = {"cmd_format": "apt install {pkgs}"}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name == "apt"
        
        # 测试复杂命令
        config = {"cmd_format": "custom-tool --option value"}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name == "custom-tool"
        
        # 测试空配置
        config = {}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name is None
        
        print("✅ 程序名提取测试通过")
    
    def test_convenience_function(self):
        """测试便捷函数"""
        print("🧪 测试便捷函数...")
        
        # 使用便捷函数创建映射
        success = create_operation_mappings_for_domain("package")
        assert success
        
        # 验证返回值为布尔型
        assert isinstance(success, bool)
        
        print("✅ 便捷函数测试通过")


def run_tests():
    """运行所有测试"""
    test_instance = TestOperationMappingMgrSimple()
    
    try:
        test_instance.setup_method()
        
        tests = [
            test_instance.test_basic_mapping_creation,
            test_instance.test_operation_to_program_structure,
            test_instance.test_command_formats_collection,
            test_instance.test_file_generation,
            test_instance.test_program_name_extraction,
            test_instance.test_convenience_function,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
                print(f"✅ {test.__name__} - 通过")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__} - 失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 测试结果: {passed} 通过, {failed} 失败")
        
        if failed == 0:
            print("🎉 所有测试通过！")
        else:
            print("💥 有测试失败，请检查")
            
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    run_tests()