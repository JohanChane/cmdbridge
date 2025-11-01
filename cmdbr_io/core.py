"""
目的: 统一输出, 方便以后修改。原因是 click 在补全向 stdout 输出字符会导致补全出错。
"""

import click
import sys
from typing import Optional, TextIO


class CmdBrIO:
    def __init__(self, out: Optional[TextIO] = None):
        """
        初始化 CmdBrIO

        :param out: 默认输出流（可选），如果为 None，则使用 click 默认 stdout/stderr
        """
        self._out = out

    def _is_completion_mode(self):
        """检查是否在补全模式下"""
        try:
            ctx = click.get_current_context(silent=True)
            return bool(ctx and ctx.resilient_parsing)
        except Exception:
            return False

    def print(self, *args, **kwargs):
        """智能打印：补全模式下输出到 stderr，正常模式下输出到终端或自定义流"""
        message = " ".join(str(arg) for arg in args)

        in_completion = self._is_completion_mode()

        # 补全模式强制输出到 stderr，优先级高于自定义 out
        if in_completion:
            kwargs['err'] = True
            click.echo(message, **kwargs)
        else:
            # 非补全模式，使用自定义输出流或默认
            if self._out is not None:
                kwargs['file'] = self._out
            click.echo(message, **kwargs)

    def secho(self, *args, **kwargs):
        """带样式的智能打印"""
        message = " ".join(str(arg) for arg in args)

        in_completion = self._is_completion_mode()

        if in_completion:
            kwargs['err'] = True
            click.secho(message, **kwargs)
        else:
            if self._out is not None:
                kwargs['file'] = self._out
            click.secho(message, **kwargs)

    def set_out(self, out: Optional[TextIO]):
        self._out = out
    def get_out(self) -> Optional[TextIO]:
        return self._out