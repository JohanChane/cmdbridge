"""CmdBridge 工具模块"""

from .core import CmdBrIO, cmdbr_io

# 创建全局实例
cmdbr_io = CmdBrIO()

# 便捷函数
def cprint(*args, **kwargs):
    """便捷的智能打印函数"""
    cmdbr_io.print(*args, **kwargs)

def csecho(*args, **kwargs):
    """便捷的带样式智能打印函数"""
    cmdbr_io.secho(*args, **kwargs)

__all__ = [
    'CmdBrIO',
    'cmdbr_io',
    'cprint',
    'csecho',
    'set_out',
    'get_out',
]