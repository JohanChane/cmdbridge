# tests/test_config/test_operation_mapping_mgr.py

import pytest
import os
import tempfile
import tomli
import tomli_w
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from cmdbridge.config.operation_mapping_mgr import OperationMappingMgr, create_operation_mappings_for_domain, create_operation_mappings_for_all_domains
from cmdbridge.config.path_manager import PathManager
from log import set_level, LogLevel


class TestOperationMappingMgr:
    """OperationMappingMgr 测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 设置日志级别
        set_level(LogLevel.INFO)
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 重置 PathManager 单例以使用临时目录
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # 创建测试配置
        self._create_test_configs()
    
    def teardown_method(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
        # 重置 PathManager
        PathManager.reset_instance()
    
    def _create_test_configs(self):
        """创建测试配置"""
        # 创建 package.domain 目录
        package_domain_dir = self.path_manager.get_config_operation_group_path("package")
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
                }
            }
        }
        
        base_file = self.path_manager.get_domain_base_config_path("package")
        with open(base_file, 'wb') as f:
            tomli_w.dump(base_config, f)
        
        # 创建 apt.toml 配置文件
        apt_config = {
            "operations": {
                "install_remote": {
                    "cmd_format": "apt install {pkgs}"
                },
                "search_remote": {
                    "cmd_format": "apt search {query}"
                },
                "list_installed": {
                    "cmd_format": "apt list --installed"
                }
            }
        }
        
        apt_file = package_domain_dir / "apt.toml"
        with open(apt_file, 'wb') as f:
            tomli_w.dump(apt_config, f)
        
        # 创建 pacman.toml 配置文件
        pacman_config = {
            "operations": {
                "install_remote": {
                    "cmd_format": "pacman -S {pkgs}"
                },
                "search_remote": {
                    "cmd_format": "pacman -Ss {query}"
                },
                "list_installed": {
                    "cmd_format": "pacman -Q"
                }
            }
        }
        
        pacman_file = package_domain_dir / "pacman.toml"
        with open(pacman_file, 'wb') as f:
            tomli_w.dump(pacman_config, f)
        
        # 创建包含程序后缀的操作文件
        mixed_config = {
            "operations": {
                "install_remote.brew": {
                    "cmd_format": "brew install {pkgs}"
                },
                "search_remote.brew": {
                    "cmd_format": "brew search {query}"
                }
            }
        }
        
        mixed_file = package_domain_dir / "brew.toml"
        with open(mixed_file, 'wb') as f:
            tomli_w.dump(mixed_config, f)
    
    def test_create_mappings_basic(self):
        """测试基本映射创建"""
        print("\n=== 测试基本映射创建 ===")
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 验证返回的数据结构
        assert isinstance(mapping_data, dict)
        assert "operation_to_program" in mapping_data
        assert "command_formats" in mapping_data
        
        operation_to_program = mapping_data["operation_to_program"]
        command_formats = mapping_data["command_formats"]
        
        # 验证操作到程序的映射
        assert "install_remote" in operation_to_program
        assert "apt" in operation_to_program["install_remote"]
        assert "pacman" in operation_to_program["install_remote"]
        assert "brew" in operation_to_program["install_remote"]
        
        assert "search_remote" in operation_to_program
        assert "list_installed" in operation_to_program
        
        # 验证命令格式
        assert "apt" in command_formats
        assert "install_remote" in command_formats["apt"]
        assert command_formats["apt"]["install_remote"] == "apt install {pkgs}"
        
        assert "pacman" in command_formats
        assert "install_remote" in command_formats["pacman"]
        assert command_formats["pacman"]["install_remote"] == "pacman -S {pkgs}"
        
        assert "brew" in command_formats
        assert "install_remote" in command_formats["brew"]
        assert command_formats["brew"]["install_remote"] == "brew install {pkgs}"
    
    def test_operation_name_extraction(self):
        """测试操作名提取（移除程序后缀）"""
        print("\n=== 测试操作名提取 ===")
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        operation_to_program = mapping_data["operation_to_program"]
        
        # 验证 brew 的操作名已经移除了 .brew 后缀
        assert "install_remote" in operation_to_program
        assert "brew" in operation_to_program["install_remote"]
        
        # 操作名不应该包含程序后缀
        for operation_name in operation_to_program.keys():
            assert "." not in operation_name or "install_remote.brew" not in operation_to_program
    
    def test_cache_files_generation(self):
        """测试缓存文件生成"""
        print("\n=== 测试缓存文件生成 ===")
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 验证缓存文件是否生成
        cache_dir = self.path_manager.get_operation_mappings_cache_path("package")
        
        # 检查 operation_to_program.toml 文件
        op_to_prog_file = cache_dir / "operation_to_program.toml"
        assert op_to_prog_file.exists()
        
        with open(op_to_prog_file, 'rb') as f:
            op_to_prog_data = tomli.load(f)
        
        assert "operation_to_program" in op_to_prog_data
        assert "install_remote" in op_to_prog_data["operation_to_program"]
        
        # 检查程序命令文件
        apt_cmd_file = cache_dir / "apt_commands.toml"
        assert apt_cmd_file.exists()
        
        with open(apt_cmd_file, 'rb') as f:
            apt_cmd_data = tomli.load(f)
        
        assert "commands" in apt_cmd_data
        assert "install_remote" in apt_cmd_data["commands"]
        
        pacman_cmd_file = cache_dir / "pacman_commands.toml"
        assert pacman_cmd_file.exists()
        
        brew_cmd_file = cache_dir / "brew_commands.toml"
        assert brew_cmd_file.exists()
    
    def test_nonexistent_domain(self):
        """测试不存在的领域"""
        print("\n=== 测试不存在的领域 ===")
        creator = OperationMappingMgr("nonexistent")
        mapping_data = creator.create_mappings()
        
        # 对于不存在的领域，应该返回空字典
        assert mapping_data == {}
    
    def test_empty_domain_directory(self):
        """测试空领域目录"""
        print("\n=== 测试空领域目录 ===")
        # 创建空领域目录
        empty_domain_dir = self.path_manager.get_config_operation_group_path("empty")
        empty_domain_dir.mkdir(parents=True, exist_ok=True)
        
        creator = OperationMappingMgr("empty")
        mapping_data = creator.create_mappings()
        
        # 空目录应该返回包含空字典的结构
        assert mapping_data == {
            "operation_to_program": {},
            "command_formats": {}
        }
    
    def test_domain_with_base_file_only(self):
        """测试只有基础文件的领域"""
        print("\n=== 测试只有基础文件的领域 ===")
        # 创建只有基础文件的领域
        base_only_domain = "base_only"
        base_only_dir = self.path_manager.get_config_operation_group_path(base_only_domain)
        base_only_dir.mkdir(parents=True, exist_ok=True)
        
        # 只创建基础文件，不创建程序文件
        base_config = {
            "operations": {
                "test_operation": {
                    "description": "Test operation",
                    "args": ["param"]
                }
            }
        }
        
        base_file = self.path_manager.get_domain_base_config_path(base_only_domain)
        with open(base_file, 'wb') as f:
            tomli_w.dump(base_config, f)
        
        creator = OperationMappingMgr(base_only_domain)
        mapping_data = creator.create_mappings()
        
        # 只有基础文件没有程序文件，应该返回包含空字典的结构
        assert mapping_data == {
            "operation_to_program": {},
            "command_formats": {}
        }
    
    def test_convenience_function(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        success = create_operation_mappings_for_domain("package")
        
        # 应该成功创建映射
        assert success is True
        
        # 验证缓存文件生成
        cache_dir = self.path_manager.get_operation_mappings_cache_path("package")
        op_to_prog_file = cache_dir / "operation_to_program.toml"
        assert op_to_prog_file.exists()
    
    def test_convenience_function_nonexistent_domain(self):
        """测试便捷函数处理不存在的领域"""
        print("\n=== 测试便捷函数处理不存在的领域 ===")
        success = create_operation_mappings_for_domain("nonexistent")
        
        # 对于不存在的领域，应该返回 False
        assert success is False
    
    def test_create_operation_mappings_for_all_domains(self):
        """测试为所有领域创建映射"""
        print("\n=== 测试为所有领域创建映射 ===")
        
        # 创建第二个测试领域
        process_domain_dir = self.path_manager.get_config_operation_group_path("process")
        process_domain_dir.mkdir(parents=True, exist_ok=True)
        
        process_config = {
            "operations": {
                "grep_log": {
                    "cmd_format": "cat {log_files} | grep -i '{log_level}'"
                }
            }
        }
        
        process_file = process_domain_dir / "process.toml"
        with open(process_file, 'wb') as f:
            tomli_w.dump(process_config, f)
        
        # 测试为所有领域创建映射
        success = create_operation_mappings_for_all_domains()
        
        # 应该成功
        assert success is True
        
        # 验证两个领域的缓存文件都生成
        package_cache_dir = self.path_manager.get_operation_mappings_cache_path("package")
        assert (package_cache_dir / "operation_to_program.toml").exists()
        
        process_cache_dir = self.path_manager.get_operation_mappings_cache_path("process")
        assert (process_cache_dir / "operation_to_program.toml").exists()
    
    def test_operation_without_cmd_format(self):
        """测试没有 cmd_format 的操作"""
        print("\n=== 测试没有 cmd_format 的操作 ===")
        
        # 创建包含无效操作的文件
        invalid_config = {
            "operations": {
                "valid_operation": {
                    "cmd_format": "apt install {pkgs}"
                },
                "invalid_operation": {
                    "description": "This operation has no cmd_format"
                }
            }
        }
        
        invalid_file = self.path_manager.get_config_operation_group_path("package") / "invalid.toml"
        with open(invalid_file, 'wb') as f:
            tomli_w.dump(invalid_config, f)
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 应该只包含有效操作的映射
        command_formats = mapping_data["command_formats"]
        if "invalid" in command_formats:
            # 如果创建了 invalid 程序组，应该只包含 valid_operation
            assert "invalid_operation" not in command_formats["invalid"]
    
    def test_file_parsing_error(self):
        """测试文件解析错误"""
        print("\n=== 测试文件解析错误 ===")
        
        # 创建无效的 TOML 文件
        invalid_file = self.path_manager.get_config_operation_group_path("package") / "invalid.toml"
        with open(invalid_file, 'w') as f:
            f.write("invalid toml content [\n")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # 即使有文件解析错误，其他有效文件应该仍然处理
        assert mapping_data != {}
        assert "operation_to_program" in mapping_data
        assert "command_formats" in mapping_data


if __name__ == "__main__":
    set_level(LogLevel.INFO)
    pytest.main([__file__, "-v", "-s"])  # 添加 -s 参数以显示 print 输出