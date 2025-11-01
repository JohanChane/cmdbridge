"""
Purpose: Unify output for easy future modifications. The reason is that when click outputs characters to stdout during completion, it can cause completion errors.
"""

import click
import sys
from typing import Optional, TextIO


class CmdBrIO:
    def __init__(self, out: Optional[TextIO] = None):
        """
        Initialize CmdBrIO

        :param out: Default output stream (optional), if None, use click's default stdout/stderr
        """
        self._out = out

    def _is_completion_mode(self):
        """Check if in completion mode"""
        try:
            ctx = click.get_current_context(silent=True)
            return bool(ctx and ctx.resilient_parsing)
        except Exception:
            return False

    def print(self, *args, **kwargs):
        """Smart printing: output to stderr in completion mode, output to terminal or custom stream in normal mode"""
        message = " ".join(str(arg) for arg in args)

        in_completion = self._is_completion_mode()

        # Force output to stderr in completion mode, takes priority over custom out
        if in_completion:
            kwargs['err'] = True
            click.echo(message, **kwargs)
        else:
            # Non-completion mode, use custom output stream or default
            if self._out is not None:
                kwargs['file'] = self._out
            click.echo(message, **kwargs)

    def secho(self, *args, **kwargs):
        """Smart printing with styles"""
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