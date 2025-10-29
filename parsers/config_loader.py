"""
配置加载器 - 从 TOML 配置数据加载程序解析器配置
"""

from typing import Dict, Any
import tomli
from .types import ParserConfig, ParserType, ArgumentConfig, ArgumentCount, SubCommandConfig


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        初始化配置加载器
        
        Args:
            config_data: TOML 解析后的配置数据
        """
        self.config_data = config_data
    
    def load_parser_config(self, program_name: str) -> ParserConfig:
        """
        加载指定程序的解析器配置
        
        Args:
            program_name: 程序名称
            
        Returns:
            ParserConfig: 解析器配置对象
            
        Raises:
            ValueError: 配置格式错误
        """
        return self._parse_config_data(program_name, self.config_data)
    
    def _parse_config_data(self, program_name: str, config_data: dict) -> ParserConfig:
        """解析配置数据为 ParserConfig 对象"""
        # 检查程序配置是否存在
        if program_name not in config_data:
            raise ValueError(f"配置文件中缺少 {program_name} 部分")
        
        program_config = config_data[program_name]
        
        # 获取解析器配置部分
        if "parser_config" not in program_config:
            raise ValueError(f"配置文件中缺少 {program_name}.parser_config 部分")
        
        parser_section = program_config["parser_config"]
        
        # 解析解析器类型
        parser_type_str = parser_section.get("parser_type")
        if not parser_type_str:
            raise ValueError("缺少 parser_type 配置")
        
        try:
            parser_type = ParserType(parser_type_str)
        except ValueError:
            raise ValueError(f"不支持的解析器类型: {parser_type_str}")
        
        # 解析程序名称
        config_program_name = parser_section.get("program_name", program_name)
        
        # 解析全局参数
        arguments = []
        if "arguments" in program_config:
            arguments = self._parse_arguments(program_config["arguments"])
        
        # 解析子命令
        sub_commands = []
        if "sub_commands" in program_config:
            sub_commands = self._parse_sub_commands(program_config["sub_commands"])
        
        return ParserConfig(
            parser_type=parser_type,
            program_name=config_program_name,
            arguments=arguments,
            sub_commands=sub_commands
        )
    
    def _parse_arguments(self, arguments_data: list) -> list[ArgumentConfig]:
        """解析参数配置列表"""
        arguments = []
        
        for arg_data in arguments_data:
            # 解析 nargs
            nargs_str = arg_data.get("nargs")
            if not nargs_str:
                raise ValueError("参数配置中缺少 nargs")
            
            # 创建 ArgumentCount（会自动校验 nargs 字符串）
            nargs = ArgumentCount(nargs_str)
            
            # 解析 required（可选，默认 false）
            required = arg_data.get("required", False)
            
            argument = ArgumentConfig(
                name=arg_data.get("name", ""),
                opt=arg_data.get("opt", []),
                nargs=nargs,
                required=required,
                description=arg_data.get("description")
            )
            arguments.append(argument)
        
        return arguments
    
    def _parse_sub_commands(self, sub_commands_data: list) -> list[SubCommandConfig]:
        """递归解析子命令配置"""
        sub_commands = []
        
        for sub_cmd_data in sub_commands_data:
            sub_command_name = sub_cmd_data.get("name")
            if not sub_command_name:
                raise ValueError("子命令配置中缺少 name")
            
            # 解析子命令的参数
            sub_cmd_arguments = []
            if "arguments" in sub_cmd_data:
                sub_cmd_arguments = self._parse_arguments(sub_cmd_data["arguments"])
            
            # 🔧 递归解析嵌套子命令
            nested_sub_commands = []
            if "sub_commands" in sub_cmd_data:
                nested_sub_commands = self._parse_sub_commands(sub_cmd_data["sub_commands"])
            
            sub_command = SubCommandConfig(
                name=sub_command_name,
                arguments=sub_cmd_arguments,
                sub_commands=nested_sub_commands,  # 🔧 新增嵌套子命令
                description=sub_cmd_data.get("description")
            )
            sub_commands.append(sub_command)
        
        return sub_commands


# 便捷函数
def load_parser_config_from_data(config_data: Dict[str, Any], program_name: str) -> ParserConfig:
    """
    便捷函数：从配置数据加载指定程序的解析器配置
    
    Args:
        config_data: TOML 解析后的配置数据
        program_name: 程序名称
        
    Returns:
        ParserConfig: 解析器配置对象
    """
    loader = ConfigLoader(config_data)
    return loader.load_parser_config(program_name)


def load_parser_config_from_file(config_file: str, program_name: str) -> ParserConfig:
    """
    便捷函数：从配置文件加载指定程序的解析器配置
    
    Args:
        config_file: 配置文件路径
        program_name: 程序名称
        
    Returns:
        ParserConfig: 解析器配置对象
    """
    with open(config_file, 'rb') as f:
        config_data = tomli.load(f)
    
    return load_parser_config_from_data(config_data, program_name)