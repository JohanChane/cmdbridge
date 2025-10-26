# cmdbridge/config/cmd_mapping_creator.py

import os
import tomli
import tomli_w
from typing import Dict, List, Any, Optional
from pathlib import Path

from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType, ArgumentConfig
from parsers.argparse_parser import ArgparseParser
from parsers.getopt_parser import GetoptParser
from parsers.config_loader import load_parser_config_from_file

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class CmdMappingMgr:
    """命令映射创建器 - 为每个程序组生成单独的映射配置文件"""
    
    def __init__(self, domain_name: str, group_name: str):
        """
        初始化命令映射创建器
        
        Args:
            domain_name: 领域名称 (如 "package", "process")
            group_name: 程序组名称 (如 "apt", "pacman")
        """
        # 使用单例 PathManager
        self.path_manager = PathManager.get_instance()
        self.domain_name = domain_name
        self.group_name = group_name
        self.mapping_data = {}
    
    def create_mappings(self) -> Dict[str, Any]:
        """
        创建指定程序组的命令映射
        
        Returns:
            Dict[str, Any]: 映射数据，包含 operation 字段
        """
        debug(f"开始创建 {self.domain_name}.{self.group_name} 的命令映射")
        
        # 获取操作组配置文件路径
        group_file = self.path_manager.get_operation_group_path_of_config(self.domain_name, self.group_name)
        if not group_file.exists():
            error(f"操作组配置文件不存在: {group_file}")
            raise FileNotFoundError(f"操作组配置文件不存在: {group_file}")
        
        # 检查程序解析器配置是否存在
        if not self.path_manager.program_parser_config_exists(self.group_name):
            warning(f"跳过 {self.group_name}: 缺少解析器配置")
            return {}
        
        # 处理单个操作组文件
        self._process_group_file(group_file)
        
        debug(f"{self.domain_name}.{self.group_name} 命令映射创建完成")
        return self.mapping_data
        
    def _process_group_file(self, operation_group_file: Path):
        """处理单个操作组文件"""
        
        # 加载操作文件内容
        try:
            with open(operation_group_file, 'rb') as f:
                group_data = tomli.load(f)
        except (tomli.TOMLDecodeError, Exception) as e:
            warning(f"无法解析操作文件 {operation_group_file}: {e}")
            return
    
        debug(f"处理程序组: {self.group_name}")
        
        # 初始化映射数据
        self.mapping_data[self.group_name] = {"command_mappings": []}
        
        # 处理所有操作
        if "operations" in group_data:
            for operation_key, operation_config in group_data["operations"].items():
                debug(f"处理操作键: {operation_key}")
                self._process_operation(operation_key, operation_config)
        else:
            debug(f"文件 {operation_group_file} 中没有 operations 部分")
    
    def _process_operation(self, operation_key: str, operation_config: Dict[str, Any]):
        """处理单个操作"""
        if "cmd_format" not in operation_config:
            warning(f"操作 {operation_key} 缺少 cmd_format，跳过")
            return
        
        cmd_format = operation_config["cmd_format"]
        final_cmd_format = operation_config.get("final_cmd_format")  # 新增
        
        # 预处理：移除参数周围的引号，但记录原始格式
        import re
        original_cmd_format = cmd_format
        
        # 移除参数周围的单引号或双引号
        cmd_format = re.sub(r"""['"]\{(\w+)\}['"]""", r'{\1}', cmd_format)
        
        debug(f"命令格式预处理: '{original_cmd_format}' -> '{cmd_format}'")

        debug(f"分析命令格式: {cmd_format}, final_cmd_format: {final_cmd_format}")
        
        # 从 operation_key 提取 operation_name
        operation_parts = operation_key.split('.')
        if len(operation_parts) > 1 and operation_parts[-1] == self.group_name:
            operation_name = '.'.join(operation_parts[:-1])
        else:
            operation_name = operation_key
        
        debug(f"提取操作名: {operation_name} (原始键: {operation_key}, 程序组: {self.group_name})")
        
        # 生成示例命令并解析得到 CommandNode
        cmd_node, param_mapping = self._parse_command_and_map_params(cmd_format, self.group_name)
        if not cmd_node:
            error(f"无法解析命令: {cmd_format}")
            return
        
        # 创建映射条目，包含 operation 和 final_cmd_format 字段
        mapping_entry = {
            "operation": operation_name,
            "cmd_format": cmd_format,
            "params": param_mapping,
            "cmd_node": self._serialize_command_node(cmd_node)
        }
        
        # 添加 final_cmd_format（如果存在）
        if final_cmd_format:
            mapping_entry["final_cmd_format"] = final_cmd_format
            debug(f"添加 final_cmd_format: {final_cmd_format}")
        
        self.mapping_data[self.group_name]["command_mappings"].append(mapping_entry)
        debug(f"为 {self.group_name} 创建映射: {operation_name}, {len(param_mapping)} 个参数")
    
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
        # 使用 PathManager 获取解析器配置文件路径
        parser_config_file = self.path_manager.get_program_parser_config_path(program_cmd)
        
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
        """标记占位符参数（简化版本，实际不再需要）"""
        # 由于新的参数提取逻辑不依赖占位符标记，
        # 这个方法可以保持空实现或简单标记所有参数
        debug("使用新的参数提取逻辑，跳过占位符标记")
        
        # 可选：为了向后兼容，简单标记所有位置参数
        # def mark_all_positionals(node: CommandNode):
        #     for arg in node.arguments:
        #         if arg.node_type == ArgType.POSITIONAL:
        #             arg.is_placeholder = True
        #     if node.subcommand:
        #         mark_all_positionals(node.subcommand)
        
        # mark_all_positionals(cmd_node)
    
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
        """在命令节点中查找参数（简化版本）"""
        # 查找第一个位置参数
        def find_first_positional(current_node: CommandNode) -> Optional[CommandArg]:
            for arg in current_node.arguments:
                if arg.node_type == ArgType.POSITIONAL:
                    return arg
            if current_node.subcommand:
                return find_first_positional(current_node.subcommand)
            return None
        
        positional_arg = find_first_positional(node)
        if positional_arg:
            return {
                "cmd_arg": self._serialize_command_arg(positional_arg),
                "found_in": "positional"
            }
        
        return None
    
    def _serialize_command_arg(self, arg: CommandArg) -> Dict[str, Any]:
        """序列化 CommandArg 对象"""
        return arg.to_dict()
        
    def _serialize_command_node(self, node: CommandNode) -> Dict[str, Any]:
        """序列化 CommandNode 对象"""
        return node.to_dict()
    
    def write_to(self) -> None:
        """
        将映射数据写入缓存文件
        """
        if not self.mapping_data:
            warning("没有映射数据可写入，请先调用 create_mappings()")
            return
        
        # 使用 PathManager 获取缓存文件路径 - 统一目录结构
        output_path = self.path_manager.get_cmd_mappings_group_path_of_cache(self.domain_name, self.group_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'wb') as f:
                tomli_w.dump(self.mapping_data, f)
            debug(f"命令映射已写入: {output_path}")
        except Exception as e:
            error(f"写入文件失败: {e}")
            raise


