# utils/config.py

import os, sys
from pathlib import Path
from typing import List, Dict, Any, Optional
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli
import shutil

from cmdbridge.config.path_manager import PathManager
from log import debug, info, warning, error


class ConfigMgr:
    """配置工具类 - 管理配置和缓存目录，包含所有功能实现"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigMgr, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化配置工具
        """
        if self._initialized:
            return
            
        # 直接使用 PathManager 单例
        self.path_manager = PathManager.get_instance()
        debug("初始化 ConfigMgr")
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'ConfigMgr':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
    
    def init_config(self) -> bool:
        """初始化用户配置"""
        try:
            # 获取包内默认配置路径
            default_configs_dir = self.path_manager.get_default_configs_dir()
            
            # 检查默认配置是否存在
            if not default_configs_dir.exists():
                error(f"默认配置目录不存在: {default_configs_dir}")
                return False
            
            info(f"初始化配置目录: {self.path_manager.config_dir}")
            info(f"初始化缓存目录: {self.path_manager.cache_dir}")
            
            # 复制领域基础文件
            base_files = list(default_configs_dir.glob("*.domain.base.toml"))
            if base_files:
                info("复制领域基础文件...")
                for base_file in base_files:
                    dest_file = self.path_manager.config_dir / base_file.name
                    if dest_file.exists():
                        info(f"  跳过已存在的: {base_file.name}")
                    else:
                        shutil.copy2(base_file, dest_file)
                        info(f"  已复制: {base_file.name}")
            else:
                warning("未找到任何领域基础文件")
            
            # 复制领域配置目录
            domain_dirs = list(default_configs_dir.glob("*.domain"))
            if domain_dirs:
                info("复制领域配置目录...")
                for domain_dir in domain_dirs:
                    # 检查是否是目录（排除 .domain.base.toml 文件）
                    if domain_dir.is_dir():
                        dest_domain_dir = self.path_manager.get_operation_domain_dir_of_config(domain_dir.stem)
                        if dest_domain_dir.exists():
                            info(f"  跳过已存在的: {domain_dir.name}")
                        else:
                            shutil.copytree(domain_dir, dest_domain_dir)
                            info(f"  已复制: {domain_dir.name}")
            else:
                warning("未找到任何领域配置目录")
            
            # 复制 program_parser_configs
            parser_configs_dir = default_configs_dir / "program_parser_configs"
            if parser_configs_dir.exists():
                dest_parser_dir = self.path_manager.program_parser_config_dir
                
                # 确保目标目录存在
                dest_parser_dir.mkdir(parents=True, exist_ok=True)
                
                info(f"复制解析器配置从 {parser_configs_dir} 到 {dest_parser_dir}")
                
                # 复制所有 .toml 文件
                config_files = list(parser_configs_dir.glob("*.toml"))
                if config_files:
                    copied_count = 0
                    for config_file in config_files:
                        dest_file = dest_parser_dir / config_file.name
                        if not dest_file.exists():
                            shutil.copy2(config_file, dest_file)
                            info(f"  已复制: {config_file.name}")
                            copied_count += 1
                        else:
                            info(f"  跳过已存在的: {config_file.name}")
                    
                    info(f"解析器配置复制完成: {copied_count} 个文件")
                else:
                    warning(f"源目录中没有找到任何 .toml 文件: {parser_configs_dir}")
            else:
                error(f"源解析器配置目录不存在: {parser_configs_dir}")
                return False
            
            # 复制 config.toml
            default_config_file = default_configs_dir / "config.toml"
            if default_config_file.exists():
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    shutil.copy2(default_config_file, dest_config_file)
                    info("  已复制: config.toml")
                else:
                    info("  跳过已存在的: config.toml")
            else:
                # 创建默认的 config.toml
                default_config = """[global_settings]"""
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    with open(dest_config_file, 'w') as f:
                        f.write(default_config)
                    info("  已创建默认: config.toml")
            
            return True
        except Exception as e:
            error(f"初始化配置失败: {e}")
            return False