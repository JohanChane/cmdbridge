# 在 cmdbridge/config/__init__.py 中添加：

from .operation_mapping_mgr import OperationMappingMgr, create_operation_mappings_for_domain, create_operation_mappings_for_all_domains

__all__ = [
    'CmdMappingCreator',
    'create_cmd_mappings_for_group',
    'create_cmd_mappings_for_domain',
    'OperationMappingMgr',  # 新增
    'create_operation_mappings_for_domain',  # 新增
    'create_operation_mappings_for_all_domains',  # 新增
    'PathManager',
]