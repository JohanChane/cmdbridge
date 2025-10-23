# cmdbridge/core/operation_mapping.py

import tomli
from typing import Dict, List, Optional
from pathlib import Path

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class OperationMapping:
    """操作映射器 - 根据操作名称和参数生成目标命令"""

    def __init__(self):
        """初始化操作映射器"""
        # 直接使用 PathManager 单例
        self.path_manager = PathManager.get_instance()
        self.operation_to_program = {}
        self.command_formats = {}
        self._load_operation_mapping()

    def _load_operation_mapping(self) -> None:
        """从缓存目录加载分离的操作映射文件"""
        debug("开始从缓存加载操作映射...")
        
        domains = self.path_manager.list_domains()
        if not domains:
            warning("未找到任何领域配置")
            return
        
        for domain in domains:
            # 获取操作映射缓存目录
            cache_dir = self.path_manager.get_operation_mappings_cache_path(domain)
            
            # 1. 加载操作到程序映射文件
            operation_to_program_file = cache_dir / "operation_to_program.toml"
            if operation_to_program_file.exists():
                try:
                    with open(operation_to_program_file, 'rb') as f:
                        operation_data = tomli.load(f)
                    
                    if "operation_to_program" in operation_data:
                        for op_name, programs in operation_data["operation_to_program"].items():
                            if op_name not in self.operation_to_program:
                                self.operation_to_program[op_name] = []
                            # 去重并添加
                            for program in programs:
                                if program not in self.operation_to_program[op_name]:
                                    self.operation_to_program[op_name].append(program)
                            debug(f"加载操作映射: {op_name} -> {self.operation_to_program[op_name]}")
                            
                except Exception as e:
                    warning(f"加载操作到程序映射文件失败 {operation_to_program_file}: {e}")
            else:
                debug(f"操作到程序映射文件不存在: {operation_to_program_file}")
            
            # 2. 加载所有程序的命令格式文件
            for command_file in cache_dir.glob("*_commands.toml"):
                program_name = command_file.stem.replace("_commands", "")
                
                try:
                    with open(command_file, 'rb') as f:
                        command_data = tomli.load(f)
                    
                    if "commands" in command_data:
                        if program_name not in self.command_formats:
                            self.command_formats[program_name] = {}
                        self.command_formats[program_name].update(command_data["commands"])
                        debug(f"加载 {program_name} 命令格式: {len(command_data['commands'])} 个命令")
                            
                except Exception as e:
                    warning(f"加载命令格式文件失败 {command_file}: {e}")
        
        info(f"操作映射加载完成: {len(self.operation_to_program)} 个操作, {len(self.command_formats)} 个程序")

    def generate_command(self, operation_name: str, params: Dict[str, str],
                        dst_operation_domain_name: str, 
                        dst_operation_group_name: str) -> str:
        """
        生成目标命令
        
        Args:
            operation_name: 操作名称
            params: 参数字典
            dst_operation_domain_name: 目标领域名称
            dst_operation_group_name: 目标程序名称
            
        Returns:
            str: 生成的命令行字符串
            
        Raises:
            ValueError: 如果操作不支持或找不到命令格式
        """
        debug(f"开始生成命令: 操作={operation_name}, 目标程序={dst_operation_group_name}, 参数={params}")
        
        # 1. 检查操作是否支持目标程序
        supported_programs = self.operation_to_program.get(operation_name, [])
        if dst_operation_group_name not in supported_programs:
            raise ValueError(f"操作 {operation_name} 不支持程序 {dst_operation_group_name}，支持的程序: {supported_programs}")
        
        # 2. 从目标程序的命令格式文件中获取命令格式
        program_formats = self.command_formats.get(dst_operation_group_name, {})
        cmd_format = program_formats.get(operation_name)
        
        if not cmd_format:
            raise ValueError(f"未找到命令格式: {operation_name} for {dst_operation_group_name}")
        
        # 3. 替换参数
        debug(f"使用命令格式: {cmd_format}")
        cmdline = self._replace_parameters(cmd_format, params)
        
        info(f"生成命令成功: {cmdline}")
        return cmdline
    
    def _replace_parameters(self, cmd_format: str, params: Dict[str, str]) -> str:
        """
        替换命令格式中的参数占位符
        
        Args:
            cmd_format: 命令格式字符串
            params: 参数字典
            
        Returns:
            str: 替换后的命令字符串
        """
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

    def list_supported_operations(self, program_name: str) -> List[str]:
        """
        列出程序支持的所有操作
        
        Args:
            program_name: 程序名称
            
        Returns:
            List[str]: 支持的操作名称列表
        """
        supported_ops = []
        for op_name, programs in self.operation_to_program.items():
            if program_name in programs:
                supported_ops.append(op_name)
        
        debug(f"程序 {program_name} 支持 {len(supported_ops)} 个操作: {supported_ops}")
        return sorted(supported_ops)

    def list_supported_programs(self, operation_name: str) -> List[str]:
        """
        列出操作支持的所有程序
        
        Args:
            operation_name: 操作名称
            
        Returns:
            List[str]: 支持的程序名称列表
        """
        programs = self.operation_to_program.get(operation_name, [])
        debug(f"操作 {operation_name} 支持 {len(programs)} 个程序: {programs}")
        return sorted(programs)

    def get_all_operations(self) -> List[str]:
        """
        获取所有可用的操作名称
        
        Returns:
            List[str]: 所有操作名称列表
        """
        operations = list(self.operation_to_program.keys())
        debug(f"共有 {len(operations)} 个可用操作: {operations}")
        return sorted(operations)

    def get_all_programs(self) -> List[str]:
        """
        获取所有可用的程序名称
        
        Returns:
            List[str]: 所有程序名称列表
        """
        programs = list(self.command_formats.keys())
        debug(f"共有 {len(programs)} 个可用程序: {programs}")
        return sorted(programs)

    def is_operation_supported(self, operation_name: str, program_name: str) -> bool:
        """
        检查操作是否支持指定程序
        
        Args:
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            bool: 是否支持
        """
        supported = program_name in self.operation_to_program.get(operation_name, [])
        debug(f"操作 {operation_name} 支持程序 {program_name}: {supported}")
        return supported

    def get_command_format(self, operation_name: str, program_name: str) -> Optional[str]:
        """
        获取指定操作和程序的命令格式
        
        Args:
            operation_name: 操作名称
            program_name: 程序名称
            
        Returns:
            Optional[str]: 命令格式字符串，如果不存在则返回 None
        """
        program_formats = self.command_formats.get(program_name, {})
        cmd_format = program_formats.get(operation_name)
        debug(f"获取命令格式: {operation_name}.{program_name} -> {cmd_format}")
        return cmd_format

    def reload(self) -> None:
        """
        重新加载操作映射配置
        
        用于在配置更新后刷新内存中的映射数据
        """
        debug("重新加载操作映射...")
        self.operation_to_program.clear()
        self.command_formats.clear()
        self._load_operation_mapping()
        info("操作映射重新加载完成")


# 便捷函数
def create_operation_mapping() -> OperationMapping:
    """
    创建操作映射器实例
    
    Returns:
        OperationMapping: 操作映射器实例
    """
    return OperationMapping()


def generate_command_from_operation(operation_name: str, params: Dict[str, str],
                                  dst_operation_domain_name: str,
                                  dst_operation_group_name: str) -> str:
    """
    便捷函数：直接从操作生成命令
    
    Args:
        operation_name: 操作名称
        params: 参数字典
        dst_operation_domain_name: 目标领域名称
        dst_operation_group_name: 目标程序名
        
    Returns:
        str: 生成的命令行字符串
    """
    mapping = OperationMapping()
    return mapping.generate_command(operation_name, params, 
                                  dst_operation_domain_name, dst_operation_group_name)