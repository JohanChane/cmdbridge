import sys
from typing import List, Optional
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from cmdbridge.config.path_manager import PathManager
from cmdbridge.cache.cache_mgr import CacheMgr
from log import debug, warning, error
from cmdbridge.cli_common import CommonCompletorHelper


class CompletorHelper:
    @staticmethod
    def get_domains() -> List[str]:
        return CommonCompletorHelper.get_domains()

    @staticmethod
    def get_operation_groups(domain: str) -> List[str]:
        return CommonCompletorHelper.get_operation_groups(domain)

    @staticmethod
    def get_all_operation_groups() -> List[str]:
        return CommonCompletorHelper.get_all_operation_groups()

    @staticmethod
    def get_commands(domain: Optional[str], source_group: str) -> List[str]:
        return CommonCompletorHelper.get_commands(domain, source_group)

    @staticmethod
    def get_all_commands(domain: Optional[str]) -> List[str]:
        return CommonCompletorHelper.get_all_commands(domain)

    @staticmethod
    def get_operation_names(domain: Optional[str], dest_group: Optional[str]) -> List[str]:
        return CommonCompletorHelper.get_operation_names(domain, dest_group)
    
    @staticmethod
    def get_all_operation_names(domain: Optional[str] = None) -> List[str]:
        return CommonCompletorHelper.get_all_operation_names(domain)
    @staticmethod
    def get_operation_with_params(domain: str, operation_name: str, dest_group: str) -> str:
        return CommonCompletorHelper.get_operation_with_params(domain, operation_name, dest_group)