# cmdbridge/core/cmd_mapping.py

"""
命令映射核心模块 - 基于操作组的映射系统
"""

from typing import List, Dict, Any, Optional
from parsers.types import CommandNode, CommandArg, ArgType
from parsers.argparse_parser import ArgparseParser
from parsers.getopt_parser import GetoptParser
from parsers.types import ParserConfig, ParserType
from ..config.path_manager import PathManager

from log import debug, info, warning, error


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
    def load_from_cache(cls, domain_name: str, group_name: str) -> 'CmdMapping':
        """
        从缓存加载指定程序组的命令映射
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称
            
        Returns:
            CmdMapping: 命令映射器实例
        """
        path_manager = PathManager.get_instance()
        cache_file = path_manager.get_cmd_mappings_domain_dir_of_cache(domain_name) / f"{group_name}.toml"
        
        if not cache_file.exists():
            debug(f"缓存文件不存在: {cache_file}")
            return cls({})
        
        try:
            with open(cache_file, 'rb') as f:
                mapping_config = tomli.load(f)
            debug(f"从缓存加载 {domain_name}.{group_name} 的命令映射")
            return cls(mapping_config)
        except Exception as e:
            error(f"加载缓存文件失败 {cache_file}: {e}")
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
        cache_dir = path_manager.get_cmd_mappings_domain_dir_of_cache(domain_name)
        
        if not cache_dir.exists():
            return {}
        
        mappings = {}
        for cache_file in cache_dir.glob("*.toml"):
            group_name = cache_file.stem
            mappings[group_name] = cls.load_from_cache(domain_name, group_name)
        
        debug(f"加载 {domain_name} 领域的 {len(mappings)} 个程序组映射")
        return mappings

    def map_to_operation(self, source_cmdline: List[str], 
                        source_parser_config: ParserConfig,
                        dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """将源命令映射到目标操作组的操作和参数"""
        debug(f"开始映射命令到操作组 '{dst_operation_group}': {' '.join(source_cmdline)}")
        
        # 1. 解析源命令
        source_parser = self._create_source_parser(source_parser_config)
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
            # 如果在全局参数中没找到，尝试在子命令参数中查找
            # 注意：这里简化处理，实际可能需要更复杂的查找逻辑
            return option_name
        
        if arg_config.opt:
            # 优先返回长参数名
            for opt in arg_config.opt:
                if opt.startswith("--"):
                    return opt
            # 如果没有长参数名，返回第一个选项名
            return arg_config.opt[0]
        
        return option_name
    
    def _create_source_parser(self, source_parser_config: ParserConfig):
        """创建源程序的解析器"""
        if source_parser_config.parser_type == ParserType.ARGPARSE:
            return ArgparseParser(source_parser_config)
        elif source_parser_config.parser_type == ParserType.GETOPT:
            return GetoptParser(source_parser_config)
        else:
            raise ValueError(f"不支持的解析器类型: {source_parser_config.parser_type}")
    
    def _find_matching_mapping(self, source_node: CommandNode, dst_operation_group: str) -> Optional[Dict[str, Any]]:
        """
        查找匹配的命令映射
        
        Args:
            source_node: 解析后的源命令节点
            dst_operation_group: 目标程序名
            
        Returns:
            Optional[Dict[str, Any]]: 匹配的映射配置，如果没有匹配则返回 None
        """
        program_name = source_node.name
        debug(f"在程序 {program_name} 中查找匹配的映射，目标程序: {dst_operation_group}")
        
        # 检查程序名是否在映射配置中（移除程序名必须匹配的限制）
        if program_name not in self.mapping_config:
            debug(f"程序 {program_name} 不在映射配置中")
            return None
        
        command_mappings = self.mapping_config[program_name].get("command_mappings", [])
        debug(f"找到 {len(command_mappings)} 个可能的映射")
        
        for mapping in command_mappings:
            if self._is_command_match(source_node, mapping):
                debug(f"找到匹配的映射: {mapping['operation']}")
                return mapping
        
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
                return False
        
        return True

    def _compare_command_args(self, arg1: CommandArg, arg2: CommandArg) -> bool:
        """比较两个 CommandArg"""
        # 1. 比较类型
        if arg1.node_type != arg2.node_type:
            return False
        
        # 2. 比较 option_name（对于 Option 和 Flag 类型）
        if arg1.node_type in [ArgType.OPTION, ArgType.FLAG]:
            if arg1.option_name != arg2.option_name:
                return False
        
        # 3. 对于 Flag 类型，比较 repeat 次数
        if arg1.node_type == ArgType.FLAG:
            if arg1.repeat != arg2.repeat:
                return False
        
        # 4. 忽略 values 的比较（因为有 placeholder）
        # 5. 忽略 placeholder 字段本身的比较
        
        return True

    def _compare_command_args_ignore_values(self, arg1: CommandArg, arg2: CommandArg) -> bool:
        """比较两个 CommandArg，忽略参数值内容"""
        # 比较参数类型
        if arg1.node_type != arg2.node_type:
            return False
        
        # 比较选项名（忽略占位符标记）
        option1 = self._strip_placeholder_marker(arg1.option_name)
        option2 = self._strip_placeholder_marker(arg2.option_name)
        if option1 != option2:
            return False
        
        # 比较重复次数
        if arg1.repeat != arg2.repeat:
            return False
        
        # 比较值数量
        if len(arg1.values) != len(arg2.values):
            return False
        
        # 忽略参数值内容比较，因为映射配置的值是占位符
        return True
    
    def _strip_placeholder_marker(self, option_name: Optional[str]) -> Optional[str]:
        """去除占位符标记"""
        if option_name and option_name.startswith("__placeholder__"):
            return option_name[15:]  # 去除 "__placeholder__" 前缀
        return option_name
    
    def _has_extra_command_args(self, source_node: CommandNode, mapping_node: CommandNode) -> bool:
        """
        检查源命令是否有多余的 CommandArg
        
        Args:
            source_node: 源命令节点
            mapping_node: 映射配置的命令节点
            
        Returns:
            bool: 如果源命令有映射配置中没有的 CommandArg，返回 True
        """
        def count_command_args(node: CommandNode) -> int:
            """计算命令节点中的 CommandArg 总数"""
            count = len(node.arguments)
            current = node.subcommand
            while current:
                count += len(current.arguments)
                current = current.subcommand
            return count
        
        source_args_count = count_command_args(source_node)
        mapping_args_count = count_command_args(mapping_node)
        
        debug(f"CommandArg 数量检查: 源命令={source_args_count}, 映射配置={mapping_args_count}")
        
        # 如果源命令的 CommandArg 数量多于映射配置，说明有多余的 CommandArg
        return source_args_count > mapping_args_count
    
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

    def _find_parameter_values(self, source_node: CommandNode, param_info: Dict[str, Any]) -> List[str]:
        cmd_arg_info = param_info.get("cmd_arg", {})
        target_node_type = ArgType(cmd_arg_info["node_type"])
        target_option_name = cmd_arg_info.get("option_name")
        
        values = []
        
        def search_in_node(node: CommandNode):
            for arg in node.arguments:
                # 基于类型和选项名匹配
                if (arg.node_type == target_node_type and 
                    arg.option_name == target_option_name):
                    
                    # 对于位置参数，提取所有值
                    if target_node_type == ArgType.POSITIONAL:
                        values.extend(arg.values)
                    # 对于选项参数，提取所有值
                    elif target_node_type == ArgType.OPTION:
                        values.extend(arg.values)
                    # 对于标志参数，不需要值
            
            if node.subcommand:
                search_in_node(node.subcommand)
        
        search_in_node(source_node)

        if not values:
            debug(f"未找到参数值 (目标类型: {target_node_type.value}, 目标选项名: {target_option_name})")
        else:
            debug(f"成功找到参数值: {values}")
        
        return values

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