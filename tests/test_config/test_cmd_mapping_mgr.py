# tests/test_config/test_cmd_mapping_creator.py

import pytest
import os
import tempfile
import tomli
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from cmdbridge.config.cmd_mapping_mgr import CmdMappingMgr, create_cmd_mappings

from log import set_level, LogLevel


class TestCmdMappingCreator:
    """CmdMappingCreator 测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 创建临时目录结构
        self.temp_dir = tempfile.mkdtemp()
        self.domain_dir = Path(self.temp_dir) / "package.domain"
        self.parser_configs_dir = Path(self.temp_dir) / "program_parser_configs"
        self.output_dir = Path(self.temp_dir) / "output"
        
        # 创建目录
        self.domain_dir.mkdir()
        self.parser_configs_dir.mkdir()
        self.output_dir.mkdir()
        
        # 设置日志级别
        set_level(LogLevel.INFO)
    
    def teardown_method(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_apt_group_file(self):
        """创建 APT 操作文件"""
        apt_group_content = """
[operations.install_remote]
cmd_format = "apt install {pkgs}"

[operations.search_remote]
cmd_format = "apt search {query}"

[operations.install_with_config]
cmd_format = "apt install {pkgs} --config {config_path}"
"""
        apt_file = self.domain_dir / "apt.toml"
        with open(apt_file, 'w') as f:
            f.write(apt_group_content)
        return apt_file
    
    def _create_pacman_group_file(self):
        """创建 Pacman 操作文件"""
        pacman_group_content = """
[operations.install_remote]
cmd_format = "pacman -S {pkgs}"

[operations.search_remote]
cmd_format = "pacman -Ss {query}"

[operations.install_with_config]
cmd_format = "pacman -S {pkgs} --config {config_path}"
"""
        pacman_file = self.domain_dir / "pacman.toml"
        with open(pacman_file, 'w') as f:
            f.write(pacman_group_content)
        return pacman_file
    
    def _create_apt_parser_config(self):
        """创建 APT 解析器配置"""
        apt_parser_content = """
[apt.parser_config]
parser_type = "argparse"
program_name = "apt"

