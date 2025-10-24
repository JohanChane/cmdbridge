# cmdbridge/click_ext/completor.py

"""Click 扩展模块，提供动态补全支持"""

import click
from typing import List, Optional, Any, Callable
from pathlib import Path
import tomli

# 正确的导入方式
try:
    from click.shell_completion import CompletionItem
except ImportError:
    # 如果导入失败，创建一个兼容类
    class CompletionItem:
        def __init__(self, value):
            self.value = value

from ..config.path_manager import PathManager


class ContextAwareChoice(click.Choice):
    """上下文感知的动态选项类型"""
    
    def __init__(self, get_choices_callback: Callable[[Optional[str]], List[str]]):
        self.get_choices_callback = get_choices_callback
        super().__init__([])
    
    def get_choices(self, ctx: click.Context) -> List[str]:
        """根据上下文动态获取选项列表"""
        try:
            # 从上下文中获取 domain 参数
            domain = None
            if ctx and ctx.params:
                domain = ctx.params.get('domain')
            
            return self.get_choices_callback(domain)
        except Exception:
            return []
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        # 在转换时更新选项列表
        if ctx:
            self.choices = self.get_choices(ctx)
        return super().convert(value, param, ctx)
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        # 在补全时更新选项列表
        self.choices = self.get_choices(ctx)
        return super().shell_complete(ctx, param, incomplete)


class DynamicCompleter:
    """动态命令补全工具类"""
    
    @staticmethod
    def _generate_example_command(cmd_format: str, program_name: str) -> str:
        """将命令格式转换为示例命令（简化版，不替换参数）"""
        if not cmd_format:
            return ""
        
        # 直接返回原始的命令格式，保留参数占位符
        # 这样用户可以清楚地看到需要提供哪些参数
        return cmd_format
    
    @staticmethod
    def get_command_completions(ctx: click.Context, param: click.Parameter, incomplete: str) -> List[str]:
        """获取命令补全，返回原始命令格式"""
        try:
            path_manager = PathManager.get_instance()
            
            # 获取上下文参数
            domain = ctx.params.get('domain')
            dest_group = ctx.params.get('dest_group')
            source_group = ctx.params.get('source_group')
            
            # 如果没有指定源程序组，尝试从命令中提取
            if not source_group and incomplete:
                first_word = incomplete.strip().split()[0] if incomplete else ""
                if first_word and path_manager.program_parser_config_exists(first_word):
                    source_group = first_word
            
            # 确定要补全的程序组列表
            if source_group:
                source_group_candidates = [source_group]
            elif domain:
                source_group_candidates = path_manager.list_operation_groups(domain)
            else:
                source_group_candidates = path_manager.list_all_operation_groups()
            
            # 收集所有可能的命令补全
            completions = []
            for src_group in source_group_candidates:
                # 获取原始命令格式（不生成示例）
                group_commands = DynamicCompleter._get_commands_for_group(domain, src_group)
                completions.extend(group_commands)
            
            # 过滤匹配 incomplete 的补全
            return [cmd for cmd in completions if cmd.startswith(incomplete)]
            
        except Exception:
            return []

    @staticmethod
    def _get_example_commands_for_group(domain: Optional[str], group_name: str, incomplete: str) -> List[str]:
        """获取程序组的命令格式（原始格式）"""
        command_formats = []
        
        try:
            # 从操作组配置获取操作定义
            if domain:
                group_config_file = PathManager.get_instance().get_operation_group_config_path(domain, group_name)
            else:
                # 如果没有指定领域，尝试在所有领域中查找
                domains = PathManager.get_instance().list_domains()
                for dom in domains:
                    group_config_file = PathManager.get_instance().get_operation_group_config_path(dom, group_name)
                    if group_config_file and group_config_file.exists():
                        domain = dom
                        break
            
            if group_config_file and group_config_file.exists():
                with open(group_config_file, 'rb') as f:
                    config_data = tomli.load(f)
                
                if "operations" in config_data:
                    for operation_key, operation_config in config_data["operations"].items():
                        cmd_format = operation_config.get("cmd_format", "")
                        if cmd_format:
                            # 直接使用原始的 cmd_format，包含参数占位符
                            command_formats.append(cmd_format)
                
                # 如果没有找到配置，尝试从缓存加载
                if not command_formats and domain:
                    cache_file = PathManager.get_instance().get_cmd_mappings_cache_path(domain, group_name)
                    if cache_file and cache_file.exists():
                        with open(cache_file, 'rb') as f:
                            mapping_data = tomli.load(f)
                        
                        if group_name in mapping_data:
                            for mapping in mapping_data[group_name].get("command_mappings", []):
                                cmd_format = mapping.get("cmd_format", "")
                                if cmd_format:
                                    command_formats.append(cmd_format)
            
        except Exception:
            pass
        
        return command_formats

    @staticmethod
    def _get_commands_for_group(domain: Optional[str], group_name: str) -> List[str]:
        """获取指定程序组的命令列表（原始格式）"""
        commands = []
        try:
            # 从命令映射缓存中获取命令格式
            cache_file = None
            if domain:
                cache_file = PathManager.get_instance().get_cmd_mappings_cache_path(domain, group_name)
            else:
                # 如果没有指定领域，尝试在所有领域中查找
                domains = PathManager.get_instance().list_domains()
                for dom in domains:
                    cache_file = PathManager.get_instance().get_cmd_mappings_cache_path(dom, group_name)
                    if cache_file and cache_file.exists():
                        break
            
            if cache_file and cache_file.exists():
                with open(cache_file, 'rb') as f:
                    mapping_data = tomli.load(f)
                
                if group_name in mapping_data:
                    for mapping in mapping_data[group_name].get("command_mappings", []):
                        cmd_format = mapping.get("cmd_format", "")
                        if cmd_format:
                            commands.append(cmd_format)
            
            # 如果没有找到缓存，从操作组配置中获取
            if not commands and domain:
                group_config_file = PathManager.get_instance().get_operation_group_config_path(domain, group_name)
                if group_config_file.exists():
                    with open(group_config_file, 'rb') as f:
                        config_data = tomli.load(f)
                    
                    if "operations" in config_data:
                        for operation_config in config_data["operations"].values():
                            cmd_format = operation_config.get("cmd_format", "")
                            if cmd_format:
                                commands.append(cmd_format)
        
        except Exception:
            pass
        
        return commands
    
    @staticmethod
    def get_command_completion_type():
        """创建命令补全类型"""
        return CommandCompletionType()


