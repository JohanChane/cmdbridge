# cmdbridge_edit/cli/cli_helper.py

import sys
from typing import Optional, List
import click

from log import set_level, LogLevel, error
from cmdbridge import CmdBridge
from cmdbridge.cli_common.cli_helper import CommonCliHelper

class CmdBridgeEditCLIHelper:
    """cmdbridge-edit 命令行辅助类 - 处理 CLI 业务逻辑"""

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
    
    def handle_debug_mode(self, debug: bool) -> None:
        """处理调试模式设置"""
        if debug:
            set_level(LogLevel.DEBUG)
            click.echo("🔧 调试模式已启用")
        else:
            set_level(LogLevel.INFO)

    def handle_version(self) -> None:
        """处理版本信息显示"""
        from .. import __version__  # 更新导入路径
        click.echo(f"cmdbridge-edit 版本: {__version__}")

    def handle_map_command(self, domain: Optional[str], src_group: Optional[str], 
                          dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令并输出到 line editor
        
        返回:
            bool: 成功返回 True，失败返回 False
        """
        if not command_args:
            click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
            return False
        
        result = self._get_cmdbridge().map_command(domain, src_group, dest_group, command_args)
        if result:
            # 输出映射后的命令到标准输出
            # 使用特殊返回码 113 表示成功映射（供 shell 函数识别）
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射命令", err=True)
            return False

    def handle_map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                           operation_args: List[str]) -> bool:
        """映射操作和参数并输出到 line editor
        
        返回:
            bool: 成功返回 True，失败返回 False
        """
        if not operation_args:
            click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
            return False
        
        result = self._get_cmdbridge().map_operation(domain, dest_group, operation_args)
        if result:
            # 输出映射后的命令到标准输出
            # 使用特殊返回码 113 表示成功映射（供 shell 函数识别）
            click.echo(result)
            return True
        else:
            click.echo("错误: 无法映射操作", err=True)
            return False

    def exit_with_success_code(self, success: bool) -> None:
        """根据操作结果退出程序
        
        Args:
            success: 操作是否成功
        """
        # 使用特殊退出码 113 表示成功映射（供 shell 函数识别）
        exit_code = 113 if success else 1
        sys.exit(exit_code)