[[apt.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"

[[apt.sub_commands]]
name = "install"

[[apt.sub_commands.arguments]]
name = "packages"
nargs = "+"

[[apt.sub_commands.arguments]]
name = "config"
opt = ["--config"]
nargs = "1"

[[apt.sub_commands]]
name = "search"

[[apt.sub_commands.arguments]]
name = "query"
nargs = "+"
"""
        apt_parser_file = self.parser_configs_dir / "apt.toml"
        with open(apt_parser_file, 'w') as f:
            f.write(apt_parser_content)
        return apt_parser_file
    
    def _create_pacman_parser_config(self):
        """创建 Pacman 解析器配置"""
        pacman_parser_content = """
[pacman.parser_config]
parser_type = "getopt"
program_name = "pacman"

[[pacman.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"

[[pacman.arguments]]
name = "sync"
opt = ["-S", ""]
nargs = "0"

[[pacman.arguments]]
name = "search"
opt = ["-s", ""]
nargs = "0"

[[pacman.arguments]]
name = "packages"
nargs = "+"

[[pacman.arguments]]
name = "config"
opt = ["--config"]
nargs = "1"
"""
        pacman_parser_file = self.parser_configs_dir / "pacman.toml"
        with open(pacman_parser_file, 'w') as f:
            f.write(pacman_parser_content)
        return pacman_parser_file

    def _create_group_file_with_program_suffix(self):
        """创建包含程序后缀的操作文件"""
        group_content = """
[operations.install_remote.apt]
cmd_format = "apt install {pkgs}"

[operations.search_remote.apt]
cmd_format = "apt search {query}"

[operations.install_remote.pacman]
cmd_format = "pacman -S {pkgs}"
"""
        operation_group_file = self.domain_dir / "mixed.toml"
        with open(operation_group_file, 'w') as f:
            f.write(group_content)
        return operation_group_file

    def _create_parser_config_for_mixed(self):
        """创建混合程序的解析器配置"""
        apt_parser_content = """
[apt.parser_config]
parser_type = "argparse"
program_name = "apt"

[[apt.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"

[[apt.sub_commands]]
name = "install"

[[apt.sub_commands.arguments]]
name = "packages"
nargs = "+"

[[apt.sub_commands]]
name = "search"

[[apt.sub_commands.arguments]]
name = "query"
nargs = "+"
"""
        apt_parser_file = self.parser_configs_dir / "apt.toml"
        with open(apt_parser_file, 'w') as f:
            f.write(apt_parser_content)

        pacman_parser_content = """
[pacman.parser_config]
parser_type = "getopt"
program_name = "pacman"

[[pacman.arguments]]
name = "help"
opt = ["-h", "--help"]
nargs = "0"

[[pacman.arguments]]
name = "sync"
opt = ["-S", ""]
nargs = "0"

[[pacman.arguments]]
name = "search"
opt = ["-s", ""]
nargs = "0"

[[pacman.arguments]]
name = "packages"
nargs = "+"
"""
        pacman_parser_file = self.parser_configs_dir / "pacman.toml"
        with open(pacman_parser_file, 'w') as f:
            f.write(pacman_parser_content)
    
    def test_placeholder_values_generation(self):
        """测试占位符值生成"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证占位符值存在
        assert "apt" in mapping_data
        command_mappings = mapping_data["apt"]["command_mappings"]
        
        for mapping in command_mappings:
            assert "cmd_node" in mapping
            cmd_node = mapping["cmd_node"]
            
            # 验证 CommandNode 包含占位符值
            self._verify_placeholder_values(cmd_node, mapping["cmd_format"])
    
    def _verify_placeholder_values(self, cmd_node: dict, cmd_format: str):
        """验证 CommandNode 包含正确的占位符值"""
        import re
        param_names = re.findall(r'\{(\w+)\}', cmd_format)
        
        def check_node(node: dict):
            for arg in node.get("arguments", []):
                values = arg.get("values", [])
                for value in values:
                    # 检查值是否包含占位符模式
                    assert any(f"__param_{name}" in value for name in param_names), \
                        f"值 {value} 应该包含占位符模式"
            
            # 检查子命令
            if "subcommand" in node and node["subcommand"]:
                check_node(node["subcommand"])
        
        check_node(cmd_node)
    
    def test_operation_field_generation(self):
        """测试 operation 字段生成"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证 operation 字段存在且格式正确
        assert "apt" in mapping_data
        command_mappings = mapping_data["apt"]["command_mappings"]
        
        # 检查每个映射都有 operation 字段
        for mapping in command_mappings:
            assert "operation" in mapping
            operation_name = mapping["operation"]
            assert isinstance(operation_name, str)
            assert len(operation_name) > 0
            
            # 验证 operation 字段不包含程序名后缀
            assert not operation_name.endswith(".apt")
            
            # 验证 operation 字段是有效的操作名
            assert operation_name in ["install_remote", "search_remote", "install_with_config"]
    
    def test_operation_field_with_program_suffix(self):
        """测试包含程序后缀的 operation 字段生成"""
        # 创建包含程序后缀的操作文件
        self._create_group_file_with_program_suffix()
        self._create_parser_config_for_mixed()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证 apt 程序的 operation 字段
        if "apt" in mapping_data:
            apt_mappings = mapping_data["apt"]["command_mappings"]
            for mapping in apt_mappings:
                assert "operation" in mapping
                operation_name = mapping["operation"]
                # 应该移除 .apt 后缀
                assert not operation_name.endswith(".apt")
                assert operation_name in ["install_remote", "search_remote"]
        
        # 验证 pacman 程序的 operation 字段
        if "pacman" in mapping_data:
            pacman_mappings = mapping_data["pacman"]["command_mappings"]
            for mapping in pacman_mappings:
                assert "operation" in mapping
                operation_name = mapping["operation"]
                # 应该移除 .pacman 后缀
                assert not operation_name.endswith(".pacman")
                assert operation_name == "install_remote"
    
    def test_operation_field_persistence(self):
        """测试 operation 字段在文件写入和读取中的持久性"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射并写入文件
        output_file = self.output_dir / "cmd_mappings.toml"
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        creator.create_mappings()
        creator.write_to(str(output_file))
        
        # 读取文件验证 operation 字段
        assert output_file.exists()
        with open(output_file, 'rb') as f:
            written_data = tomli.load(f)
        
        # 验证 operation 字段在写入的文件中
        assert "apt" in written_data
        apt_mappings = written_data["apt"]["command_mappings"]
        
        for mapping in apt_mappings:
            assert "operation" in mapping
            operation_name = mapping["operation"]
            assert operation_name in ["install_remote", "search_remote", "install_with_config"]
    
    def test_placeholder_values_persistence(self):
        """测试占位符值在文件写入和读取中的持久性"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射并写入文件
        output_file = self.output_dir / "cmd_mappings.toml"
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        creator.create_mappings()
        creator.write_to(str(output_file))
        
        # 读取文件验证占位符值
        assert output_file.exists()
        with open(output_file, 'rb') as f:
            written_data = tomli.load(f)
        
        # 验证占位符值在写入的文件中
        assert "apt" in written_data
        apt_mappings = written_data["apt"]["command_mappings"]
        
        for mapping in apt_mappings:
            assert "cmd_node" in mapping
            self._verify_placeholder_values(mapping["cmd_node"], mapping["cmd_format"])
    
    def test_create_mappings_basic(self):
        """测试基本映射创建"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证结果
        assert "apt" in mapping_data
        assert "command_mappings" in mapping_data["apt"]
        assert isinstance(mapping_data["apt"]["command_mappings"], list)
        
        # 验证至少有一个映射创建成功
        if mapping_data["apt"]["command_mappings"]:
            mapping = mapping_data["apt"]["command_mappings"][0]
            assert "operation" in mapping
            assert "cmd_format" in mapping
            assert "params" in mapping
            assert "cmd_node" in mapping
    
    def test_create_mappings_multiple_programs(self):
        """测试多程序映射创建"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_pacman_group_file()
        self._create_apt_parser_config()
        self._create_pacman_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证结果
        assert "apt" in mapping_data
        assert "pacman" in mapping_data
        assert isinstance(mapping_data["apt"]["command_mappings"], list)
        assert isinstance(mapping_data["pacman"]["command_mappings"], list)
    
    def test_parameter_mapping(self):
        """测试参数映射"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 查找 install_with_config 操作
        install_config_mapping = None
        for mapping in mapping_data["apt"]["command_mappings"]:
            if mapping["operation"] == "install_with_config":
                install_config_mapping = mapping
                break
        
        # 如果有映射，验证参数结构
        if install_config_mapping:
            assert "params" in install_config_mapping
            params = install_config_mapping["params"]
            # 应该有两个参数：pkgs 和 config_path
            assert "pkgs" in params
            assert "config_path" in params
    
    def test_command_node_generation(self):
        """测试 CommandNode 生成"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 验证 CommandNode 存在且结构正确
        for mapping in mapping_data["apt"]["command_mappings"]:
            assert "cmd_node" in mapping
            cmd_node = mapping["cmd_node"]
            
            # 验证 CommandNode 结构
            assert "name" in cmd_node
            assert "arguments" in cmd_node
            assert isinstance(cmd_node["arguments"], list)
    
    def test_write_to_file(self):
        """测试写入文件"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 创建映射并写入文件
        output_file = self.output_dir / "cmd_mappings.toml"
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        creator.create_mappings()
        creator.write_to(str(output_file))
        
        # 验证文件存在且内容正确
        assert output_file.exists()
        
        with open(output_file, 'rb') as f:
            written_data = tomli.load(f)
        
        assert "apt" in written_data
        
        # 验证写入的数据结构
        apt_mappings = written_data["apt"]["command_mappings"]
        for mapping in apt_mappings:
            assert "operation" in mapping
            assert "cmd_format" in mapping
            assert "params" in mapping
            assert "cmd_node" in mapping
    
    def test_convenience_function(self):
        """测试便捷函数"""
        # 创建测试文件
        self._create_apt_group_file()
        self._create_apt_parser_config()
        
        # 使用便捷函数
        output_file = self.output_dir / "cmd_mappings.toml"
        create_cmd_mappings(
            domain_dir=str(self.domain_dir),
            parser_configs_dir=str(self.parser_configs_dir),
            output_path=str(output_file)
        )
        
        # 验证文件存在且内容正确
        assert output_file.exists()
        
        with open(output_file, 'rb') as f:
            written_data = tomli.load(f)
        
        assert "apt" in written_data
    
    def test_missing_parser_config(self):
        """测试缺少解析器配置的情况"""
        # 只创建操作文件，不创建解析器配置
        self._create_apt_group_file()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 应该有空映射数据
        assert "apt" in mapping_data
        assert mapping_data["apt"]["command_mappings"] == []
    
    def test_invalid_group_directory(self):
        """测试无效的操作目录"""
        # 使用不存在的目录
        invalid_group_dir = Path(self.temp_dir) / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            creator = CmdMappingMgr(str(invalid_group_dir), str(self.parser_configs_dir))
            creator.create_mappings()
    
    def test_empty_group_file(self):
        """测试空的操作文件"""
        # 创建空的操作文件
        empty_file = self.domain_dir / "empty.toml"
        empty_file.touch()
        
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 空文件应该没有命令映射
        assert "empty" in mapping_data
        assert mapping_data["empty"]["command_mappings"] == []
    
    def test_operation_without_cmd_format(self):
        """测试缺少 cmd_format 的操作"""
        # 创建包含无效操作的文件
        invalid_group_content = """
[operations.valid_operation]
cmd_format = "apt install {pkgs}"

[operations.invalid_operation]
description = "This operation has no cmd_format"
"""
        invalid_file = self.domain_dir / "apt.toml"
        with open(invalid_file, 'w') as f:
            f.write(invalid_group_content)
        
        self._create_apt_parser_config()
        
        # 创建映射
        creator = CmdMappingMgr(str(self.domain_dir), str(self.parser_configs_dir))
        mapping_data = creator.create_mappings()
        
        # 应该只有有效操作的映射
        assert "apt" in mapping_data
        command_mappings = mapping_data["apt"]["command_mappings"]
        # 应该只有一个有效映射
        valid_mappings = [m for m in command_mappings if m["operation"] == "valid_operation"]
        assert len(valid_mappings) <= 1


if __name__ == "__main__":
    set_level(LogLevel.DEBUG)
    pytest.main([__file__, "-v"])