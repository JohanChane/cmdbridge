#!/usr/bin/env python3
"""
OperationMapping Core Functionality Tests
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

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cmdbridge.core.operation_mapping import OperationMapping
from cmdbridge.config.path_manager import PathManager


class TestOperationMapping:
    """OperationMapping Core Functionality Tests"""
    
    def setup_method(self):
        """Test setup"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Reset PathManager
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=self.temp_dir,
            cache_dir=self.temp_dir
        )
        
        # Create domain configuration directory
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test configuration
        self._create_test_config()
    
    def teardown_method(self):
        """Test cleanup"""
        shutil.rmtree(self.temp_dir)
        PathManager.reset_instance()
    
    def _create_test_config(self):
        """Create test configuration"""
        # Create cache directory
        cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache("package")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create operation to program mapping file
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
        
        # Create apt command format
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
        """Test basic command generation"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim git"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim git"
    
    def test_search_command(self):
        """Test search command"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="search",
            params={"query": "python"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt search python"
    
    def test_no_parameters_command(self):
        """Test command without parameters"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="update",
            params={},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt update"
    
    def test_nonexistent_operation(self):
        """Test non-existent operation"""
        mapping = OperationMapping()
        
        with pytest.raises(ValueError):
            mapping.generate_command(
                operation_name="nonexistent",
                params={},
                dst_operation_domain_name="package",
                dst_operation_group_name="apt"
            )
    
    def test_parameter_replacement(self):
        """Test parameter replacement"""
        mapping = OperationMapping()
        
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim"
        
        # Test multiple parameters
        cmd = mapping.generate_command(
            operation_name="install",
            params={"pkgs": "vim git curl"},
            dst_operation_domain_name="package",
            dst_operation_group_name="apt"
        )
        
        assert cmd == "apt install vim git curl"


def run_tests():
    """Run all tests"""
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
                print(f"✅ {test.__name__} - Passed")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__} - Failed: {e}")
        
        print(f"\n📊 Test results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print("💥 Some tests failed, please check")
            
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    run_tests()