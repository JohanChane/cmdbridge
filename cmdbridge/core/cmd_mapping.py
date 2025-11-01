"""
命令映射核心模块 - 基于操作组的映射系统
"""

from typing import List, Dict, Any, Optional
from parsers.types import CommandNode, CommandArg, ArgType
from parsers.types import ParserConfig
from parsers.factory import ParserFactory
from ..config.path_manager import PathManager

from log import debug, info, warning, error
import tomli

class CmdMapping:
    """
    命令映射器 - 将源命令映射到操作和参数
    
    输入: 
      - source cmdline (字符串列表, 如 ["apt", "install", "vim"])
      - cmd_mapping 配置数据 (包含 operation 字段)
      - dst_operation_group (程序名, 如 "apt")
    
    输出: 
      - {operation_name, params{pkgs:, path: }}
    """
    
    def __init__(self, mapping_config: Dict[str, Any]):
        """
        初始化命令映射器
        
        Args:
            mapping_config: 单个程序组的映射配置
        """
        self.mapping_config = mapping_config
        self.source_parser_config = None

    @classmethod
    def load_from_cache(cls, domain_name: str, program_name: str) -> 'CmdMapping':
        """
        从缓存加载指定程序的命令映射（跨操作组查找）
        
        Args:
            domain_name: 领域名称
            program_name: 程序名称
            
        Returns:
            CmdMapping: 命令映射器实例
        """
        path_manager = PathManager.get_instance()
        
        # 从 cmd_to_operation.toml 获取程序列表
        cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain_name)
        
        if not cmd_to_operation_file.exists():
            debug(f"cmd_to_operation 文件不存在: {cmd_to_operation_file}")
            return cls({})
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            debug(f"跨操作组查找程序: {program_name}")
            found_group = None
            
            # 在所有操作组中查找包含该程序的操作组
            for op_group, group_data in cmd_to_operation_data.get("cmd_to_operation", {}).items():
                if program_name in group_data.get("programs", []):
                    found_group = op_group
                    debug(f"在操作组 {op_group} 中找到程序 {program_name}")
                    break
            
            if not found_group:
                debug(f"在所有操作组中未找到程序 {program_name}")
                return cls({})
            
            # 加载该程序的命令映射
            program_file = path_manager.get_cmd_mappings_group_program_path_of_cache(
                domain_name, found_group, program_name
            )
            
            if not program_file.exists():
                debug(f"程序映射文件不存在: {program_file}")
                return cls({})
            
            with open(program_file, 'rb') as f:
                program_data = tomli.load(f)
            
            debug(f"加载程序 {program_name} 的命令映射（来自操作组 {found_group}）")
            debug(f"程序数据: {program_data}")
            
            # 确保返回正确的数据结构
            # 程序文件的结构是 {"command_mappings": [...]}
            # 但 CmdMapping 期望的是 {program_name: {"command_mappings": [...]}}
            mapping_config = {
                program_name: program_data
            }
            
            return cls(mapping_config)
            
        except Exception as e:
            error(f"加载缓存文件失败: {e}")
            return cls({})
        
    @classmethod
    def load_all_for_domain(cls, domain_name: str) -> Dict[str, 'CmdMapping']:
        """
        加载指定领域的所有程序组命令映射
        
        Args:
            domain_name: 领域名称
            
        Returns:
            Dict[str, CmdMapping]: 程序组名到命令映射器的字典
        """
        path_manager = PathManager.get_instance()
        cmd_to_operation_file = path_manager.get_cmd_to_operation_path(domain_name)
        
        if not cmd_to_operation_file.exists():
            return {}
        
        try:
            with open(cmd_to_operation_file, 'rb') as f:
                cmd_to_operation_data = tomli.load(f)
            
            mappings = {}
            cmd_to_operation = cmd_to_operation_data.get("cmd_to_operation", {})
            
            for group_name in cmd_to_operation.keys():
                mappings[group_name] = cls.load_from_cache(domain_name, group_name)
            
            debug(f"加载 {domain_name} 领域的 {len(mappings)} 个程序组映射")
            return mappings
            
        except Exception as e:
            error(f"加载领域映射失败: {e}")
            return {}

    def map_to_operation(self, source_cmdline: List[str], 
                        source_parser_config: ParserConfig,
                        dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """将源命令映射到目标操作组的操作和参数"""
        debug(f"开始映射命令到操作组 '{dst_operation_group}': {' '.join(source_cmdline)}")
        
        # 1. 解析源命令
        source_parser = ParserFactory.create_parser(source_parser_config)
        source_node = source_parser.parse(source_cmdline)
        
        if not source_parser.validate(source_node):
            warning(f"源命令验证失败: {' '.join(source_cmdline)}")
            return None

        # 2. 在映射配置中查找匹配的操作
        matched_mapping = self._find_matching_mapping(source_node, dst_operation_group)
        if not matched_mapping:
            debug(f"在操作组 '{dst_operation_group}' 中未找到匹配的命令映射")
            return None
        
        # 3. 反序列化映射节点
        mapping_node = self._deserialize_command_node(matched_mapping["cmd_node"])
        
        # 4. 提取参数值
        param_values = self._extract_parameter_values(source_node, mapping_node)
        
        # 5. 返回操作和参数
        result = {
            "operation_name": matched_mapping["operation"],
            "params": param_values
        }
        
        debug(f"命令映射成功: {' '.join(source_cmdline)} -> {result}")
        return result

    def _normalize_option_name(self, option_name: Optional[str]) -> str:
        """规范化选项名，对于长短参数优先返回长参数名"""
        if not option_name:
            return ""
        
        if not self.source_parser_config:
            return option_name
        
        # 在解析器配置中查找对应的参数配置
        arg_config = self.source_parser_config.find_argument(option_name)
        if not arg_config:
            return option_name
        
        primary_name = arg_config.get_primary_option_name()
        return primary_name or option_name
    
    def _find_matching_mapping(self, source_node: CommandNode, dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """
        查找匹配的命令映射
        
        Args:
            source_node: 解析后的源命令节点
            dst_operation_group: 目标操作组名称
            
        Returns:
            Optional[Dict[str, Any]]: 匹配的映射配置，如果没有匹配则返回 None
        """
        program_name = source_node.name  # 源程序名，如 "asp"
        debug(f"在程序 {program_name} 中查找匹配的映射，目标操作组: {dst_operation_group}")
        
        # 直接根据源程序名查找对应的映射配置
        if program_name not in self.mapping_config:
            debug(f"程序 {program_name} 不在映射配置中")
            return None
        
        program_data = self.mapping_config[program_name]
        command_mappings = program_data.get("command_mappings", [])
        debug(f"找到 {len(command_mappings)} 个可能的映射")
        
        for mapping in command_mappings:
            if self._is_command_match(source_node, mapping):
                debug(f"找到匹配的映射: {mapping['operation']}")
                return mapping
        
        debug(f"在操作组 {dst_operation_group} 中未找到程序 {program_name} 的匹配映射")
        return None
    
    def _is_command_match(self, source_node: CommandNode, mapping: Dict[str, Any]) -> bool:
        """
        检查源命令是否与映射配置匹配
        
        匹配规则:
        1. 程序名相同（已在外部检查）
        2. 命令节点结构相同（名称、参数数量、子命令结构）
        3. 参数结构相同（类型、选项名、重复次数）
        4. 忽略参数值内容
        """
        # 1. 程序名匹配（已经在 _find_matching_mapping 中检查过）
        
        # 2. 反序列化映射配置中的 CommandNode
        mapping_node = self._deserialize_command_node(mapping["cmd_node"])
        
        # 3. 深度比较命令节点结构
        return self._compare_command_nodes_deep(source_node, mapping_node)
    
    def _compare_command_nodes_deep(self, node1: CommandNode, node2: CommandNode) -> bool:
        """深度比较两个命令节点结构"""
        # 比较节点名称
        if node1.name != node2.name:
            return False
        
        # 比较子命令结构
        if (node1.subcommand is None) != (node2.subcommand is None):
            return False
        
        if node1.subcommand and node2.subcommand:
            # 递归比较子命令
            if not self._compare_command_nodes_deep(node1.subcommand, node2.subcommand):
                return False
        
        # 比较参数数量
        if len(node1.arguments) != len(node2.arguments):
            return False
        
        # 逐个比较参数
        for arg1, arg2 in zip(node1.arguments, node2.arguments):
            if not self._compare_command_args(arg1, arg2):
                debug(f"arg1 和 arg2 不相同。arg1: {arg1}, arg2: {arg2}")
                return False
        
        return True

    def _compare_command_args(self, arg1: CommandArg, arg2: CommandArg) -> bool:
        """比较两个 CommandArg"""
        # 1. 比较类型
        if arg1.node_type != arg2.node_type:
            return False
        
        # 2. 对于 Flag 类型，比较 repeat 次数
        if arg1.node_type == ArgType.FLAG:
            if arg1.option_name != arg2.option_name:        # option_name 必须要用统一名称。ArgumentConfig.get_primary_option_name()
                return False
            if arg1.repeat != arg2.repeat:
                return False
            
        # 3. 比较 option_name（对于 Option 和 Flag 类型）。
        if arg1.node_type == ArgType.OPTION:
            if arg1.option_name != arg2.option_name:        # option_name 必须要用统一名称。ArgumentConfig.get_primary_option_name()
                return False
            if not arg1.placeholder and not arg2.placeholder:   # 其中一个有 placeholder 字段则忽略比较
                if set(arg1.values) != set(arg2.values):
                    return False
        # 4. 比较 positional value
        if arg1.node_type == ArgType.POSITIONAL:
            if not arg1.placeholder and not arg2.placeholder:   # 其中一个有 placeholder 字段则忽略比较
                if set(arg1.values) != set(arg2.values):
                    return False
        
        return True
    
    def _extract_parameter_values(self, source_node: CommandNode, mapping_node: CommandNode) -> Dict[str, str]:
        """从源命令节点中提取参数值"""
        param_values = {}
        
        # 递归遍历节点提取参数
        def extract_from_node(source_node: CommandNode, mapping_node: CommandNode):
            # 逐个参数比较和提取
            for source_arg, mapping_arg in zip(source_node.arguments, mapping_node.arguments):
                if mapping_arg.placeholder:
                    # 提取参数值
                    param_name = mapping_arg.placeholder
                    if source_arg.values:
                        param_values[param_name] = " ".join(source_arg.values)
                        debug(f"提取参数 {param_name} = '{param_values[param_name]}'")
            
            # 递归处理子命令
            if source_node.subcommand and mapping_node.subcommand:
                extract_from_node(source_node.subcommand, mapping_node.subcommand)
        
        extract_from_node(source_node, mapping_node)
        debug(f"参数提取完成: {param_values}")
        return param_values

    def _deserialize_command_node(self, serialized_node: Dict[str, Any]) -> CommandNode:
        """反序列化 CommandNode"""
        return CommandNode.from_dict(serialized_node)


# 便捷函数
def create_cmd_mapping(mapping_config: Dict[str, Any]) -> CmdMapping:
    """
    创建命令映射器实例
    
    Args:
        mapping_config: 映射配置数据
        
    Returns:
        CmdMapping: 命令映射器实例
    """
    return CmdMapping(mapping_config)