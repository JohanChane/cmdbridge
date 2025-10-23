# cmdbridge/core/operation_mapping.py

import os
from typing import Dict, Any, Optional
from pathlib import Path
import tomli

from log import debug, info, warning, error


class OperationMapping:
    """
    操作映射器 - 根据操作名称和参数生成目标命令
    
    输入: operation_name, params, dst_operation_groups_name, dst_operation_group_name
    输出: cmdline (命令行字符串)
    """
    
    def __init__(self, configs_dir: str):
        """
        初始化操作映射器
        
        Args:
            configs_dir: 配置目录路径，包含 *.groups 文件夹
        """
        self.configs_dir = Path(configs_dir)
        self.operations_cache = {}  # 缓存加载的操作配置
    
    def generate_command(self, operation_name: str, params: Dict[str, str],
                        dst_operation_groups_name: str, 
                        dst_operation_group_name: str) -> str:
        """
        生成目标命令
        
        Args:
            operation_name: 操作名称
            params: 参数字典
            dst_operation_groups_name: 目标操作组名称 (如 "package", "process")
            dst_operation_group_name: 目标程序名 (如 "apt", "pacman")
            
        Returns:
            str: 生成的命令行字符串
            
        Raises:
            ValueError: 如果操作不存在或参数不匹配
        """
        debug(f"开始生成命令: 操作={operation_name}, 目标组={dst_operation_groups_name}, 目标程序={dst_operation_group_name}")
        debug(f"参数: {params}")
        
        # 1. 加载操作配置
        operation_config = self._load_operation_config(
            dst_operation_groups_name, dst_operation_group_name, operation_name
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
    
    def _load_operation_config(self, groups_name: str, program_name: str, 
                              operation_name: str) -> Optional[Dict[str, Any]]:
        """加载操作配置"""
        cache_key = f"{groups_name}.{program_name}.{operation_name}"
        
        if cache_key in self.operations_cache:
            return self.operations_cache[cache_key]
        
        # 构建配置文件路径
        groups_dir = self.configs_dir / f"{groups_name}.groups"
        config_file = groups_dir / f"{program_name}.toml"
        
        if not config_file.exists():
            warning(f"配置文件不存在: {config_file}")
            return None
        
        try:
            with open(config_file, 'rb') as f:
                config_data = tomli.load(f)
            
            # 查找操作配置
            operations = config_data.get("operations", {})
            
            # 查找匹配的操作键
            operation_key = None
            for key in operations.keys():
                # 支持两种格式: "operation_name.program" 或 "operation_name"
                key_parts = key.split('.')
                if len(key_parts) == 2 and key_parts[0] == operation_name and key_parts[1] == program_name:
                    operation_key = key
                    break
                elif len(key_parts) == 1 and key_parts[0] == operation_name:
                    operation_key = key
                    break
            
            if operation_key and operation_key in operations:
                operation_config = operations[operation_key]
                self.operations_cache[cache_key] = operation_config
                debug(f"加载操作配置: {operation_key} -> {operation_config}")
                return operation_config
            
            warning(f"未找到操作配置: {operation_name} in {config_file}")
            return None
            
        except Exception as e:
            error(f"加载操作配置失败: {e}")
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
                                  dst_operation_groups_name: str,
                                  dst_operation_group_name: str,
                                  configs_dir: str) -> str:
    """
    便捷函数：直接从操作生成命令
    
    Args:
        operation_name: 操作名称
        params: 参数字典
        dst_operation_groups_name: 目标操作组名称
        dst_operation_group_name: 目标程序名
        configs_dir: 配置目录路径
        
    Returns:
        str: 生成的命令行字符串
    """
    mapping = OperationMapping(configs_dir)
    return mapping.generate_command(operation_name, params, 
                                  dst_operation_groups_name, dst_operation_group_name)