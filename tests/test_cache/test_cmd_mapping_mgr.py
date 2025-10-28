#!/usr/bin/env python3
"""
CmdMappingMgr 核心功能测试 - 简化版
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

from cmdbridge.cache.cmd_mapping_mgr import CmdMappingMgr
from cmdbridge.config.path_manager import PathManager


class TestCmdMappingMgrSimple:
    """CmdMappingMgr 简化测试类"""
    
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
        
        # 创建简单的 apt 配置
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
        
        # 创建简单的解析器配置
        parser_config_dir = self.path_manager.program_parser_config_dir
        parser_config_dir.mkdir(parents=True, exist_ok=True)
        
        apt_parser_config = {
            "apt": {
                "parser_config": {
                    "parser_type": "argparse",
                    "program_name": "apt"
                },
                "sub_commands": [
                    {
                        "name": "install",
                        "arguments": [
                            {
                                "name": "packages",
                                "nargs": "+"
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
                        "name": "update",
                        "arguments": []
                    }
                ]
            }
        }
        
        apt_parser_file = parser_config_dir / "apt.toml"
        with open(apt_parser_file, 'wb') as f:
            tomli_w.dump(apt_parser_config, f)
    
    def test_basic_functionality(self):
        """测试基本功能 - 映射创建和数据生成"""
        print("🧪 测试基本功能...")
        
        # 创建映射管理器
        creator = CmdMappingMgr("package", "apt")
        
        # 创建映射
        mapping_data = creator.create_mappings()
        
        # 验证返回数据结构
        assert isinstance(mapping_data, dict)
        assert "program_mappings" in mapping_data
        assert "cmd_to_operation" in mapping_data
        
        # 验证程序映射
        program_mappings = mapping_data["program_mappings"]
        assert "apt" in program_mappings
        assert "command_mappings" in program_mappings["apt"]
        
        # 验证命令映射
        command_mappings = program_mappings["apt"]["command_mappings"]
        assert len(command_mappings) == 3  # install, search, update
        
        print("✅ 基本功能测试通过")
    
    def test_command_mapping_structure(self):
        """测试命令映射结构"""
        print("🧪 测试命令映射结构...")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        command_mappings = mapping_data["program_mappings"]["apt"]["command_mappings"]
        
        # 验证每个映射条目的结构
        for mapping in command_mappings:
            assert "operation" in mapping
            assert "cmd_format" in mapping
            assert "cmd_node" in mapping
            
            # 验证命令节点结构
            cmd_node = mapping["cmd_node"]
            assert "name" in cmd_node
            assert "arguments" in cmd_node
            assert isinstance(cmd_node["arguments"], list)
        
        print("✅ 命令映射结构测试通过")
    
    def test_parameter_extraction(self):
        """测试参数提取"""
        print("🧪 测试参数提取...")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        command_mappings = mapping_data["program_mappings"]["apt"]["command_mappings"]
        
        # 查找包含参数的映射
        install_mapping = next(m for m in command_mappings if m["operation"] == "install")
        search_mapping = next(m for m in command_mappings if m["operation"] == "search")
        
        # 验证参数占位符
        assert "{pkgs}" in install_mapping["cmd_format"]
        assert "{query}" in search_mapping["cmd_format"]
        
        print("✅ 参数提取测试通过")
    
    def test_file_generation(self):
        """测试文件生成"""
        print("🧪 测试文件生成...")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        # 写入文件
        creator.write_to()
        
        # 验证缓存文件是否生成
        program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert program_file.exists()
        
        cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path("package")
        assert cmd_to_operation_file.exists()
        
        print("✅ 文件生成测试通过")
    
    def test_cmd_to_operation_integration(self):
        """测试 cmd_to_operation 集成"""
        print("🧪 测试 cmd_to_operation 集成...")
        
        creator = CmdMappingMgr("package", "apt")
        mapping_data = creator.create_mappings()
        
        cmd_to_operation = mapping_data["cmd_to_operation"]
        
        # 验证数据结构
        assert "apt" in cmd_to_operation
        assert "programs" in cmd_to_operation["apt"]
        assert isinstance(cmd_to_operation["apt"]["programs"], list)
        assert "apt" in cmd_to_operation["apt"]["programs"]
        
        print("✅ cmd_to_operation 集成测试通过")


def run_tests():
    """运行所有测试"""
    test_instance = TestCmdMappingMgrSimple()
    
    try:
        test_instance.setup_method()
        
        tests = [
            test_instance.test_basic_functionality,
            test_instance.test_command_mapping_structure,
            test_instance.test_parameter_extraction,
            test_instance.test_file_generation,
            test_instance.test_cmd_to_operation_integration,
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