# 在 cmdbridge/config/__init__.py 中添加：

from .operation_mapping_creator import OperationMappingCreator, create_operation_mappings_for_domain, create_operation_mappings_for_all_domains

__all__ = [
    'CmdMappingCreator',
    'create_cmd_mappings_for_group',
    'create_cmd_mappings_for_domain',
    'OperationMappingCreator',  # 新增
    'create_operation_mappings_for_domain',  # 新增
    'create_operation_mappings_for_all_domains',  # 新增
    'PathManager',
]