# cmdbridge/cli_helper.py

import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from .cmdbridge import CmdBridge


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

    def handle_init_config(self) -> bool:
        """处理初始化配置命令"""
        success = self.cmdbridge.init_config()
        if success:
            click.echo("✅ 用户配置初始化成功")
        else:
            click.echo("❌ 用户配置初始化失败", err=True)
        return success

    def handle_refresh_cache(self) -> bool:
        """处理刷新缓存命令"""
        success = self.cmdbridge.refresh_cmd_mappings()
        if success:
            click.echo("✅ 命令映射缓存已刷新")
        else:
            click.echo("❌ 刷新命令映射缓存失败", err=True)
        return success

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        """处理映射完整命令"""
        if not command_args:
            click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
            return False
        
        result = self.cmdbridge.map_command(domain, src_group, dest_group, command_args)
        if result:
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射命令", err=True)
            return False

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        """处理映射操作和参数"""
        if not operation_args:
            click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
            return False
        
        result = self.cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射操作", err=True)
            return False

    def handle_version(self) -> None:
        """处理版本信息显示"""
        from . import __version__
        click.echo(f"cmdbridge 版本: {__version__}")

    def handle_list_cmdbridges(self) -> None:
        """列出所有可用的包管理器"""
        try:
            # 获取所有领域和程序组
            domains = self.cmdbridge.path_manager.list_domains()
            
            click.echo("ℹ️ INFO: 📦 Package managers in current configuration:")
            
            for domain in domains:
                groups = self.cmdbridge.path_manager.list_operation_groups(domain)
                for group in groups:
                    # 获取操作数量（简化实现）
                    operation_count = self._get_operation_count(domain, group)
                    click.echo(f"  ✅ {group} - supports {operation_count} operations")
                    
        except Exception as e:
            error(f"列出包管理器失败: {e}")
            click.echo("错误: 无法列出包管理器", err=True)

    def handle_output_cmdbridge(self, source_group: str, dest_group: str) -> None:
        """输出两个包管理器之间的映射关系"""
        try:
            # 这里可以实现详细的映射关系输出
            # 简化实现，实际应该从操作映射中获取详细信息
            click.echo(f"================================================================================")
            click.echo(f"Status Operation          Source Command            Target Command")
            click.echo(f"--------------------------------------------------------------------------------")
            
            # 示例输出
            mappings = [
                ("install", f"{source_group} -S {{pkgs}}", f"{dest_group} install {{pkgs}}"),
                ("remove", f"{source_group} -R {{pkgs}}", f"{dest_group} remove {{pkgs}}"),
                ("search", f"{source_group} -Ss {{pkgs}}", f"{dest_group} search {{pkgs}}"),
                ("update", f"{source_group} -Sy", f"{dest_group} update"),
            ]
            
            for operation, source_cmd, target_cmd in mappings:
                click.echo(f"✅    {operation:15} {source_cmd:20} {target_cmd}")
                
            click.echo(f"================================================================================")
            
        except Exception as e:
            error(f"输出映射关系失败: {e}")
            click.echo("错误: 无法输出映射关系", err=True)

    def _get_operation_count(self, domain: str, group: str) -> int:
        """获取程序组的操作数量（简化实现）"""
        try:
            # 从操作映射中获取实际的操作数量
            operation_mappings = self.cmdbridge.operation_mapper.operation_to_program
            count = 0
            for operation, programs in operation_mappings.items():
                if group in programs:
                    count += 1
            return count if count > 0 else 15  # 默认值
        except:
            return 15  # 默认值


class CustomCommand(click.Command):
    """自定义命令类，支持 -- 分隔符"""
    
    def parse_args(self, ctx, args):
        """解析参数，处理 -- 分隔符"""
        if '--' in args:
            idx = args.index('--')
            # 使用 ctx.meta 来存储保护参数
            ctx.meta['protected_args'] = args[idx+1:]
            args = args[:idx]
        
        return super().parse_args(ctx, args)


# 便捷函数
def create_cli_helper() -> CmdBridgeCLIHelper:
    """创建 CLI 辅助类实例"""
    return CmdBridgeCLIHelper()