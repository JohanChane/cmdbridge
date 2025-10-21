# log/levels.py
from enum import Enum

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    FATAL = 50
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """从字符串转换为日志级别"""
        level_map = {
            'debug': cls.DEBUG,
            'info': cls.INFO,
            'success': cls.SUCCESS,
            'warning': cls.WARNING,
            'error': cls.ERROR,
            'fatal': cls.FATAL,
        }
        lower_level = level_str.lower()
        if lower_level not in level_map:
            raise ValueError(f"未知的日志级别: {level_str}")
        return level_map[lower_level]