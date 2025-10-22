# cmdbridge/config/cmd_mapping_creator.py

import os
import tomli
import tomli_w
from typing import Dict, List, Any, Optional
from pathlib import Path

from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType
from parsers.argparse_parser import ArgparseParser
from parsers.getopt_parser import GetoptParser
from parsers.config_loader import load_parser_config_from_file

from log import debug, info, warning, error


class CmdMappingCreator:
    """命令映射创建器 - 生成包含 CommandNode 和 operation 字段的映射配置"""
    
    def __init__(self, ops_dir: str, parser_configs_dir: str):
        """
        初始化命令映射创建器
        
        Args:
            ops_dir: 操作接口文件夹路径 (如 package.ops, process.ops)
            parser_configs_dir: 解析器配置文件夹路径
        """
        self.ops_dir = Path(ops_dir)
        self.parser_configs_dir = Path(parser_configs_dir)
        self.mapping_data = {}
    
    def create_mappings(self) -> Dict[str, Any]:
        """
        创建命令映射
        
        Returns:
            Dict[str, Any]: 映射数据，包含 operation 字段
        """
        debug(f"开始创建命令映射，操作目录: {self.ops_dir}")
        
        if not self.ops_dir.exists():
            error(f"操作目录不存在: {self.ops_dir}")
            raise FileNotFoundError(f"操作目录不存在: {self.ops_dir}")
        
        # 处理所有操作文件
        for ops_file in self.ops_dir.glob("*.toml"):
            debug(f"处理操作文件: {ops_file}")
            self._process_ops_file(ops_file)
        
        debug("命令映射创建完成")
        return self.mapping_data
    
    def _process_ops_file(self, ops_file: Path):
        """处理单个操作文件"""
        try:
            with open(ops_file, 'rb') as f:
                ops_data = tomli.load(f)
        except (tomli.TOMLDecodeError, Exception) as e:
            warning(f"无法解析操作文件 {ops_file}: {e}")
            return
        
        # 获取程序名称（从文件名）
        program_name = ops_file.stem
        debug(f"处理程序: {program_name}")
        
        if program_name not in self.mapping_data:
            self.mapping_data[program_name] = {"command_mappings": []}
        
        # 处理所有操作
        if "operations" in ops_data:
            for operation_key, operation_config in ops_data["operations"].items():
                debug(f"处理操作键: {operation_key}")
                self._process_operation(program_name, operation_key, operation_config)
        else:
            debug(f"文件 {ops_file} 中没有 operations 部分")
    
    def _process_operation(self, program_name: str, operation_key: str, operation_config: Dict[str, Any]):
        """处理单个操作"""
        if "cmd_format" not in operation_config:
            warning(f"操作 {operation_key} 缺少 cmd_format，跳过")
            return
        
        cmd_format = operation_config["cmd_format"]
        debug(f"分析命令格式: {cmd_format}")
        
        # 从 operation_key 提取 operation_name
        # operation_key 格式可能是 "install_remote.apt" 或 "install_remote"
        operation_parts = operation_key.split('.')
        if len(operation_parts) > 1 and operation_parts[-1] == program_name:
            # 如果 operation_key 包含程序名，如 "install_remote.apt"
            operation_name = '.'.join(operation_parts[:-1])
        else:
            # 如果 operation_key 不包含程序名，如 "install_remote"
            operation_name = operation_key
        
        debug(f"提取操作名: {operation_name}")
        
        # 生成示例命令并解析得到 CommandNode
        cmd_node, param_mapping = self._parse_command_and_map_params(cmd_format, program_name)
        if not cmd_node:
            error(f"无法解析命令: {cmd_format}")
            return
        
        # 创建映射条目，包含 operation 字段
        mapping_entry = {
            "operation": operation_name,
            "cmd_format": cmd_format,
            "params": param_mapping,
            "cmd_node": self._serialize_command_node(cmd_node)
        }
        
        self.mapping_data[program_name]["command_mappings"].append(mapping_entry)
        debug(f"为 {program_name} 创建映射: {operation_name}, {len(param_mapping)} 个参数")
    
    def _parse_command_and_map_params(self, cmd_format: str, program_cmd: str) -> tuple[Optional[CommandNode], Dict[str, Any]]:
        """解析命令并映射参数"""
        # 加载解析器配置
        parser_config = self._load_parser_config(program_cmd)
        if not parser_config:
            return None, {}
        
        # 生成示例命令
        example_command = self._generate_example_command(cmd_format, parser_config)
        
        # 解析命令得到 CommandNode
        cmd_node = self._parse_command(parser_config, example_command)
        if not cmd_node:
            return None, {}
        
        # 标记占位符参数
        self._mark_placeholder_args(cmd_node, cmd_format)
        
        # 分析参数映射
        param_mapping = self._analyze_parameter_mapping(cmd_node, cmd_format)
        
        return cmd_node, param_mapping
    
    def _generate_example_command(self, cmd_format: str, parser_config: ParserConfig) -> List[str]:
        """为 cmd_format 生成示例命令"""
        parts = cmd_format.split()
        example_parts = []
        
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                # 参数占位符
                param_name = part[1:-1]
                example_values = self._generate_param_example_values(param_name, parser_config)
                example_parts.extend(example_values)
            else:
                example_parts.append(part)
        
        debug(f"生成的示例命令: {example_parts}")
        return example_parts
    
    def _generate_param_example_values(self, param_name: str, parser_config: ParserConfig) -> List[str]:
        """为参数生成示例值"""
        # 使用独特的占位符格式
        PLACEHOLDER_PREFIX = "__param_"
        PLACEHOLDER_SUFFIX = "__"
        
        # 查找参数配置
        arg_config = self._find_param_config(param_name, parser_config)
        if arg_config:
            # 根据 nargs 生成相应数量的示例值
            if arg_config.nargs.spec == '+' or arg_config.nargs.spec == '*':
                # 一个或多个参数，生成2个示例值
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}_1{PLACEHOLDER_SUFFIX}",
                    f"{PLACEHOLDER_PREFIX}{param_name}_2{PLACEHOLDER_SUFFIX}"
                ]
            elif arg_config.nargs.spec.isdigit():
                # 固定数量参数
                count = int(arg_config.nargs.spec)
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}_{i+1}{PLACEHOLDER_SUFFIX}" 
                    for i in range(count)
                ]
            else:
                # 默认生成1个示例值
                return [f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"]
        else:
            # 没有找到配置，默认生成1个示例值
            return [f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"]
    
    def _find_param_config(self, param_name: str, parser_config: ParserConfig) -> Optional[ArgumentConfig]:
        """根据参数名查找配置"""
        # 在全局参数中查找
        for arg_config in parser_config.arguments:
            if arg_config.name == param_name:
                return arg_config
        
        # 在子命令参数中查找
        for sub_cmd in parser_config.sub_commands:
            for arg_config in sub_cmd.arguments:
                if arg_config.name == param_name:
                    return arg_config
        
        return None
    
    def _load_parser_config(self, program_cmd: str) -> Optional[ParserConfig]:
        """加载解析器配置"""
        parser_config_file = self.parser_configs_dir / f"{program_cmd}.toml"
        
        if not parser_config_file.exists():
            warning(f"找不到程序 {program_cmd} 的解析器配置: {parser_config_file}")
            return None
        
        debug(f"加载解析器配置: {parser_config_file}")
        try:
            return load_parser_config_from_file(str(parser_config_file), program_cmd)
        except Exception as e:
            error(f"加载解析器配置失败: {e}")
            return None
    
    def _parse_command(self, parser_config: ParserConfig, command_parts: List[str]) -> Optional[CommandNode]:
        """解析命令得到 CommandNode"""
        try:
            if parser_config.parser_type == ParserType.ARGPARSE:
                parser = ArgparseParser(parser_config)
            elif parser_config.parser_type == ParserType.GETOPT:
                parser = GetoptParser(parser_config)
            else:
                error(f"不支持的解析器类型: {parser_config.parser_type}")
                return None
            
            # 使用完整的命令（包括程序名）
            return parser.parse(command_parts)
            
        except Exception as e:
            error(f"解析命令失败: {e}")
            return None
    
    def _mark_placeholder_args(self, cmd_node: CommandNode, cmd_format: str):
        """标记包含占位符值的参数"""
        # 从 cmd_format 中提取所有参数名
        import re
        param_names = re.findall(r'\{(\w+)\}', cmd_format)
        
        def mark_node(n: CommandNode):
            for arg in n.arguments:
                # 检查这个参数的值是否包含占位符模式
                for value in arg.values:
                    if any(f"__param_{name}" in value for name in param_names):
                        # 设置自定义标记（通过 option_name 或特殊字段）
                        # 由于不能修改 CommandArg 结构，我们通过其他方式标记
                        if arg.option_name:
                            arg.option_name = f"__placeholder__{arg.option_name}"
                        else:
                            arg.option_name = "__placeholder__"
                        break
            
            # 递归处理子命令
            if n.subcommand:
                mark_node(n.subcommand)
        
        mark_node(cmd_node)
    
    def _analyze_parameter_mapping(self, cmd_node: CommandNode, cmd_format: str) -> Dict[str, Any]:
        """分析参数映射"""
        param_mapping = {}
        
        # 从 cmd_format 中提取参数名
        import re
        param_names = re.findall(r'\{(\w+)\}', cmd_format)
        
        # 在 CommandNode 中查找这些参数
        for param_name in param_names:
            param_info = self._find_parameter_in_node(cmd_node, param_name)
            if param_info:
                param_mapping[param_name] = param_info
        
        return param_mapping
    
    def _find_parameter_in_node(self, node: CommandNode, param_name: str) -> Optional[Dict[str, Any]]:
        """在命令节点中查找参数"""
        # 在当前节点中查找
        for i, arg in enumerate(node.arguments):
            for j, value in enumerate(arg.values):
                if f"__param_{param_name}" in value:
                    return {
                        "cmd_arg": self._serialize_command_arg(arg),
                        "value_index": j,
                        "found_in": arg.node_type.value
                    }
        
        # 在子命令中查找
        if node.subcommand:
            return self._find_parameter_in_node(node.subcommand, param_name)
        
        return None
    
    def _serialize_command_arg(self, arg: CommandArg) -> Dict[str, Any]:
        """序列化 CommandArg 对象"""
        return arg.to_dict()
        
    def _serialize_command_node(self, node: CommandNode) -> Dict[str, Any]:
        """序列化 CommandNode 对象"""
        return node.to_dict()
    
    def write_to(self, path: str) -> None:
        """
        将映射数据写入文件
        
        Args:
            path: 输出文件路径
        """
        if not self.mapping_data:
            warning("没有映射数据可写入，请先调用 create_mappings()")
            return
        
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'wb') as f:
                tomli_w.dump(self.mapping_data, f)
            info(f"命令映射已写入: {output_path}")
        except Exception as e:
            error(f"写入文件失败: {e}")
            raise


# 便捷函数
def create_cmd_mappings(ops_dir: str, parser_configs_dir: str, output_path: str) -> None:
    """
    便捷函数：创建命令映射并写入文件
    
    Args:
        ops_dir: 操作接口文件夹路径
        parser_configs_dir: 解析器配置文件夹路径  
        output_path: 输出文件路径
    """
    creator = CmdMappingCreator(ops_dir, parser_configs_dir)
    creator.create_mappings()
    creator.write_to(output_path)