# cmdbridge/core/operation_mapping.py

import os
from typing import Dict, Any, Optional
from pathlib import Path
import tomli

from log import debug, info, warning, error
from utils import ConfigUtils


class OperationMapping:
    """
    操作映射器 - 根据操作名称和参数生成目标命令
    
    输入: operation_name, params, dst_operation_domain_name, dst_operation_group_name
    输出: cmdline (命令行字符串)
    """


    def __init__(self, configs_dir: str, cache_dir: str):
        """
        初始化操作映射器
        
        Args:
            configs_dir: 配置目录路径
            cache_dir: 缓存目录路径
        """
        self.configs_dir = Path(configs_dir)
        self.cache_dir = Path(cache_dir)
        self.operations_cache = {}  # 缓存加载的操作配置
        # 初始化配置工具 - 使用正确的路径
        # cache_dir = self.configs_dir.parent / "cache"
        # self.config_utils = ConfigUtils(
        #     configs_dir=self.configs_dir,
        #     cache_dir=cache_dir
        # )

    def generate_command(self, operation_name: str, params: Dict[str, str],
                        dst_operation_domain_name: str, 
                        dst_operation_group_name: str) -> str:
        """
        生成目标命令
        
        Args:
            operation_name: 操作名称
            params: 参数字典
            dst_operation_domain_name: 目标操作组名称 (如 "package", "process")
            dst_operation_group_name: 目标程序名 (如 "apt", "pacman")
            
        Returns:
            str: 生成的命令行字符串
            
        Raises:
            ValueError: 如果操作不存在或参数不匹配
        """
        debug(f"开始生成命令: 操作={operation_name}, 目标组={dst_operation_domain_name}, 目标程序={dst_operation_group_name}")
        debug(f"参数: {params}")
        
        # 1. 加载操作配置
        operation_config = self._load_operation_config(
            dst_operation_domain_name, dst_operation_group_name, operation_name
        )
        
        if not operation_config:
            raise ValueError(f"未找到操作配置: {operation_name} for {dst_operation_group_name}")
        
        # 2. 获取命令格式
        cmd_format = operation_config.get("cmd_format")
        if not cmd_format:
            raise ValueError(f"操作 {operation_name} 缺少 cmd_format")
        
        debug(f"使用命令格式: {cmd_format}")
        
        # 3. 替换参数，直接返回字符串
        cmdline = self._replace_parameters(cmd_format, params)
        
        info(f"生成命令成功: {cmdline}")
        return cmdline
        
    def _load_operation_config(self, domain_name: str, program_name: str, 
                            operation_name: str) -> Optional[Dict[str, Any]]:
        """加载操作配置 - 直接从缓存目录读取合并后的配置"""
        cache_key = f"{domain_name}.{program_name}.{operation_name}"
        
        if cache_key in self.operations_cache:
            return self.operations_cache[cache_key]
        
        # 使用传递的缓存目录
        cache_file = self.cache_dir / "domains" / f"{domain_name}.domain" / f"{program_name}.toml"
        
        debug(f"查找缓存文件: {cache_file}")
        debug(f"缓存文件是否存在: {cache_file.exists()}")
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = tomli.load(f)
                
                debug(f"缓存文件内容: {cached_data}")
                
                operations = cached_data.get("operations", {})
                debug(f"所有操作键: {list(operations.keys())}")
                
                # 查找操作配置
                operation_config = None
                
                # 首先尝试直接的操作名
                if operation_name in operations:
                    op_data = operations[operation_name]
                    debug(f"找到操作数据: {op_data}")
                    
                    # 检查是否是嵌套结构：{'apt': {'cmd_format': ...}}
                    if isinstance(op_data, dict) and program_name in op_data:
                        operation_config = op_data[program_name]
                        debug(f"从嵌套结构中提取 {program_name} 的配置: {operation_config}")
                    # 如果是直接配置：{'cmd_format': ...}
                    elif isinstance(op_data, dict) and 'cmd_format' in op_data:
                        operation_config = op_data
                        debug(f"使用直接配置: {operation_config}")
                
                if operation_config:
                    self.operations_cache[cache_key] = operation_config
                    debug(f"最终操作配置: {operation_config}")
                    return operation_config
                else:
                    debug(f"未找到操作 {operation_name} 的配置")
                    
            except Exception as e:
                warning(f"加载缓存配置失败: {e}")
                import traceback
                debug(f"详细错误: {traceback.format_exc()}")
        
        warning(f"未找到操作配置: {operation_name} for {program_name} (缓存文件: {cache_file})")
        return None
    
    def _replace_parameters(self, cmd_format: str, params: Dict[str, str]) -> str:
        """替换命令格式中的参数占位符"""
        result = cmd_format
        
        for param_name, param_value in params.items():
            placeholder = "{" + param_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, param_value)
                debug(f"替换参数: {placeholder} -> {param_value}")
            else:
                warning(f"参数占位符 {placeholder} 在命令格式中未找到")
        
        # 检查是否还有未替换的占位符
        import re
        remaining_placeholders = re.findall(r'\{(\w+)\}', result)
        if remaining_placeholders:
            warning(f"命令格式中仍有未替换的占位符: {remaining_placeholders}")
        
        return result


# 便捷函数
def create_operation_mapping(configs_dir: str) -> OperationMapping:
    """
    创建操作映射器实例
    
    Args:
        configs_dir: 配置目录路径
        
    Returns:
        OperationMapping: 操作映射器实例
    """
    return OperationMapping(configs_dir)


def generate_command_from_operation(operation_name: str, params: Dict[str, str],
                                  dst_operation_domain_name: str,
                                  dst_operation_group_name: str,
                                  configs_dir: str) -> str:
    """
    便捷函数：直接从操作生成命令
    
    Args:
        operation_name: 操作名称
        params: 参数字典
        dst_operation_domain_name: 目标操作组名称
        dst_operation_group_name: 目标程序名
        configs_dir: 配置目录路径
        
    Returns:
        str: 生成的命令行字符串
    """
    mapping = OperationMapping(configs_dir)
    return mapping.generate_command(operation_name, params, 
                                  dst_operation_domain_name, dst_operation_group_name)