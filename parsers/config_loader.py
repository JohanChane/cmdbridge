"""
配置加载器 - 从 TOML 配置数据加载程序解析器配置
支持 id 和 include_arguments_and_subcmds 功能，使用预处理解决依赖问题
"""

from typing import Dict, Any, Optional, List
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
        self._id_templates = {}  # 存储有 id 的子命令模板（预处理后的）
    
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
            parser_type_str = "argparse"    # default parser
        
        try:
            parser_type = ParserType(parser_type_str)
        except ValueError:
            raise ValueError(f"不支持的解析器类型: {parser_type_str}")
        
        # 解析程序名称
        config_program_name = parser_section.get("program_name", program_name)
        
        # 步骤1: 收集所有有 id 的子命令节点
        self._collect_id_templates(program_config)
        
        # 步骤2: 预处理 id 子命令节点，递归解析 include_arguments_and_subcmds
        self._preprocess_id_templates()
        
        # 解析全局参数
        arguments = []
        if "arguments" in program_config:
            arguments = self._parse_arguments(program_config["arguments"])
        
        # 步骤3: 解析子命令，处理 include_arguments_and_subcmds
        sub_commands = []
        if "sub_commands" in program_config:
            sub_commands = self._parse_sub_commands(program_config["sub_commands"])
        
        return ParserConfig(
            parser_type=parser_type,
            program_name=config_program_name,
            arguments=arguments,
            sub_commands=sub_commands
        )
    
    def _collect_id_templates(self, program_config: dict):
        """步骤1: 收集所有有 id 的子命令节点"""
        if "sub_commands" not in program_config:
            return
        
        def collect_recursive(sub_commands_data: list):
            for sub_cmd_data in sub_commands_data:
                if "id" in sub_cmd_data:
                    template_id = sub_cmd_data["id"]
                    # 深度复制原始数据
                    self._id_templates[template_id] = sub_cmd_data.copy()
                
                # 递归收集嵌套子命令
                if "sub_commands" in sub_cmd_data:
                    collect_recursive(sub_cmd_data["sub_commands"])
        
        collect_recursive(program_config["sub_commands"])
    
    def _preprocess_id_templates(self):
        """步骤2: 预处理 id 子命令节点，递归解析 include_arguments_and_subcmds"""
        processed = set()
        
        def preprocess_template(template_id: str):
            if template_id in processed:
                return
            
            template_data = self._id_templates[template_id]
            
            # 如果模板有 include_arguments，递归处理
            if "include_arguments_and_subcmds" in template_data:
                referenced_id = template_data["include_arguments_and_subcmds"]
                
                # 确保引用的模板已预处理
                if referenced_id in self._id_templates:
                    preprocess_template(referenced_id)
                    
                    # 复制引用的模板内容
                    referenced_template = self._id_templates[referenced_id]
                    
                    # 复制 arguments
                    if "arguments" in referenced_template:
                        template_data["arguments"] = referenced_template["arguments"].copy()
                    
                    # 复制 sub_commands
                    if "sub_commands" in referenced_template:
                        template_data["sub_commands"] = referenced_template["sub_commands"].copy()
                    
                    # 复制 description（如果存在）
                    if "description" in referenced_template:
                        template_data["description"] = referenced_template["description"]
                
                # 移除 include_arguments，标记为已处理
                template_data.pop("include_arguments_and_subcmds", None)
            
            processed.add(template_id)
        
        # 预处理所有模板
        for template_id in list(self._id_templates.keys()):
            preprocess_template(template_id)
    
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
        """步骤3: 解析子命令，处理 include_arguments_and_subcmds"""
        sub_commands = []
        
        for sub_cmd_data in sub_commands_data:
            sub_command = self._parse_single_sub_command(sub_cmd_data)
            sub_commands.append(sub_command)
        
        return sub_commands

    def _parse_single_sub_command(self, sub_cmd_data: dict) -> SubCommandConfig:
        """解析单个子命令配置"""
        # 获取最终配置数据
        final_data = self._get_final_sub_command_data(sub_cmd_data)
        
        # 创建基础对象
        sub_command = SubCommandConfig(
            name=final_data["name"],
            alias=final_data.get("alias", []),
            arguments=[],
            sub_commands=[],
            description=final_data.get("description")
        )
        
        # 替换需要解析的字段
        sub_command.arguments = self._parse_arguments(final_data.get("arguments", []))
        sub_command.sub_commands = self._parse_sub_commands(final_data.get("sub_commands", []))
        
        return sub_command

    def _get_final_sub_command_data(self, sub_cmd_data: dict) -> dict:
        """获取最终的子命令配置数据（处理模板引用）"""
        if "include_arguments_and_subcmds" not in sub_cmd_data:
            return sub_cmd_data
        
        template_id = sub_cmd_data["include_arguments_and_subcmds"]
        if template_id not in self._id_templates:
            raise ValueError(f"未找到模板: {template_id}")
        
        # 合并配置
        template_data = self._id_templates[template_id].copy()
        final_data = {**template_data, **sub_cmd_data}
        
        # 清理模板特定字段
        final_data.pop("id", None)
        final_data.pop("include_arguments_and_subcmds", None)
        
        return final_data


# 便捷函数（保持不变）
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