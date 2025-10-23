# cmdbridge/config/operation_mapping_creator.py

import tomli
import tomli_w
from typing import Dict, List, Any, Optional
from pathlib import Path

from log import debug, info, warning, error
from .path_manager import PathManager


class OperationMappingCreator:
    """操作映射创建器 - 生成分离的操作映射文件"""
    
    def __init__(self, domain_name: str):
        """
        初始化操作映射创建器
        
        Args:
            domain_name: 领域名称 (如 "package", "process")
        """
        # 使用单例 PathManager
        self.path_manager = PathManager.get_instance()
        self.domain_name = domain_name
    
    def create_mappings(self) -> bool:
        """
        为指定领域创建分离的操作映射文件
        
        Returns:
            bool: 创建是否成功
        """
        try:
            # 获取领域配置目录
            domain_config_dir = self.path_manager.get_config_operation_group_path(self.domain_name)
            if not domain_config_dir.exists():
                warning(f"领域配置目录不存在: {domain_config_dir}")
                return False
            
            # 获取操作映射缓存目录
            cache_dir = self.path_manager.get_operation_mappings_cache_path(self.domain_name)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 收集所有操作组文件
            operation_groups = {}
            command_formats_by_program = {}
            
            # 1. 首先加载领域基础文件
            base_file = self.path_manager.get_domain_base_config_path(self.domain_name)
            base_operations = {}
            if base_file.exists():
                try:
                    with open(base_file, 'rb') as f:
                        base_data = tomli.load(f)
                    if "operations" in base_data:
                        base_operations = base_data["operations"]
                    debug(f"加载基础操作定义: {base_file}")
                except Exception as e:
                    warning(f"解析基础操作文件 {base_file} 失败: {e}")
            else:
                warning(f"领域基础文件不存在: {base_file}")
            
            # 2. 遍历程序组目录中的所有程序文件
            for config_file in domain_config_dir.glob("*.toml"):
                program_name = config_file.stem
                debug(f"处理程序文件: {config_file}")
                
                try:
                    with open(config_file, 'rb') as f:
                        group_data = tomli.load(f)
                    
                    # 收集操作到程序的映射
                    if "operations" in group_data:
                        for operation_key, operation_config in group_data["operations"].items():
                            # 从 operation_key 提取操作名（移除程序后缀）
                            operation_parts = operation_key.split('.')
                            if len(operation_parts) > 1 and operation_parts[-1] == program_name:
                                operation_name = '.'.join(operation_parts[:-1])
                            else:
                                operation_name = operation_key
                            
                            # 添加到操作到程序映射
                            if operation_name not in operation_groups:
                                operation_groups[operation_name] = []
                            
                            if program_name not in operation_groups[operation_name]:
                                operation_groups[operation_name].append(program_name)
                            
                            # 按程序分组收集命令格式
                            if program_name not in command_formats_by_program:
                                command_formats_by_program[program_name] = {}
                            
                            if "cmd_format" in operation_config:
                                command_formats_by_program[program_name][operation_name] = operation_config["cmd_format"]
                                
                except Exception as e:
                    warning(f"解析程序文件 {config_file} 失败: {e}")
                    continue
            
            # 3. 验证所有程序实现的操作都在基础定义中有对应
            for operation_name in operation_groups.keys():
                if operation_name not in base_operations:
                    warning(f"操作 {operation_name} 在基础定义文件中未定义")
            
            # 生成分离的文件
            
            # 1. 操作到程序映射文件
            operation_to_program_file = cache_dir / "operation_to_program.toml"
            with open(operation_to_program_file, 'wb') as f:
                tomli_w.dump({"operation_to_program": operation_groups}, f)
            info(f"✅ 已生成 operation_to_program.toml 文件: {operation_to_program_file}")
            
            # 2. 为每个程序生成单独的命令格式文件
            for program_name, command_formats in command_formats_by_program.items():
                program_command_file = cache_dir / f"{program_name}_commands.toml"
                with open(program_command_file, 'wb') as f:
                    tomli_w.dump({"commands": command_formats}, f)
                info(f"✅ 已生成 {program_name}_commands.toml 文件: {program_command_file}")
            
            return True
            
        except Exception as e:
            error(f"生成操作映射文件失败: {e}")
            return False


# 便捷函数
def create_operation_mappings_for_domain(domain_name: str) -> bool:
    """
    便捷函数：为指定领域创建操作映射
    
    Args:
        domain_name: 领域名称
        
    Returns:
        bool: 创建是否成功
    """
    creator = OperationMappingCreator(domain_name)
    return creator.create_mappings()

def create_operation_mappings_for_all_domains() -> bool:
    """
    便捷函数：为所有领域创建操作映射
    
    Returns:
        bool: 所有领域创建是否成功
    """
    path_manager = PathManager.get_instance()
    domains = path_manager.list_domains()
    
    all_success = True
    for domain in domains:
        try:
            success = create_operation_mappings_for_domain(domain)
            if success:
                info(f"✅ 已完成 {domain} 领域的操作映射生成")
            else:
                error(f"❌ {domain} 领域的操作映射生成失败")
                all_success = False
        except Exception as e:
            error(f"❌ {domain} 领域的操作映射生成异常: {e}")
            all_success = False
    
    return all_success