# cmdbridge/click_ext/__init__.py

"""Click 扩展模块，提供动态补全支持"""

from .completor import (
    ContextAwareChoice,
    DynamicCompleter,
    Completer,
    CommandCompletionType,
    OperationCompletionType,
    completer,
    COMMAND_COMPLETION_TYPE,
    OPERATION_COMPLETION_TYPE
)
from .params import (
    domain_option,
    dest_group_option,
    source_group_option,
    command_argument,
    operation_argument
)

__all__ = [
    'ContextAwareChoice',
    'DynamicCompleter', 
    'Completer',
    'CommandCompletionType',
    'OperationCompletionType',
    'completer',
    'COMMAND_COMPLETION_TYPE',
    'OPERATION_COMPLETION_TYPE',
    'domain_option',
    'dest_group_option',
    'source_group_option',
    'command_argument',
    'operation_argument'
]