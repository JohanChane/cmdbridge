from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    FATAL = 50
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """Convert from string to log level"""
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
            raise ValueError(f"Unknown log level: {level_str}")
        return level_map[lower_level]