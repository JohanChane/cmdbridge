# log/core.py
import click
from typing import Any, Optional
from .levels import LogLevel

class Logger:
    """独立的日志类，内部使用 Click 但对外透明"""
    
    def __init__(self, 
                 level: LogLevel = LogLevel.INFO, 
                 show_timestamp: bool = False,
                 use_icons: bool = True):
        self.level = level
        self.show_timestamp = show_timestamp
        self.use_icons = use_icons
        self._debug_mode = (level == LogLevel.DEBUG)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        self.level = level
        self._debug_mode = (level == LogLevel.DEBUG)
    
    def set_level_from_string(self, level_str: str) -> None:
        """从字符串设置日志级别"""
        self.set_level(LogLevel.from_string(level_str))
    
    def _should_log(self, message_level: LogLevel) -> bool:
        """检查是否应该记录该级别的日志"""
        return message_level.value >= self.level.value
    
    def _get_icon(self, level: LogLevel) -> str:
        """获取日志图标"""
        if not self.use_icons:
            return ""
        
        icons = {
            LogLevel.DEBUG: "🐛",
            LogLevel.INFO: "ℹ️",
            LogLevel.SUCCESS: "✅",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.FATAL: "💀",
        }
        return icons.get(level, "")
    
    def _get_style(self, level: LogLevel) -> tuple[str, Optional[str]]:
        """根据日志级别返回颜色样式"""
        styles = {
            LogLevel.DEBUG: ('cyan', None),
            LogLevel.INFO: ('blue', None),
            LogLevel.SUCCESS: ('green', None),
            LogLevel.WARNING: ('yellow', None),
            LogLevel.ERROR: ('red', None),
            LogLevel.FATAL: ('red', True),  # 粗体红色
        }
        return styles.get(level, ('white', None))
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """格式化消息"""
        icon = self._get_icon(level)
        if icon:
            return f"{icon} {message}"
        else:
            level_name = level.name.lower()
            return f"{level_name.upper()}: {message}"
    
    def _log(self, 
             level: LogLevel, 
             message: str, 
             file: Any = None, 
             **kwargs: Any) -> None:
        """内部日志方法"""
        if not self._should_log(level):
            return
        
        formatted_message = self._format_message(level, message)
        color, bold = self._get_style(level)
        
        # 使用 Click 进行输出，但外部不知道这个实现细节
        output_kwargs = {'fg': color}
        if bold:
            output_kwargs['bold'] = True
        
        # 如果指定了输出文件，则传递
        if file is not None:
            output_kwargs['file'] = file
        
        click.secho(formatted_message, **output_kwargs, **kwargs)
    
    # 公共日志方法
    def debug(self, message: str, **kwargs: Any) -> None:
        """调试信息"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """一般信息"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def success(self, message: str, **kwargs: Any) -> None:
        """成功信息"""
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """警告信息"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """错误信息"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def fatal(self, message: str, **kwargs: Any) -> None:
        """致命错误信息（并退出程序）"""
        self._log(LogLevel.FATAL, message, **kwargs)
        exit(1)
    
    def plain(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> None:
        """纯文本输出（无图标）"""
        icon_backup = self.use_icons
        self.use_icons = False
        try:
            self._log(level, message, **kwargs)
        finally:
            self.use_icons = icon_backup
    
    def progress(self, message: str, **kwargs: Any) -> None:
        """进度信息"""
        self._log(LogLevel.INFO, f"⏳ {message}", **kwargs)
    
    def step(self, message: str, **kwargs: Any) -> None:
        """步骤信息"""
        self._log(LogLevel.INFO, f"➡️ {message}", **kwargs)
    
    def is_debug(self) -> bool:
        """是否处于调试模式"""
        return self._debug_mode