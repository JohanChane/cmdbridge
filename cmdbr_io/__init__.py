"""CmdBridge Utility Module"""

from .core import CmdBrIO

# Create global instance
cmdbr_io = CmdBrIO()

# Convenience functions
def cprint(*args, **kwargs):
    """Convenient smart print function"""
    cmdbr_io.print(*args, **kwargs)

def csecho(*args, **kwargs):
    """Convenient styled smart print function"""
    cmdbr_io.secho(*args, **kwargs)

__all__ = [
    'CmdBrIO',
    'cmdbr_io',
    'cprint',
    'csecho',
]