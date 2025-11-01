#!/usr/bin/env python3
"""
测试解析器配置缓存管理器核心功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cmdbridge.cache.parser_config_mgr import ParserConfigCacheMgr
from cmdbridge.config.path_manager import PathManager
from parsers.types import ParserConfig, ParserType
import tomli_w
import tomli


def setup_test_parser_config():
    """设置测试解析器配置"""
    # 创建临时目录结构
    temp_dir = tempfile.mkdtemp()
    
    # 初始化 PathManager
    path_manager = PathManager(
        config_dir=temp_dir,
        cache_dir=temp_dir
    )
    
    # 创建程序解析器配置目录
    parser_config_dir = path_manager.program_parser_config_dir
    parser_config_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试解析器配置
    test_parser_config = {
        "test_program": {
            "parser_config": {
                "parser_type": "argparse",
                "program_name": "test_program"
            },
            "arguments": [
                {
                    "name": "help",
                    "opt": ["-h", "--help"],
                    "nargs": "0"
                }
            ]
        }
    }
    
    # 写入配置文件
    config_file = parser_config_dir / "test_program.toml"
    with open(config_file, 'wb') as f:
        tomli_w.dump(test_parser_config, f)
    
    return temp_dir, path_manager


def test_cache_generation_and_loading():
    """测试缓存生成和加载功能"""
    print("=== 测试缓存生成和加载 ===")
    
    temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # 创建缓存管理器
        cache_mgr = ParserConfigCacheMgr()
        
        # 生成缓存
        cache_mgr.generate_parser_config_cache()
        
        # 从缓存加载配置
        parser_config = cache_mgr.load_from_cache("test_program")
        
        # 验证加载的配置对象
        assert isinstance(parser_config, ParserConfig)
        assert parser_config.parser_type == ParserType.ARGPARSE
        assert parser_config.program_name == "test_program"
        assert len(parser_config.arguments) == 1
        
        print("✅ 缓存生成和加载测试通过")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_cache_file_content():
    """测试缓存文件内容"""
    print("\n=== 测试缓存文件内容 ===")
    
    temp_dir, path_manager = setup_test_parser_config()
    
    try:
        # 创建缓存管理器
        cache_mgr = ParserConfigCacheMgr()
        
        # 生成缓存
        cache_mgr.generate_parser_config_cache()
        
        # 验证缓存文件内容
        cache_file = path_manager.get_parser_config_path_of_cache("test_program")
        assert cache_file.exists()
        
        with open(cache_file, 'rb') as f:
            cached_data = tomli.load(f)
        
        # 验证基本结构
        assert "parser_type" in cached_data
        assert "program_name" in cached_data
        assert "arguments" in cached_data
        
        print("✅ 缓存文件内容测试通过")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("开始测试解析器配置缓存管理器核心功能...\n")
    
    try:
        test_cache_generation_and_loading()
        test_cache_file_content()
        
        print("\n🎉 所有核心功能测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())