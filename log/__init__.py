from .core import Logger
from .levels import LogLevel
from typing import Any, Optional, TextIO

# Global logger instance
_global_logger = Logger()

def setup_logging(level: LogLevel = LogLevel.INFO, 
                  show_timestamp: bool = False,
                  use_icons: bool = True) -> None:
    """Set global logging configuration"""
    _global_logger.set_level(level)
    _global_logger.show_timestamp = show_timestamp
    _global_logger.use_icons = use_icons

def set_level(level: LogLevel) -> None:
    """Set global log level"""
    _global_logger.set_level(level)

def set_level_from_string(level_str: str) -> None:
    """Set global log level from string"""
    _global_logger.set_level_from_string(level_str)

# Convenience functions
def debug(message: str, **kwargs) -> None:
    _global_logger.debug(message, **kwargs)

def info(message: str, **kwargs) -> None:
    _global_logger.info(message, **kwargs)

def success(message: str, **kwargs) -> None:
    _global_logger.success(message, **kwargs)

def warning(message: str, **kwargs) -> None:
    _global_logger.warning(message, **kwargs)

def error(message: str, **kwargs) -> None:
    _global_logger.error(message, **kwargs)

def fatal(message: str, **kwargs) -> None:
    _global_logger.fatal(message, **kwargs)

def plain(message: str, level: LogLevel = LogLevel.INFO, **kwargs) -> None:
    _global_logger.plain(message, level, **kwargs)

def progress(message: str, **kwargs) -> None:
    _global_logger.progress(message, **kwargs)

def step(message: str, **kwargs) -> None:
    _global_logger.step(message, **kwargs)

def is_debug() -> bool:
    """Check if in debug mode"""
    return _global_logger.is_debug()

def get_logger() -> Logger:
    """Get global logger instance"""
    return _global_logger

def create_logger(level: LogLevel = LogLevel.INFO, 
                  show_timestamp: bool = False,
                  use_icons: bool = True) -> Logger:
    """Create logger instance"""
    return Logger(level, show_timestamp, use_icons)

def set_out(out: Optional[TextIO] = None):
    return _global_logger.set_out(out)

def get_out(out: Optional[TextIO] = None) -> Optional[TextIO]:
    return _global_logger.get_out()

__all__ = [
    'Logger',
    'LogLevel',
    'setup_logging',
    'set_level',
    'set_level_from_string',
    'debug',
    'info',
    'success',
    'warning',
    'error',
    'fatal',
    'plain',
    'progress',
    'step',
    'is_debug',
    'get_logger',
    'create_logger',
    'set_out',
    'get_out',
]