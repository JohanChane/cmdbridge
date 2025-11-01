# cmdbridge/cache/parser_config_mgr.py
import tomli
import tomli_w
from typing import Dict, Any
from pathlib import Path

from parsers.config_loader import load_parser_config_from_file
from parsers.types import ParserConfig
from log import debug, info, warning, error
from ..config.path_manager import PathManager


class ParserConfigCacheMgr:
    """解析器配置缓存管理器"""
    
    def __init__(self):
        self.path_manager = PathManager.get_instance()
    
    def generate_parser_config_cache(self):
        """为所有程序生成预处理的参数配置缓存"""
        source_dir = self.path_manager.program_parser_config_dir
        cache_dir = self.path_manager.get_parser_config_dir_of_cache()
        
        # 确保缓存目录存在
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        for config_file in source_dir.glob("*.toml"):
            program_name = config_file.stem
            try:
                # 使用 ConfigLoader 加载和预处理配置
                parser_config = load_parser_config_from_file(str(config_file), program_name)
                
                # 使用对象的序列化方法
                serialized_data = parser_config.to_dict()
                
                # 存储到缓存目录
                cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
                with open(cache_file, 'wb') as f:
                    tomli_w.dump(serialized_data, f)
                    
                info(f"✅ 已生成 {program_name} 的解析器配置缓存")
                
            except Exception as e:
                error(f"❌ 生成 {program_name} 的解析器配置缓存失败: {e}")
                raise
    
    def load_from_cache(self, program_name: str) -> ParserConfig:
        """从缓存加载预处理后的 ParserConfig 对象"""
        cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
        
        if not cache_file.exists():
            raise ValueError(f"未找到 {program_name} 的解析器配置缓存，请先运行 cache refresh")
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = tomli.load(f)
            
            # 使用类的反序列化方法
            return ParserConfig.from_dict(cached_data)
            
        except Exception as e:
            error(f"加载 {program_name} 的解析器配置缓存失败: {e}")
            raise
    
    def cache_exists(self, program_name: str) -> bool:
        """检查指定程序的解析器配置缓存是否存在"""
        cache_file = self.path_manager.get_parser_config_path_of_cache(program_name)
        return cache_file.exists()