# 便捷函数
def create_cmd_mappings_for_group(domain_name: str, group_name: str) -> Dict[str, Any]:
    """
    便捷函数：为指定领域的程序组创建命令映射
    
    Args:
        domain_name: 领域名称
        group_name: 程序组名称
        
    Returns:
        Dict[str, Any]: 映射数据
    """
    creator = CmdMappingMgr(domain_name, group_name)
    mapping_data = creator.create_mappings()
    creator.write_to()
    return mapping_data

def create_cmd_mappings_for_domain(domain_name: str) -> Dict[str, Dict[str, Any]]:
    """
    便捷函数：为指定领域的所有程序组创建命令映射
    
    Args:
        domain_name: 领域名称
        
    Returns:
        Dict[str, Dict[str, Any]]: 所有程序组的映射数据
    """
    path_manager = PathManager.get_instance()
    groups = path_manager.get_operation_groups_from_config(domain_name)
    
    all_mappings = {}
    for group_name in groups:
        try:
            mapping_data = create_cmd_mappings_for_group(domain_name, group_name)
            all_mappings[group_name] = mapping_data
            info(f"✅ 已为 {domain_name}.{group_name} 创建命令映射")
        except Exception as e:
            error(f"❌ 为 {domain_name}.{group_name} 创建命令映射失败: {e}")
    
    return all_mappings

def create_cmd_mappings_for_all_domains() -> None:
    """
    便捷函数：为所有领域的所有程序组创建命令映射
    """
    path_manager = PathManager.get_instance()
    domains = path_manager.get_domains_from_config()
    
    for domain in domains:
        create_cmd_mappings_for_domain(domain)