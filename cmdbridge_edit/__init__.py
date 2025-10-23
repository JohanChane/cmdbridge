# cmdbridge-edit/__init__.py

"""CmdBridge Edit - Line Editor Integration"""

__version__ = "1.0.0"
__author__ = "CmdBridge Developer"

from .cli import main, cli

__all__ = [
    'main',
    'cli',
    '__version__',
    '__author__',
]