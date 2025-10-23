# tests/test_core/test_operation_mapping.py

import pytest
import os
import sys
from pathlib import Path
import tempfile
import tomli

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from cmdbridge.core.operation_mapping import OperationMapping, create_operation_mapping, generate_command_from_operation
from log import set_level, LogLevel


class TestOperationMapping:
    """OperationMapping 测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 设置日志级别
        set_level(LogLevel.INFO)
        
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.configs_dir = Path(self.temp_dir)
        
        # 创建 package.groups 目录
        package_groups_dir = self.configs_dir / "package.groups"
        package_groups_dir.mkdir(parents=True)
        
        # 创建 apt.toml 配置文件
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
                }
            }
        }
        
        apt_file = package_groups_dir / "apt.toml"
        with open(apt_file, 'wb') as f:  # 使用二进制模式
            tomli_w = __import__('tomli_w')
            tomli_w.dump(apt_config, f)
        
        # 创建 pacman.toml 配置文件
        pacman_config = {
            "operations": {
                "install_remote.pacman": {
                    "cmd_format": "pacman -S {pkgs}"
                },
                "search_remote.pacman": {
                    "cmd_format": "pacman -Ss {query}"
                },
                "update.pacman": {
                    "cmd_format": "pacman -Syu"
                }
            }
        }
        
        pacman_file = package_groups_dir / "pacman.toml"
        with open(pacman_file, 'wb') as f:  # 使用二进制模式
            tomli_w = __import__('tomli_w')
            tomli_w.dump(pacman_config, f)
        
        # 创建 process.groups 目录和配置文件
        process_groups_dir = self.configs_dir / "process.groups"
        process_groups_dir.mkdir(parents=True)
        
        process_config = {
            "operations": {
                "grep_log.process": {
                    "cmd_format": "cat {log_files} | grep -i '{log_level}' | grep -i '{log_msg}'"
                }
            }
        }
        
        process_file = process_groups_dir / "process.toml"
        with open(process_file, 'wb') as f:  # 使用二进制模式
            tomli_w = __import__('tomli_w')
            tomli_w.dump(process_config, f)
    
    def teardown_method(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_basic_command_generation(self):
        """测试基本命令生成"""
        print("\n=== 测试基本命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试 apt install 命令
        cmdline = mapping.generate_command(
            operation_name="install_remote",
            params={"pkgs": "vim git"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"基本命令生成结果: {cmdline}")
        assert cmdline == "apt install vim git"
    
    def test_search_command_generation(self):
        """测试搜索命令生成"""
        print("\n=== 测试搜索命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试 apt search 命令
        cmdline = mapping.generate_command(
            operation_name="search_remote",
            params={"query": "python"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"搜索命令生成结果: {cmdline}")
        assert cmdline == "apt search python"
    
    def test_command_with_multiple_parameters(self):
        """测试多参数命令生成"""
        print("\n=== 测试多参数命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试带配置的安装命令
        cmdline = mapping.generate_command(
            operation_name="install_with_config",
            params={"pkgs": "vim", "config_path": "custom.conf"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"多参数命令生成结果: {cmdline}")
        assert cmdline == "apt install vim --config custom.conf"
    
    def test_command_without_parameters(self):
        """测试无参数命令生成"""
        print("\n=== 测试无参数命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试无参数命令
        cmdline = mapping.generate_command(
            operation_name="list_installed",
            params={},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"无参数命令生成结果: {cmdline}")
        assert cmdline == "apt list --installed"
    
    def test_pacman_command_generation(self):
        """测试 Pacman 命令生成"""
        print("\n=== 测试 Pacman 命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试 pacman 命令
        cmdline = mapping.generate_command(
            operation_name="install_remote",
            params={"pkgs": "vim"},
            dst_operation_groups_name="package",
            dst_operation_group_name="pacman"
        )
        
        print(f"Pacman 命令生成结果: {cmdline}")
        assert cmdline == "pacman -S vim"
    
    def test_process_group_command_generation(self):
        """测试 process 组命令生成"""
        print("\n=== 测试 process 组命令生成 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试 process 组命令
        cmdline = mapping.generate_command(
            operation_name="grep_log",
            params={
                "log_files": "app.log error.log",
                "log_level": "ERROR", 
                "log_msg": "connection"
            },
            dst_operation_groups_name="process",
            dst_operation_group_name="process"
        )
        
        print(f"Process 命令生成结果: {cmdline}")
        expected = "cat app.log error.log | grep -i 'ERROR' | grep -i 'connection'"
        assert cmdline == expected
    
    def test_operation_not_found(self):
        """测试操作不存在的情况"""
        print("\n=== 测试操作不存在 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试不存在的操作
        with pytest.raises(ValueError, match="未找到操作配置"):
            mapping.generate_command(
                operation_name="nonexistent_operation",
                params={"pkgs": "vim"},
                dst_operation_groups_name="package",
                dst_operation_group_name="apt"
            )
    
    def test_program_not_found(self):
        """测试程序不存在的情况"""
        print("\n=== 测试程序不存在 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试不存在的程序
        with pytest.raises(ValueError, match="未找到操作配置"):
            mapping.generate_command(
                operation_name="install_remote",
                params={"pkgs": "vim"},
                dst_operation_groups_name="package", 
                dst_operation_group_name="nonexistent"
            )
    
    def test_group_not_found(self):
        """测试操作组不存在的情况"""
        print("\n=== 测试操作组不存在 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试不存在的操作组
        with pytest.raises(ValueError, match="未找到操作配置"):
            mapping.generate_command(
                operation_name="install_remote",
                params={"pkgs": "vim"},
                dst_operation_groups_name="nonexistent",
                dst_operation_group_name="apt"
            )
    
    def test_missing_required_parameter(self):
        """测试缺少必需参数的情况"""
        print("\n=== 测试缺少必需参数 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试缺少参数（应该仍然生成命令，但参数不会被替换）
        cmdline = mapping.generate_command(
            operation_name="install_with_config",
            params={"pkgs": "vim"},  # 缺少 config_path
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"缺少参数命令生成结果: {cmdline}")
        # 缺少的参数占位符会保留在命令中
        assert cmdline == "apt install vim --config {config_path}"
    
    def test_convenience_function(self):
        """测试便捷函数"""
        print("\n=== 测试便捷函数 ===")
        
        # 测试便捷函数
        cmdline = generate_command_from_operation(
            operation_name="install_remote",
            params={"pkgs": "test-package"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt",
            configs_dir=str(self.configs_dir)
        )
        
        print(f"便捷函数结果: {cmdline}")
        assert cmdline == "apt install test-package"
    
    def test_create_operation_mapping(self):
        """测试创建操作映射器"""
        print("\n=== 测试创建操作映射器 ===")
        
        mapping = create_operation_mapping(str(self.configs_dir))
        assert isinstance(mapping, OperationMapping)
        
        # 验证创建的实例可以正常工作
        cmdline = mapping.generate_command(
            operation_name="install_remote",
            params={"pkgs": "test-package"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"创建映射器测试结果: {cmdline}")
        assert cmdline == "apt install test-package"
    
    def test_command_with_special_characters(self):
        """测试特殊字符参数"""
        print("\n=== 测试特殊字符参数 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试包含特殊字符的参数
        cmdline = mapping.generate_command(
            operation_name="install_remote",
            params={"pkgs": "package-with-dash package_with_underscore"},
            dst_operation_groups_name="package",
            dst_operation_group_name="apt"
        )
        
        print(f"特殊字符参数结果: {cmdline}")
        expected = "apt install package-with-dash package_with_underscore"
        assert cmdline == expected
    
    def test_update_command_without_params(self):
        """测试无参数的更新命令"""
        print("\n=== 测试无参数更新命令 ===")
        mapping = OperationMapping(str(self.configs_dir))
        
        # 测试 pacman 更新命令（无参数）
        cmdline = mapping.generate_command(
            operation_name="update",
            params={},
            dst_operation_groups_name="package", 
            dst_operation_group_name="pacman"
        )
        
        print(f"无参数更新命令结果: {cmdline}")
        assert cmdline == "pacman -Syu"


if __name__ == "__main__":
    set_level(LogLevel.INFO)
    pytest.main([__file__, "-v", "-s"])  # 添加 -s 参数以显示 print 输出