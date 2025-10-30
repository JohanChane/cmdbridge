import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge.cmdbridge import CmdBridge
from cmdbridge.cache.cache_mgr import CacheMgr

class CommonCliHelper:
    """cmdbridge 命令行辅助类 - 处理 CLI 业务逻辑"""
    
    def __init__(self):
        # 初始化 CmdBridge 核心功能
        self._cmdbridge = CmdBridge()
    
    def get_cmdbridge(self) -> CmdBridge:
        return self._cmdbridge
    
    def handle_debug_mode(self, debug: bool) -> None:
        """处理调试模式设置"""
        if debug:
            set_level(LogLevel.DEBUG)
            click.echo("🔧 调试模式已启用")
        else:
            set_level(LogLevel.INFO)

    def handle_version(self) -> None:
        """处理版本信息显示"""
        from .. import __version__
        click.echo(f"cmdbridge 版本: {__version__}")

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令
        
        返回:
            bool: 成功返回 True，失败返回 False
        """
        if not command_args:
            click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
            return False
        
        result = self._cmdbridge.map_command(domain, src_group, dest_group, command_args)
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
        
        result = self._cmdbridge.map_operation(domain, dest_group, operation_args)
        if result:
            # 输出映射后的命令到标准输出
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射操作", err=True)
            return False
        
    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        """根据程序组名称获取所属领域"""
        return self.get_cmdbridge().path_manager.get_domain_for_group(group_name)