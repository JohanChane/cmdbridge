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
        # Create a parent temporary directory
        self.parent_temp_dir = tempfile.mkdtemp()
        
        # Create separate subdirectories for config and cache under the same parent
        self.config_temp_dir = Path(self.parent_temp_dir) / "config"
        self.cache_temp_dir = Path(self.parent_temp_dir) / "cache"
        
        self.config_temp_dir.mkdir(parents=True, exist_ok=True)
        self.cache_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset PathManager with separate directories under same parent
        PathManager.reset_instance()
        self.path_manager = PathManager(
            config_dir=str(self.config_temp_dir),
            cache_dir=str(self.cache_temp_dir)
        )
        
        print(f"Test parent dir: {self.parent_temp_dir}")
        print(f"Test config dir: {self.config_temp_dir}")
        print(f"Test cache dir: {self.cache_temp_dir}")
        
        # Create domain configuration directory
        package_domain_dir = self.path_manager.get_operation_domain_dir_of_config("package")
        package_domain_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test configuration
        self._create_test_config()
    
    def teardown_method(self):
        """Test cleanup"""
        if self.parent_temp_dir and Path(self.parent_temp_dir).exists():
            shutil.rmtree(self.parent_temp_dir)
        PathManager.reset_instance()
    
    def _create_test_config(self):
        """Create test configuration"""
        # Create cache directory (in cache_temp_dir)
        cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache("package")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify cache directory is in cache_temp_dir
        assert str(cache_dir).startswith(str(self.cache_temp_dir)), "Cache directory should be in cache_temp_dir"
        
        # Create operation to program mapping file (in cache directory)
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
        
        # Verify operation to program file is in cache directory
        assert str(op_file).startswith(str(self.cache_temp_dir)), "operation_to_program file should be in cache directory"
        
        # Create apt command format (in cache directory)
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
        
        # Verify apt command file is in cache directory
        assert str(apt_file).startswith(str(self.cache_temp_dir)), "apt command file should be in cache directory"
    
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
    
    def test_directory_separation(self):
        """Test that config and cache directories are properly separated"""
        # Verify directories are different but under same parent
        assert self.config_temp_dir != self.cache_temp_dir, "Config and cache directories should be different"
        assert self.config_temp_dir.parent == self.cache_temp_dir.parent, "Config and cache should be under same parent"
        
        # Verify PathManager uses correct directories
        assert str(self.path_manager.config_dir) == str(self.config_temp_dir)
        assert str(self.path_manager.cache_dir) == str(self.cache_temp_dir)
        
        # Verify all created files are in cache directory, not config directory
        cache_dir = self.path_manager.get_operation_mappings_domain_dir_of_cache("package")
        assert str(cache_dir).startswith(str(self.cache_temp_dir)), "Cache files should be in cache directory"
        
        op_file = self.path_manager.get_operation_to_program_path("package")
        assert str(op_file).startswith(str(self.cache_temp_dir)), "operation_to_program file should be in cache directory"
        
        apt_file = self.path_manager.get_operation_mappings_group_program_path_of_cache("package", "apt", "apt")
        assert str(apt_file).startswith(str(self.cache_temp_dir)), "apt command file should be in cache directory"
        
        # Verify config files would be in config directory (if we created any)
        # For this test, we're only creating cache files, so no config files to verify


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
            test_instance.test_directory_separation,
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