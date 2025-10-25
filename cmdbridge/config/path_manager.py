import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from log import debug, info, warning, error


class PathManager:
    """路径管理器 - 统一管理配置和缓存目录路径（单例模式）"""
    
    _instance = None
    
    def __new__(cls, config_dir: Optional[str] = None, 
                cache_dir: Optional[str] = None,
                program_parser_config_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_dir: Optional[str] = None, 
                 cache_dir: Optional[str] = None,
                 program_parser_config_dir: Optional[str] = None):
        """
        初始化路径管理器
        
        Args:
            config_dir: 配置目录路径，如果为 None 则使用默认路径
            cache_dir: 缓存目录路径，如果为 None 则使用默认路径
            program_parser_config_dir: 程序解析器配置目录路径，如果为 None 则基于 config_dir
        """
        if self._initialized:
            return
            
        # 设置默认路径
        self._config_dir = Path(
            config_dir or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        ) / "cmdbridge"
        
        self._cache_dir = Path(
            cache_dir or os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        ) / "cmdbridge"
        
        # 程序解析器配置目录
        if program_parser_config_dir:
            self._program_parser_config_dir = Path(program_parser_config_dir)
        else:
            self._program_parser_config_dir = self._config_dir / "program_parser_configs"
        
        # 确保目录存在
        self._ensure_directories()
        self._initialized = True
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._program_parser_config_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_instance(cls) -> 'PathManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
    
    def list_domains(self) -> List[str]:
        """
        列出所有可用的领域名称
        
        Returns:
            List[str]: 领域名称列表，如 ["package", "process"]
        """
        domains = []
        
        if not self._config_dir.exists():
            return domains
        
        # 查找所有 *.domain 目录
        for item in self._config_dir.iterdir():
            if item.is_dir() and item.name.endswith('.domain'):
                domain_name = item.name[:-7]  # 移除 .domain 后缀
                domains.append(domain_name)
        
        return sorted(domains)
    
    def list_operation_groups(self, domain_name: str) -> List[str]:
        """
        列出指定领域中的所有操作组名称
        
        Args:
            domain_name: 领域名称
            
        Returns:
            List[str]: 操作组名称列表，如 ["apt", "pacman", "brew"]
        """
        groups = []
        domain_dir = self.get_config_operation_group_path(domain_name)
        
        if not domain_dir.exists():
            return groups
        
        # 查找所有 .toml 配置文件（排除 base.toml）
        for config_file in domain_dir.glob("*.toml"):
            group_name = config_file.stem
            groups.append(group_name)
        
        return sorted(groups)
    
    def list_all_operation_groups(self) -> List[str]:
        """
        列出所有领域中的所有操作组名称
        
        Returns:
            List[str]: 所有操作组名称列表
        """
        all_groups = []
        domains = self.list_domains()
        
        for domain in domains:
            domain_groups = self.list_operation_groups(domain)
            all_groups.extend(domain_groups)
        
        return sorted(list(set(all_groups)))  # 去重并排序
    
    def list_program_parser_configs(self) -> List[str]:
        """
        列出所有可用的程序解析器配置
        
        Returns:
            List[str]: 程序名称列表，如 ["apt", "pacman", "apt-file"]
        """
        programs = []
        
        if not self._program_parser_config_dir.exists():
            return programs
        
        # 查找所有 .toml 配置文件
        for config_file in self._program_parser_config_dir.glob("*.toml"):
            program_name = config_file.stem
            programs.append(program_name)
        
        return sorted(programs)
    
    def get_config_operation_group_path(self, domain_name: str) -> Path:
        """
        获取配置目录中的操作组文件路径
        
        Args:
            domain_name: 领域名称
            
        Returns:
            Path: 操作组配置文件路径
        """
        return self._config_dir / f"{domain_name}.domain"
    
    def get_cache_domain_path(self, domain_name: str) -> Path:
        """
        获取缓存目录中的操作组文件路径
        
        Args:
            domain_name: 领域名称
            
        Returns:
            Path: 操作组缓存文件路径
        """
        return self._cache_dir / "domains" / f"{domain_name}.domain"
    
    def get_program_parser_config_path(self, program_name: str) -> Path:
        """
        获取程序解析器配置文件路径
        
        Args:
            program_name: 程序名称
            
        Returns:
            Path: 解析器配置文件路径
        """
        return self._program_parser_config_dir / f"{program_name}.toml"
    
    def get_cmd_mappings_cache_path(self, domain_name: str, group_name: Optional[str] = None) -> Path:
        """
        获取命令映射缓存文件路径
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称，如果为 None 则返回目录路径
            
        Returns:
            Path: 命令映射缓存文件路径或目录路径
        """
        if group_name:
            return self._cache_dir / "cmd_mappings" / f"{domain_name}.domain" / f"{group_name}.toml"
        else:
            return self._cache_dir / "cmd_mappings" / f"{domain_name}.domain"
        
    def get_operation_mappings_cache_path(self, domain_name: str, group_name: Optional[str] = None) -> Path:
        """
        获取操作映射缓存文件路径
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称，如果为 None 则返回目录路径
            
        Returns:
            Path: 操作映射缓存文件路径或目录路径
        """
        if group_name:
            return self._cache_dir / "operation_mappings" / f"{domain_name}.domain" / f"{group_name}.toml"
        else:
            return self._cache_dir / "operation_mappings" / f"{domain_name}.domain"

    def get_operation_group_config_path(self, domain_name: str, group_name: str) -> Path:
        """ 
        获取特定操作组的配置文件路径
        
        Args:
            domain_name: 领域名称
            group_name: 操作组名称
            
        Returns:
            Path: 操作组配置文件路径
        """
        return self.get_config_operation_group_path(domain_name) / f"{group_name}.toml"
    
    def get_operation_group_cache_path(self, domain_name: str, group_name: str) -> Path:
        """
        获取特定操作组的缓存文件路径
        
        Args:
            domain_name: 领域名称
            group_name: 操作组名称
            
        Returns:
            Path: 操作组缓存文件路径
        """
        return self.get_cache_domain_path(domain_name) / f"{group_name}.toml"
    
    def get_base_operation_config_path(self, domain_name: str) -> Path:
        """
        获取基础操作配置文件路径
        
        Args:
            domain_name: 领域名称
            
        Returns:
            Path: 基础操作配置文件路径
        """
        return self.get_config_operation_group_path(domain_name) / "base.toml"
    
    def get_cmd_mappings_domain_dir(self, domain_name: str) -> Path:
        """获取命令映射领域目录路径"""
        return self.get_cmd_mappings_cache_path(domain_name)
    def get_operation_mappings_domain_dir(self, domain_name: str) -> Path:
        """获取操作映射领域目录路径"""
        return self.get_operation_mappings_cache_path(domain_name)

    def ensure_cmd_mappings_domain_dir(self, domain_name: str) -> None:
        """
        确保命令映射领域目录存在
        
        Args:
            domain_name: 领域名称
        """
        cmd_mappings_dir = self.get_cmd_mappings_domain_dir(domain_name)
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
    
    def rm_cmd_mappings_dir(self, domain_name: Optional[str] = None) -> bool:
        """
        删除命令映射目录
        
        Args:
            domain_name: 领域名称，如果为 None 则删除所有命令映射目录
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if domain_name is None:
                # 删除所有命令映射目录
                cmd_mappings_dir = self._cache_dir / "cmd_mappings"
                if cmd_mappings_dir.exists():
                    shutil.rmtree(cmd_mappings_dir)
                    debug(f"已删除所有命令映射目录: {cmd_mappings_dir}")
                return True
            else:
                # 删除指定领域的命令映射目录
                domain_cmd_mappings_dir = self.get_cmd_mappings_domain_dir(domain_name)
                if domain_cmd_mappings_dir.exists():
                    shutil.rmtree(domain_cmd_mappings_dir)
                    debug(f"已删除 {domain_name} 领域的命令映射目录: {domain_cmd_mappings_dir}")
                return True
        except Exception as e:
            error(f"删除命令映射目录失败: {e}")
            return False

    def rm_domain_cache_dir(self, domain_name: Optional[str] = None) -> bool:
        """
        删除领域缓存目录
        
        Args:
            domain_name: 领域名称，如果为 None 则删除所有领域缓存目录
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if domain_name is None:
                # 删除所有领域缓存目录
                domains_cache_dir = self._cache_dir / "domains"
                if domains_cache_dir.exists():
                    shutil.rmtree(domains_cache_dir)
                    debug(f"已删除所有领域缓存目录: {domains_cache_dir}")
                return True
            else:
                # 删除指定领域的缓存目录
                domain_cache_dir = self.get_cache_domain_path(domain_name)
                if domain_cache_dir.exists():
                    shutil.rmtree(domain_cache_dir)
                    debug(f"已删除 {domain_name} 领域的缓存目录: {domain_cache_dir}")
                return True
        except Exception as e:
            error(f"删除领域缓存目录失败: {e}")
            return False

    def rm_all_cache_dirs(self) -> bool:
        """
        删除所有缓存目录
        
        Returns:
            bool: 删除是否成功
        """
        try:
            if self._cache_dir.exists():
                shutil.rmtree(self._cache_dir)
                # 重新创建空的缓存目录
                self._cache_dir.mkdir(parents=True, exist_ok=True)
                debug(f"已删除并重新创建所有缓存目录: {self._cache_dir}")
            return True
        except Exception as e:
            error(f"删除所有缓存目录失败: {e}")
            return False

    # 属性访问器
    @property
    def config_dir(self) -> Path:
        """获取配置目录路径"""
        return self._config_dir
    
    @property
    def cache_dir(self) -> Path:
        """获取缓存目录路径"""
        return self._cache_dir
    
    @property
    def program_parser_config_dir(self) -> Path:
        """获取程序解析器配置目录路径"""
        return self._program_parser_config_dir
    
    def get_global_config_path(self) -> Path:
        """获取全局配置文件路径"""
        return self._config_dir / "config.toml"
    
    def ensure_cache_directories(self, domain_name: str) -> None:
        """
        确保缓存目录结构存在
        
        Args:
            domain_name: 领域名称
        """
        # 确保命令映射目录存在
        cmd_mappings_dir = self._cache_dir / "cmd_mappings" / domain_name
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保领域缓存目录存在
        domain_cache_dir = self._cache_dir / "domains" / f"{domain_name}.domain"
        domain_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def domain_exists(self, domain_name: str) -> bool:
        """
        检查领域是否存在
        
        Args:
            domain_name: 领域名称
            
        Returns:
            bool: 领域是否存在
        """
        domain_path = self.get_config_operation_group_path(domain_name)
        return domain_path.exists() and domain_path.is_dir()
    
    def operation_group_exists(self, domain_name: str, group_name: str) -> bool:
        """
        检查操作组是否存在
        
        Args:
            domain_name: 领域名称
            group_name: 操作组名称
            
        Returns:
            bool: 操作组是否存在
        """
        config_path = self.get_operation_group_config_path(domain_name, group_name)
        return config_path.exists()
    
    def program_parser_config_exists(self, program_name: str) -> bool:
        """
        检查程序解析器配置是否存在
        
        Args:
            program_name: 程序名称
            
        Returns:
            bool: 配置是否存在
        """
        config_path = self.get_program_parser_config_path(program_name)
        return config_path.exists()
    
    def get_group_mapping_cache_path(self, domain_name: str, group_name: str) -> Path:
        """
        获取程序组映射缓存文件路径
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称
            
        Returns:
            Path: 程序组映射缓存文件路径
        """
        return self.get_cmd_mappings_domain_dir(domain_name) / f"{group_name}.toml"
    
    def get_domain_base_config_path(self, domain_name: str) -> Path:
        """
        获取领域基础配置文件路径
        
        Args:
            domain_name: 领域名称
            
        Returns:
            Path: 领域基础配置文件路径
        """
        return self._config_dir / f"{domain_name}.domain.base.toml"

    def domain_base_config_exists(self, domain_name: str) -> bool:
        """
        检查领域基础配置文件是否存在
        
        Args:
            domain_name: 领域名称
            
        Returns:
            bool: 基础配置文件是否存在
        """
        return self.get_domain_base_config_path(domain_name).exists()