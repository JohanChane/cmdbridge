# utils/completion.py

from typing import List
from .config import ConfigUtils


class CompletionUtils:
    """补全工具类 - 包装 ConfigUtils 的补全功能"""
    
    def __init__(self, configs_dir: str = "configs", cache_dir: str = "output"):
        """
        初始化补全工具
        
        Args:
            configs_dir: 配置目录路径
            cache_dir: 缓存目录路径
        """
        self.config_utils = ConfigUtils(configs_dir, cache_dir)
    
    def list_domains(self) -> List[str]:
        """列出所有领域名称"""
        return self.config_utils.list_domains()
    
    def list_groups_in_domain(self, domain_name: str) -> List[str]:
        """列出指定领域中的所有程序组名称"""
        return self.config_utils.list_groups_in_domain(domain_name)
    
    def list_commands_in_domain_group(self, domain_name: str, group_name: str = None) -> List[str]:
        """列出指定领域和程序组中的所有命令名称"""
        return self.config_utils.list_commands_in_domain_group(domain_name, group_name)