class Completer:
    """补全工具类"""
    
    @staticmethod
    def get_domains(domain: Optional[str] = None) -> List[str]:
        """获取领域名称列表"""
        try:
            path_manager = PathManager.get_instance()
            domains = path_manager.list_domains()
            # 如果指定了 domain，只返回匹配的（用于过滤）
            if domain:
                return [d for d in domains if d == domain]
            return domains
        except Exception:
            return []
    
    @staticmethod
    def get_program_groups(domain: Optional[str] = None) -> List[str]:
        """根据领域获取程序组列表"""
        try:
            path_manager = PathManager.get_instance()
            if domain:
                # 获取指定领域的程序组
                return path_manager.list_operation_groups(domain)
            else:
                # 获取所有程序组
                return path_manager.list_all_operation_groups()
        except Exception:
            return []
    
    @staticmethod
    def get_domain_type() -> ContextAwareChoice:
        """创建领域类型"""
        return ContextAwareChoice(Completer.get_domains)
    
    @staticmethod
    def get_program_group_type() -> ContextAwareChoice:
        """创建程序组类型（用于 -t 选项）"""
        return ContextAwareChoice(Completer.get_program_groups)
    
    @staticmethod
    def get_source_group_type() -> ContextAwareChoice:
        """创建源程序组类型（用于 -s 选项）"""
        return ContextAwareChoice(Completer.get_program_groups)
    
    @staticmethod
    def get_command_type():
        """创建命令补全类型"""
        return DynamicCompleter.get_command_completion_type()


class CommandCompletionType(click.ParamType):
    """命令补全类型"""
    name = "command"
    
    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str):
        completions = DynamicCompleter.get_command_completions(ctx, param, incomplete)
        # 使用 "plain" 类型避免自动转义
        return [CompletionItem(cmd, type="plain") for cmd in completions]


# 创建全局实例
completer = Completer()
COMMAND_COMPLETION_TYPE = CommandCompletionType()