import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge.cmdbridge import CmdBridge
from cmdbridge.cache.cache_mgr import CacheMgr

class CmdBridgeCLIHelper:
    """cmdbridge 命令行辅助类 - 处理 CLI 业务逻辑"""
    
    def __init__(self):
        # 初始化 CmdBridge 核心功能
        self.cmdbridge = CmdBridge()

    def _get_default_domain(self) -> str:
        """获取默认领域"""
        return self.cmdbridge._get_default_domain()
    
    def _get_default_group(self) -> str:
        """获取默认程序组"""
        return self.cmdbridge._get_default_group()
    
    def handle_debug_mode(self, debug: bool) -> None:
        """处理调试模式设置"""
        if debug:
            set_level(LogLevel.DEBUG)
            click.echo("🔧 调试模式已启用")
        else:
            set_level(LogLevel.INFO)

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令
        
        返回:
            bool: 成功返回 True，失败返回 False
        """
        if not command_args:
            click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
            return False
        
        result = self.cmdbridge.map_command(domain, src_group, dest_group, command_args)
        if result:
            # 输出映射后的命令到标准输出
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射命令", err=True)
            return False

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        """映射操作和参数
        
        返回:
            bool: 成功返回 True，失败返回 False
        """
        if not operation_args:
            click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
            return False
        
        result = self.cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            # 输出映射后的命令到标准输出
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射操作", err=True)
            return False

    def handle_version(self) -> None:
        """处理版本信息显示"""
        from .. import __version__
        click.echo(f"cmdbridge 版本: {__version__}")

    def handle_init_config(self) -> bool:
        """初始化用户配置"""
        success = self.cmdbridge.init_config()
        if success:
            click.echo("✅ 用户配置初始化成功")
        else:
            click.echo("❌ 用户配置初始化失败", err=True)
        return success

    def handle_refresh_cache(self) -> bool:
        """刷新命令映射缓存"""
        success = self.cmdbridge.refresh_cmd_mappings()
        if success:
            click.echo("✅ 命令映射缓存刷新成功")
        else:
            click.echo("❌ 命令映射缓存刷新失败", err=True)
        return success

    def handle_list_op_cmds(self, domain: Optional[str], dest_group: Optional[str]) -> None:
        """输出动作映射 - 使用 shlex 处理参数显示"""
        cache_mgr = CacheMgr.get_instance()
        domain = domain or self._get_default_domain()
        dest_group = dest_group or self._get_default_group()
        
        if dest_group:
            operations = cache_mgr.get_supported_operations(domain, dest_group)
            
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
        """输出命令之间的映射 - 使用 shlex 处理复杂命令"""        
        cache_mgr = CacheMgr.get_instance()
        
        # 设置默认值
        domain = domain or self._get_default_domain()
        source_group = source_group or self._get_default_group()
        dest_group = dest_group or self._get_default_group()
        
        # 获取源程序组的命令映射
        cmd_mappings = cache_mgr.get_cmd_mappings(domain, source_group)
        if not cmd_mappings:
            click.echo("❌ 未找到命令映射")
            return
        
        # 收集数据
        operations = []
        sources = []
        targets = []
        
        for mapping in cmd_mappings.get(source_group, {}).get("command_mappings", []):
            operation = mapping.get("operation", "")
            cmd_format = mapping.get("cmd_format", "")
            
            target_cmd_format = cache_mgr.get_command_format(domain, operation, dest_group)
            final_cmd_format = cache_mgr.get_final_command_format(domain, operation, dest_group)
            
            if target_cmd_format or final_cmd_format:
                display_cmd = final_cmd_format if final_cmd_format else target_cmd_format
                operations.append(f"{operation}:")
                sources.append(cmd_format)
                targets.append(display_cmd)
        
        if not operations:
            click.echo("❌ 未找到有效的命令映射")
            return
        
        # 计算列宽
        max_op_len = max(len(op) for op in operations)
        max_source_len = max(len(source) for source in sources)
        
        # 输出对齐的结果
        for op, source, target in zip(operations, sources, targets):
            click.echo(f"{op:<{max_op_len}} {source:<{max_source_len}} -> {target}")


# 便捷函数
def create_cli_helper() -> CmdBridgeCLIHelper:
    """创建 cmdbridge CLI 辅助类实例"""
    return CmdBridgeCLIHelper()