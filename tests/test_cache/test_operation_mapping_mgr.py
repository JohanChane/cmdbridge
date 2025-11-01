#!/usr/bin/env python3
"""
OperationMappingMgr Core Functionality Tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import tomli_w
import sys

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.cache.operation_mapping_mgr import OperationMappingMgr, create_operation_mappings_for_domain
from cmdbridge.config.path_manager import PathManager


class TestOperationMappingMgrSimple:
    """OperationMappingMgr simplified test class"""
    
    def setup_method(self):
        """Test setup"""
        self.temp_dir = tempfile.mkdtemp(prefix="cmdbridge_test_")
        
        # Reset PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # Create minimal test configuration
        self._create_minimal_config()
    
    def teardown_method(self):
        """Test cleanup"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_minimal_config(self):
        """Create minimal test configuration"""
        # Create package.domain directory
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # Create domain base file
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
        
        base_file = self.path_manager.get_domain_base_path_of_config("package")
        with open(base_file, 'wb') as f:
            tomli_w.dump(base_config, f)
        
        # Create apt.toml configuration file
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
        
        # Create pacman.toml configuration file
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
        """Test basic mapping creation"""
        print("🧪 Testing basic mapping creation...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        
        # Verify returned data structure
        assert "operation_to_program" in mapping_data
        assert "command_formats_by_group" in mapping_data
        
        operation_to_program = mapping_data["operation_to_program"]
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # Verify basic operation mapping
        assert "install" in operation_to_program
        assert "search" in operation_to_program
        assert "update" in operation_to_program
        
        # Verify operation groups
        assert "apt" in command_formats_by_group
        assert "pacman" in command_formats_by_group
        
        print("✅ Basic mapping creation test passed")
    
    def test_operation_to_program_structure(self):
        """Test operation to program mapping structure"""
        print("🧪 Testing operation to program mapping structure...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        operation_to_program = mapping_data["operation_to_program"]
        
        # Verify install operation mapping
        assert "install" in operation_to_program
        install_mapping = operation_to_program["install"]
        
        assert "apt" in install_mapping
        assert "pacman" in install_mapping
        
        # Verify program lists
        assert "apt" in install_mapping["apt"]
        assert "pacman" in install_mapping["pacman"]
        
        print("✅ Operation to program mapping structure test passed")
    
    def test_command_formats_collection(self):
        """Test command formats collection"""
        print("🧪 Testing command formats collection...")
        
        creator = OperationMappingMgr("package")
        mapping_data = creator.create_mappings()
        command_formats_by_group = mapping_data["command_formats_by_group"]
        
        # Verify apt operation group command formats
        assert "apt" in command_formats_by_group
        apt_formats = command_formats_by_group["apt"]
        
        assert "apt" in apt_formats
        apt_commands = apt_formats["apt"]
        
        # Verify command format content
        assert "install" in apt_commands
        assert apt_commands["install"] == "apt install {pkgs}"
        assert "search" in apt_commands
        assert apt_commands["search"] == "apt search {query}"
        assert "update" in apt_commands
        assert apt_commands["update"] == "apt update"
        
        print("✅ Command formats collection test passed")
    
    def test_file_generation(self):
        """Test file generation"""
        print("🧪 Testing file generation...")
        
        # Use convenience function to create mapping, it will automatically generate files
        success = create_operation_mappings_for_domain("package")
        assert success
        
        # Verify main files were generated
        operation_to_program_file = self.path_manager.get_operation_to_program_path("package")
        assert operation_to_program_file.exists(), f"operation_to_program file should exist: {operation_to_program_file}"
        
        # Verify operation group files
        apt_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "apt", "apt"
        )
        assert apt_commands_file.exists(), f"apt command file should exist: {apt_commands_file}"
        
        pacman_commands_file = self.path_manager.get_operation_mappings_group_program_path_of_cache(
            "package", "pacman", "pacman"
        )
        assert pacman_commands_file.exists(), f"pacman command file should exist: {pacman_commands_file}"
        
        print("✅ File generation test passed")
    
    def test_program_name_extraction(self):
        """Test program name extraction"""
        print("🧪 Testing program name extraction...")
        
        creator = OperationMappingMgr("package")
        
        # Test normal command format
        config = {"cmd_format": "apt install {pkgs}"}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name == "apt"
        
        # Test complex command
        config = {"cmd_format": "custom-tool --option value"}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name == "custom-tool"
        
        # Test empty configuration
        config = {}
        program_name = creator._extract_program_from_cmd_format(config)
        assert program_name is None
        
        print("✅ Program name extraction test passed")
    
    def test_convenience_function(self):
        """Test convenience function"""
        print("🧪 Testing convenience function...")
        
        # Use convenience function to create mapping
        success = create_operation_mappings_for_domain("package")
        assert success
        
        # Verify return value is boolean
        assert isinstance(success, bool)
        
        print("✅ Convenience function test passed")


def run_tests():
    """Run all tests"""
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
                print(f"✅ {test.__name__} - Passed")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__} - Failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Test results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print("💥 Some tests failed, please check")
            
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    run_tests()