import click
from typing import Any, Optional, TextIO
from .levels import LogLevel


class Logger:
    """Independent logger class, internally uses Click but transparent externally"""
    
    def __init__(self, 
                 level: LogLevel = LogLevel.INFO, 
                 show_timestamp: bool = False,
                 use_icons: bool = True,
                 out: Optional[TextIO] = None):
        self.level = level
        self.show_timestamp = show_timestamp
        self.use_icons = use_icons
        self._debug_mode = (level == LogLevel.DEBUG)
        self._out = out  # Customizable output stream
        
    def set_level(self, level: LogLevel) -> None:
        """Set log level"""
        self.level = level
        self._debug_mode = (level == LogLevel.DEBUG)
    
    def set_level_from_string(self, level_str: str) -> None:
        """Set log level from string"""
        self.set_level(LogLevel.from_string(level_str))
    
    def _should_log(self, message_level: LogLevel) -> bool:
        """Check if this level should be logged"""
        return message_level.value >= self.level.value
    
    def _get_icon(self, level: LogLevel) -> str:
        """Get log icon"""
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
        """Return color style based on log level"""
        styles = {
            LogLevel.DEBUG: ('cyan', None),
            LogLevel.INFO: ('blue', None),
            LogLevel.SUCCESS: ('green', None),
            LogLevel.WARNING: ('yellow', None),
            LogLevel.ERROR: ('red', None),
            LogLevel.FATAL: ('red', True),  # Bold red
        }
        return styles.get(level, ('white', None))
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """Format message"""
        icon = self._get_icon(level)
        if icon:
            return f"{icon} {message}"
        else:
            return f"{level.name.upper()}: {message}"
    
    def _log(self, 
             level: LogLevel, 
             message: str, 
             **kwargs: Any) -> None:
        """Internal logging method"""
        if not self._should_log(level):
            return
        
        formatted_message = self._format_message(level, message)
        color, bold = self._get_style(level)
        
        # Click output parameters
        output_kwargs = {'fg': color}
        if bold:
            output_kwargs['bold'] = True

        # Use custom output stream if available
        if self._out is not None:
            output_kwargs['file'] = self._out

        click.secho(formatted_message, **output_kwargs, **kwargs)
    
    # Public logging methods
    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.INFO, message, **kwargs)
    
    def success(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def fatal(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.FATAL, message, **kwargs)
        exit(1)
    
    def plain(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> None:
        icon_backup = self.use_icons
        self.use_icons = False
        try:
            self._log(level, message, **kwargs)
        finally:
            self.use_icons = icon_backup
    
    def progress(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.INFO, f"⏳ {message}", **kwargs)
    
    def step(self, message: str, **kwargs: Any) -> None:
        self._log(LogLevel.INFO, f"➡️ {message}", **kwargs)
    
    def is_debug(self) -> bool:
        return self._debug_mode

    def set_out(self, out: Optional[TextIO]):
        self._out = out
    def get_out(self) -> Optional[TextIO]:
        return self._out