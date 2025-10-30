import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge.cmdbridge import CmdBridge
from cmdbridge.cache.cache_mgr import CacheMgr
from ..cli_common import CommonCliHelper

class CmdBridgeCLIHelper:
    """cmdbridge 命令行辅助类 - 处理 CLI 业务逻辑"""
    
    def __init__(self):
        self._common_cli_helper = CommonCliHelper()
    
    def _get_common_cli_helper(self) -> CommonCliHelper:
        return self._common_cli_helper
    
    def _get_cmdbridge(self) -> CmdBridge:
        return self._get_common_cli_helper().get_cmdbridge()
    
    def handle_debug_mode(self, debug: bool) -> None:
        return self._get_common_cli_helper().handle_debug_mode(debug)

    def handle_version(self) -> None:
        return self._get_common_cli_helper().handle_version()

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        return self._get_common_cli_helper().handle_map_command(domain, src_group, dest_group, command_args)

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        return self._get_common_cli_helper().handle_map_operation(domain, dest_group, operation_args)

    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        return self._get_common_cli_helper().get_domain_for_group(group_name)
    
    def handle_init_config(self) -> bool:
        """初始化用户配置"""
        success = self._get_cmdbridge().init_config()
        if success:
            click.echo("✅ 用户配置初始化成功")
        else:
            click.echo("❌ 用户配置初始化失败", err=True)
        return success

    def handle_refresh_cache(self) -> bool:
        """刷新命令映射缓存"""
        success = self._get_cmdbridge().refresh_cmd_mappings()
        if success:
            click.echo("✅ 命令映射缓存刷新成功")
        else:
            click.echo("❌ 命令映射缓存刷新失败", err=True)
        return success
    
    def handle_list_op_cmds(self, domain: Optional[str], dest_group: str) -> None:
        """输出动作映射 - 使用 shlex 处理参数显示"""
        cache_mgr = CacheMgr.get_instance()
        domain = domain or self.get_domain_for_group(dest_group)
        if domain is None:
            raise ValueError("需要指定 domain")

        if dest_group:
            operations = cache_mgr.get_supported_operations(domain, dest_group)
            
            if not operations:
                click.echo("❌ 该程序组不支持任何操作")
                return
            
            # 收集所有操作和参数信息
            op_data = []
            for op in sorted(operations):
                # 获取操作参数
                params = cache_mgr.get_operation_parameters(domain, op, dest_group)
                op_data.append((op, params))
            
            # 计算最大操作名称长度用于对齐
            max_op_len = max(len(op) for op, _ in op_data) if op_data else 0
            
            # 使用 shlex 安全地格式化参数
            for op, params in op_data:
                if params:
                    # 使用 shlex.quote 确保参数安全显示
                    param_display = ' '.join([f'{{{param}}}' for param in params])
                    # 对齐输出
                    click.echo(f"{op:<{max_op_len}} {param_display}")
                else:
                    click.echo(f"{op:<{max_op_len}}")
        else:
            operations = cache_mgr.get_all_operations(domain)
            for op in sorted(operations):
                click.echo(op)

    def handle_list_cmd_mappings(self, domain: Optional[str], source_group: Optional[str], 
                            dest_group: Optional[str]) -> None:
        """输出命令之间的映射 - 简化版本"""
        cache_mgr = CacheMgr.get_instance()
        
        # 设置默认值
        if source_group is None:
            raise ValueError("需要指定 source_group")
        if dest_group is None:
            raise ValueError("需要指定 dest_group")
        domain = domain or self.get_domain_for_group(dest_group)
        if domain is None:
            raise ValueError("需要指定 domain")

        # 获取所有操作
        operations = cache_mgr.get_all_operations(domain)
        if not operations:
            click.echo("❌ 未找到任何操作")
            return
        
        # 收集数据
        operation_data = []
        
        for operation in operations:
            # 获取源命令格式
            source_programs = cache_mgr.get_supported_programs(domain, operation)
            if source_group not in [pg for pg in source_programs]:
                continue
                
            source_cmd_format = cache_mgr.get_command_format(domain, operation, source_group)
            if not source_cmd_format:
                continue
                
            # 获取目标命令格式
            target_cmd_format = cache_mgr.get_command_format(domain, operation, dest_group)
            final_cmd_format = cache_mgr.get_final_command_format(domain, operation, dest_group)
            
            if target_cmd_format or final_cmd_format:
                display_cmd = final_cmd_format if final_cmd_format else target_cmd_format
                operation_data.append((operation, source_cmd_format, display_cmd))
        
        if not operation_data:
            click.echo("❌ 未找到有效的命令映射")
            return
        
        # 计算列宽
        max_op_len = max(len(op) for op, _, _ in operation_data)
        max_source_len = max(len(source) for _, source, _ in operation_data)
        
        # 输出对齐的结果        
        for operation, source, target in operation_data:
            click.echo(f"{operation:<{max_op_len}} {source:<{max_source_len}} -> {target}")