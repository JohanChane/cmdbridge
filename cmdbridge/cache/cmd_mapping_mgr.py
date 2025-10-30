import os
import tomli
import tomli_w
from typing import Dict, List, Any, Optional
from pathlib import Path

from parsers.types import CommandNode, CommandArg, ArgType, ParserConfig, ParserType, ArgumentConfig
from parsers.config_loader import load_parser_config_from_file
from parsers.factory import ParserFactory

from log import debug, info, warning, error
from ..config.path_manager import PathManager


class CmdMappingMgr:
    """命令映射创建器 - 为每个程序生成单独的命令映射文件"""
    
    def __init__(self, domain_name: str, group_name: str):
        """
        初始化命令映射创建器
        
        Args:
            domain_name: 领域名称 (如 "package", "process")
            group_name: 操作组名称 (如 "apt", "pacman")
        """
        # 使用单例 PathManager
        self.path_manager = PathManager.get_instance()
        self.domain_name = domain_name
        self.group_name = group_name
        self.program_mappings = {}  # 按程序组织的映射数据
        self.cmd_to_operation_data = {}  # cmd_to_operation 数据
    
    def create_mappings(self) -> Dict[str, Any]:
        debug(f"=== 开始处理操作组: {self.domain_name}.{self.group_name} ===")
        
        # 获取操作组配置文件路径
        group_file = self.path_manager.get_operation_group_path_of_config(self.domain_name, self.group_name)
        debug(f"操作组配置文件: {group_file}")
        debug(f"配置文件存在: {group_file.exists()}")
        
        if not group_file.exists():
            error(f"操作组配置文件不存在: {group_file}")
            raise FileNotFoundError(f"操作组配置文件不存在: {group_file}")
        
        # 处理单个操作组文件
        self._process_group_file(group_file)
        
        debug(f"处理完成后的程序映射: {self.program_mappings}")
        
        # 生成 cmd_to_operation 数据
        self._generate_cmd_to_operation_data()
        
        debug(f"生成的 cmd_to_operation 数据: {self.cmd_to_operation_data}")
        debug(f"=== 完成处理操作组: {self.domain_name}.{self.group_name} ===\n")
        
        return {
            "program_mappings": self.program_mappings,
            "cmd_to_operation": self.cmd_to_operation_data
        }
    
    def _process_group_file(self, operation_group_file: Path):
        """处理单个操作组文件"""
        
        # 加载操作文件内容
        try:
            with open(operation_group_file, 'rb') as f:
                group_data = tomli.load(f)
        except (tomli.TOMLDecodeError, Exception) as e:
            warning(f"无法解析操作文件 {operation_group_file}: {e}")
            return
    
        debug(f"处理操作组: {self.group_name}")
        
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
        final_cmd_format = operation_config.get("final_cmd_format")
        
        # 预处理：移除参数周围的引号
        import re
        original_cmd_format = cmd_format
        cmd_format = re.sub(r"""['"]\{(\w+)\}['"]""", r'{\1}', cmd_format)
        
        debug(f"命令格式预处理: '{original_cmd_format}' -> '{cmd_format}'")
        
        # 从 operation_key 提取 operation_name
        operation_parts = operation_key.split('.')
        if len(operation_parts) > 1 and operation_parts[-1] == self.group_name:
            operation_name = '.'.join(operation_parts[:-1])
        else:
            operation_name = operation_key
        
        debug(f"提取操作名: {operation_name}")
        
        # 从命令格式中提取实际的程序名
        actual_program_name = self._extract_program_from_cmd_format(cmd_format)
        if not actual_program_name:
            actual_program_name = self.group_name  # 回退到操作组名
        
        debug(f"操作 {operation_name} 使用程序: {actual_program_name}")
        
        # 生成示例命令并解析得到 CommandNode
        cmd_node = self._parse_command_and_map_params(cmd_format, actual_program_name)
        if not cmd_node:
            error(f"无法解析命令: {cmd_format}")
            return
        
        # 创建映射条目
        mapping_entry = {
            "operation": operation_name,
            "cmd_format": cmd_format,
            "cmd_node": self._serialize_command_node(cmd_node)
        }
        
        # 添加 final_cmd_format（如果存在）
        if final_cmd_format:
            mapping_entry["final_cmd_format"] = final_cmd_format
        
        # 按程序名组织映射数据
        if actual_program_name not in self.program_mappings:
            self.program_mappings[actual_program_name] = {"command_mappings": []}
        
        self.program_mappings[actual_program_name]["command_mappings"].append(mapping_entry)
        debug(f"为程序 {actual_program_name} 创建映射: {operation_name}")

    def _extract_program_from_cmd_format(self, cmd_format: str) -> Optional[str]:
        """从命令格式中提取程序名"""
        parts = cmd_format.strip().split()
        if parts:
            program_name = parts[0]
            debug(f"从命令格式 '{cmd_format}' 中提取程序名: {program_name}")
            return program_name
        return None

    def _generate_cmd_to_operation_data(self):
        """生成 cmd_to_operation 数据"""
        # 收集该操作组使用的所有程序
        programs = list(self.program_mappings.keys())
        if programs:
            self.cmd_to_operation_data[self.group_name] = {
                "programs": programs
            }
            debug(f"操作组 {self.group_name} 使用程序: {programs}")

    def _parse_command_and_map_params(self, cmd_format: str, program_cmd: str) -> Optional[CommandNode]:
        """解析命令并设置 placeholder"""
        debug(f"解析命令: '{cmd_format}', 程序: {program_cmd}")
        
        # 加载解析器配置
        parser_config = self._load_parser_config(program_cmd)
        if not parser_config:
            error(f"无法加载程序 '{program_cmd}' 的解析器配置")
            return None
        
        # 生成示例命令
        example_command = self._generate_example_command(cmd_format, parser_config)
        
        # 解析命令得到 CommandNode
        cmd_node = self._parse_command(parser_config, example_command)
        if not cmd_node:
            return None
        
        # 设置 placeholder 标记
        self._set_placeholder_markers(cmd_node, cmd_format)
        
        return cmd_node
    
    def _set_placeholder_markers(self, cmd_node: CommandNode, cmd_format: str):
        """在 CommandNode 中设置 placeholder 标记"""
        import re
        
        # 从 cmd_format 中提取所有参数名
        param_names = re.findall(r'\{(\w+)\}', cmd_format)
        if not param_names:
            return
        
        # 🔧 修复：创建参数名到 placeholder 的映射
        param_mapping = {}
        for param_name in param_names:
            # 对于每个参数名，创建对应的占位符模式
            placeholder_pattern = re.compile(rf'__param_{param_name}(?:_\d+)?__')
            param_mapping[param_name] = placeholder_pattern
        
        # 递归遍历 CommandNode 设置 placeholder
        def set_placeholders(node: CommandNode):
            for arg in node.arguments:
                # 检查参数值是否包含占位符
                for value in arg.values:
                    # 🔧 修复：使用参数映射来匹配占位符
                    for param_name, pattern in param_mapping.items():
                        if pattern.match(value):
                            arg.placeholder = param_name  # 使用命令格式中的参数名
                            debug(f"设置参数 {param_name} 的 placeholder")
                            break  # 一个 CommandArg 只需要设置一次
                    else:
                        continue
                    break
                
            if node.subcommand:
                set_placeholders(node.subcommand)
        
        set_placeholders(cmd_node)

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
        """为参数生成示例值（带placeholder标记）"""
        # 使用独特的占位符格式
        PLACEHOLDER_PREFIX = "__param_"
        PLACEHOLDER_SUFFIX = "__"
        
        # 查找参数配置
        arg_config = self._find_param_config(param_name, parser_config)
        if arg_config:
            # 根据 nargs 生成相应数量的示例值
            if arg_config.nargs.spec == '+' or arg_config.nargs.spec == '*':
                # 🔧 修复：对于多值参数，使用相同的参数名（不带数字后缀）
                # 这样参数名就能与命令格式中的占位符保持一致
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}",
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}"  # 相同的参数名
                ]
            elif arg_config.nargs.spec.isdigit():
                # 固定数量参数
                count = int(arg_config.nargs.spec)
                return [
                    f"{PLACEHOLDER_PREFIX}{param_name}{PLACEHOLDER_SUFFIX}" 
                    for _ in range(count)  # 相同的参数名
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

            parser = ParserFactory.create_parser(parser_config)
            
            # 使用完整的命令（包括程序名）
            return parser.parse(command_parts)
            
        except Exception as e:
            error(f"解析命令失败: {e}")
            return None
    
    def _serialize_command_node(self, node: CommandNode) -> Dict[str, Any]:
        """序列化 CommandNode 对象"""
        return node.to_dict()

    def write_to(self) -> None:
        """
        将映射数据写入缓存文件
        """
        # 检查是否有程序映射数据
        if not self.program_mappings:
            warning(f"⚠️ {self.domain_name}.{self.group_name} 没有程序映射数据可写入")
            return
        
        # 确保操作组目录存在
        self.path_manager.ensure_cmd_mappings_group_dir(self.domain_name, self.group_name)
        
        # 为每个程序生成单独的命令文件
        for program_name, program_data in self.program_mappings.items():
            program_file = self.path_manager.get_cmd_mappings_group_program_path_of_cache(
                self.domain_name, self.group_name, program_name
            )
            try:
                with open(program_file, 'wb') as f:
                    tomli_w.dump(program_data, f)
                info(f"✅ 已生成 {self.group_name}/{program_name}_command.toml 文件")
            except Exception as e:
                error(f"❌ 写入程序命令文件失败 {program_file}: {e}")
                raise
        
        # 生成 cmd_to_operation.toml 文件（读取→合并→写入）
        if self.cmd_to_operation_data:
            cmd_to_operation_file = self.path_manager.get_cmd_to_operation_path(self.domain_name)
            cmd_to_operation_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # 读取现有的 cmd_to_operation 数据（如果存在）
                existing_data = {}
                if cmd_to_operation_file.exists():
                    with open(cmd_to_operation_file, 'rb') as f:
                        existing_data = tomli.load(f)
                
                # 合并数据：保留现有的，添加或更新当前操作组的数据
                merged_data = existing_data.copy()
                merged_data.setdefault("cmd_to_operation", {})
                merged_data["cmd_to_operation"].update(self.cmd_to_operation_data)
                
                # 写入合并后的数据
                with open(cmd_to_operation_file, 'wb') as f:
                    tomli_w.dump(merged_data, f)
                info(f"✅ 已更新 cmd_to_operation.toml 文件，包含操作组: {list(self.cmd_to_operation_data.keys())}")
                
            except Exception as e:
                error(f"❌ 写入 cmd_to_operation 文件失败 {cmd_to_operation_file}: {e}")
                raise

# 便捷函数
def create_cmd_mappings_for_group(domain_name: str, group_name: str) -> Dict[str, Any]:
    """
    便捷函数：为指定领域的操作组创建命令映射
    
    Args:
        domain_name: 领域名称
        group_name: 操作组名称
        
    Returns:
        Dict[str, Any]: 映射数据
    """
    creator = CmdMappingMgr(domain_name, group_name)
    mapping_data = creator.create_mappings()
    creator.write_to()
    return mapping_data

def create_cmd_mappings_for_domain(domain_name: str) -> Dict[str, Dict[str, Any]]:
    """
    便捷函数：为指定领域的所有操作组创建命令映射
    
    Args:
        domain_name: 领域名称
        
    Returns:
        Dict[str, Dict[str, Any]]: 所有操作组的映射数据
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
    便捷函数：为所有领域的所有操作组创建命令映射
    """
    path_manager = PathManager.get_instance()
    domains = path_manager.get_domains_from_config()
    
    for domain in domains:
        create_cmd_mappings_for_domain(domain)