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

    def exit_with_success_code(self, success: bool) -> None:
        """根据操作结果退出程序
        
        Args:
            success: 操作是否成功
        """
        # 使用特殊退出码 113 表示成功映射（供 shell 函数识别）
        exit_code = 113 if success else 1
        sys.exit(exit_code)