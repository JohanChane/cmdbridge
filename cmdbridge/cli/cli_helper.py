# cmdbridge/cli/cli_helper.py

import sys
from typing import Optional, List, Dict, Any
import click
from pathlib import Path

from log import set_level, LogLevel, error, info, debug
from ..cmdbridge import CmdBridge  # 更新导入路径


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
    
    def handle_debug_mode(self, debug_flag: bool) -> None:
        """处理调试模式设置"""
        if debug_flag:
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
        from .. import __version__  # 更新导入路径
        click.echo(f"cmdbridge 版本: {__version__}")

    def handle_list_op_cmds(self, domain: Optional[str], dest_group: Optional[str]) -> None:
        """输出动作映射"""
        try:
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            debug(f"输出动作映射 - 领域: {domain}, 目标组: {dest_group}")
            
            # 获取操作映射器
            operation_mapper = self.cmdbridge.operation_mapper
            
            # 获取所有操作
            all_operations = operation_mapper.get_all_operations()
            
            if not all_operations:
                click.echo("❌ 没有找到任何操作映射")
                return
            
            click.echo(f"================================================================================")
            click.echo(f"操作映射 - 领域: {domain}, 目标程序组: {dest_group}")
            click.echo(f"--------------------------------------------------------------------------------")
            click.echo(f"操作名称                支持的程序")
            click.echo(f"--------------------------------------------------------------------------------")
            
            for operation in sorted(all_operations):
                supported_programs = operation_mapper.list_supported_programs(operation)
                
                # 如果指定了目标组，只显示支持该组的操作
                if dest_group and dest_group not in supported_programs:
                    continue
                
                # 高亮显示目标组
                programs_display = []
                for program in sorted(supported_programs):
                    if program == dest_group:
                        programs_display.append(f"**{program}**")
                    else:
                        programs_display.append(program)
                
                click.echo(f"{operation:20} {', '.join(programs_display)}")
            
            click.echo(f"================================================================================")
            info(f"共显示 {len([op for op in all_operations if not dest_group or dest_group in operation_mapper.list_supported_programs(op)])} 个操作")
            
        except Exception as e:
            error(f"输出动作映射失败: {e}")
            click.echo("❌ 输出动作映射失败", err=True)

    def handle_list_cmd_mappings(self, domain: Optional[str], src_group: Optional[str], 
                               dest_group: Optional[str]) -> None:
        """输出命令之间的映射"""
        try:
            # 设置默认值
            domain = domain or self._get_default_domain()
            src_group = src_group or self._get_default_group()
            dest_group = dest_group or self._get_default_group()
            
            debug(f"输出命令映射 - 领域: {domain}, 源组: {src_group}, 目标组: {dest_group}")
            
            # 检查源组和目标组是否存在
            if not self.cmdbridge.path_manager.operation_group_exists(domain, src_group):
                click.echo(f"❌ 源程序组 '{src_group}' 在领域 '{domain}' 中不存在")
                return
            
            if not self.cmdbridge.path_manager.operation_group_exists(domain, dest_group):
                click.echo(f"❌ 目标程序组 '{dest_group}' 在领域 '{domain}' 中不存在")
                return
            
            # 加载源组的命令映射
            src_mapping_config = self.cmdbridge._get_mapping_config(domain, src_group)
            
            if not src_mapping_config or src_group not in src_mapping_config:
                click.echo(f"❌ 源程序组 '{src_group}' 没有命令映射配置")
                return
            
            command_mappings = src_mapping_config[src_group].get("command_mappings", [])
            
            if not command_mappings:
                click.echo(f"❌ 源程序组 '{src_group}' 没有可用的命令映射")
                return
            
            click.echo(f"================================================================================")
            click.echo(f"命令映射 - 领域: {domain}")
            click.echo(f"源程序组: {src_group} -> 目标程序组: {dest_group}")
            click.echo(f"--------------------------------------------------------------------------------")
            click.echo(f"操作名称                源命令格式                   目标命令格式")
            click.echo(f"--------------------------------------------------------------------------------")
            
            displayed_count = 0
            
            for mapping in command_mappings:
                operation_name = mapping.get("operation", "")
                cmd_format = mapping.get("cmd_format", "")
                
                # 生成目标命令格式
                target_cmd_format = self._generate_target_command_format(
                    operation_name, domain, dest_group
                )
                
                if target_cmd_format:
                    click.echo(f"{operation_name:20} {cmd_format:25} {target_cmd_format}")
                    displayed_count += 1
                else:
                    # 如果目标组不支持该操作，显示不支持
                    click.echo(f"{operation_name:20} {cmd_format:25} ❌ 不支持")
            
            click.echo(f"================================================================================")
            info(f"共显示 {displayed_count} 个命令映射")
            
        except Exception as e:
            error(f"输出命令映射失败: {e}")
            click.echo("❌ 输出命令映射失败", err=True)

    def _generate_target_command_format(self, operation_name: str, domain: str, dest_group: str) -> str:
        """生成目标命令格式"""
        try:
            # 检查目标组是否支持该操作
            if not self.cmdbridge.operation_mapper.is_operation_supported(operation_name, dest_group):
                return ""
            
            # 获取目标组的命令格式
            target_cmd_format = self.cmdbridge.operation_mapper.get_command_format(
                operation_name, dest_group
            )
            
            return target_cmd_format or ""
            
        except Exception as e:
            debug(f"生成目标命令格式失败: {e}")
            return ""


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