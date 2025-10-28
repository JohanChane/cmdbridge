#!/usr/bin/env python3
"""
OperationMapping 核心功能测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import tomli_w
import sys

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.core.operation_mapping import OperationMapping
from cmdbridge.config.path_manager import PathManager


class TestOperationMapping:
    """OperationMapping 核心功能测试"""
    
    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 重置 PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # 创建领域配置目录
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试配置
        self._create_test_config()
    
    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_test_config(self):
        """创建测试配置"""
        # 创建缓存目录
        cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache("package")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建操作到程序映射文件
        op_to_program = {
            "operation_to_program": {
                "install": {
                    "apt": ["apt"]
                },
                "search": {
                    "apt": ["apt"]
                },
                "update": {
                    "apt": ["apt"]
                }
            }
        }
        
        op_file = self.path_manager.get_operation_to_program_path("package")
        with open(op_file, 'wb') as f:
            tomli_w.dump(op_to_program, f)
        
        # 创建 apt 命令格式
        apt_dir = self.path_manager.get_operation_mappings_group_dir_of_cache("package", "apt")
        apt_dir.mkdir(parents=True, exist_ok=True)
        
        apt_commands = {
            "commands": {
                "install": "apt install {pkgs}",
                "search": "apt search {query}",
                "update": "apt update"
            }
        }
        
        apt_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_commands, f)
    
    def test_basic_command_generation(self):
        """测试基本命令生成"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim git"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim git"
    
    def test_search_command(self):
        """测试搜索命令"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="search",
            params={"query": "python"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt search python"
    
    def test_no_parameters_command(self):
        """测试无参数命令"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="update",
            params={},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt update"
    
    def test_nonexistent_operation(self):
        """测试不存在的操作"""
        mapping = OperationMapping()
        
        with pytest.raises(ValueError):
            mapping.generate_command(
                operation_name="nonexistent",
                params={},
                dst_operation_domain_name="package",
                dst_operation_group_name="apt"
            )
    
    def test_parameter_replacement(self):
        """测试参数替换"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim"
        
        # 测试多个参数
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim git curl"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim git curl"


def run_tests():
    """运行所有测试"""
    test_instance = TestOperationMapping()
    
    try:
        test_instance.setup_method()
        
        tests = [
            test_instance.test_basic_command_generation,
            test_instance.test_search_command,
            test_instance.test_no_parameters_command,
            test_instance.test_nonexistent_operation,
            test_instance.test_parameter_replacement,
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
        
        print(f"\n📊 测试结果: {passed} 通过, {failed} 失败")
        
        if failed == 0:
            print("🎉 所有测试通过！")
        else:
            print("💥 有测试失败，请检查")
            
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    run_tests()