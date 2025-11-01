import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from log import debug, info, warning, error


class ConfigPathMgr:
    """配置路径管理器 - 专门管理配置相关的路径"""
    
    def __init__(self, base_config_dir: Path):
        """初始化配置路径管理器"""
        self._base_config_dir = base_config_dir
        self._program_parser_config_dir = base_config_dir / "program_parser_configs"
    
    def get_program_parser_path(self, program_name: str) -> Path:
        """获取程序解析器配置文件路径"""
        return self._program_parser_config_dir / f"{program_name}.toml"
    
    def get_domain_base_path(self, domain_name: str) -> Path:
        """获取领域基础配置文件路径"""
        return self._base_config_dir / f"{domain_name}.domain.base.toml"
    
    def get_operation_domain_dir(self, domain_name: str) -> Path:
        """获取配置目录中的操作组文件路径"""
        return self._base_config_dir / f"{domain_name}.domain"
    
    def get_operation_group_path(self, domain_name: str, group_name: str) -> Path:
        """获取特定操作组的配置文件路径"""
        return self.get_operation_domain_dir(domain_name) / f"{group_name}.toml"


class CachePathMgr:
    """缓存路径管理器 - 专门管理缓存相关的路径"""

    def __init__(self, base_cache_dir: Path):
        """初始化缓存路径管理器"""
        self._base_cache_dir = base_cache_dir
    
    def _operation_to_program_domain_dir(self, domain_name: str) -> Path:
        """获取缓存目录中的操作组文件路径"""
        return self._base_cache_dir / f"{domain_name}.domain"
    
    def get_operation_to_program_path(self, domain_name: str) -> Path:
        """获取操作到程序映射文件路径"""
        return self.get_operation_mappings_domain_dir(domain_name) / "operation_to_program.toml"
    
    def get_cmd_mappings_domain_dir(self, domain_name) -> Path:
        return self._base_cache_dir / "cmd_mappings" / f"{domain_name}.domain"
    
    def get_cmd_mappings_group_dir(self, domain_name: str, group_name: str) -> Path:
        """获取命令映射组目录路径"""
        return self.get_cmd_mappings_domain_dir(domain_name) / group_name
    
    def get_cmd_mappings_group_program_path(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """获取命令映射组中特定程序的命令文件路径"""
        return self.get_cmd_mappings_group_dir(domain_name, group_name) / f"{program_name}_command.toml"
    
    def get_cmd_to_operation_path(self, domain_name: str) -> Path:
        """获取命令到操作映射文件路径"""
        return self.get_cmd_mappings_domain_dir(domain_name) / "cmd_to_operation.toml"
    
    def get_operation_mappings_domain_dir(self, domain_name) -> Path:
        return self._base_cache_dir / "operation_mappings" / f"{domain_name}.domain"
    
    def get_operation_mappings_group_dir(self, domain_name: str, group_name: str) -> Path:
        """获取操作映射组目录路径"""
        return self.get_operation_mappings_domain_dir(domain_name) / group_name
    
    def get_operation_mappings_group_program_path(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """获取操作映射组中特定程序的命令文件路径"""
        return self.get_operation_mappings_group_dir(domain_name, group_name) / f"{program_name}_commands.toml"
    
    def get_operation_mappings_group_path(self, domain_name: str, group_name: str) -> Path:
        """获取操作映射缓存文件路径（兼容性方法）"""
        return self.get_operation_mappings_domain_dir(domain_name) / f"{group_name}.toml"

    def get_parser_config_dir(self) -> Path:
        """获取解析器配置缓存目录"""
        return self._base_cache_dir / "program_parser_configs"
    
    def get_parser_config_path(self, program_name: str) -> Path:
        """获取指定程序的解析器配置缓存文件路径"""
        return self.get_parser_config_dir() / f"{program_name}.toml"

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
        
        # 初始化内部路径管理器
        self._config_path_mgr = ConfigPathMgr(self._config_dir)
        self._cache_path_mgr = CachePathMgr(self._cache_dir)

        # 程序解析器配置目录
        if program_parser_config_dir:
            self._program_parser_config_dir = Path(program_parser_config_dir)
        else:
            self._program_parser_config_dir = self._config_dir / "program_parser_configs"
        
        # 确保目录存在
        self._ensure_directories()
        self._initialized = True
    
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
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._program_parser_config_dir.mkdir(parents=True, exist_ok=True)

    def ensure_cache_directories(self, domain_name: str) -> None:
        """确保缓存目录结构存在"""
        # 确保命令映射目录存在
        cmd_mappings_dir = self._cache_dir / "cmd_mappings" / domain_name
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保领域缓存目录存在
        domain_cache_dir = self._cache_dir / "domains" / f"{domain_name}.domain"
        domain_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_package_dir(self) -> Path:
        """
        获取包目录路径
        
        Returns:
            Path: 包目录路径
        """
        return Path(__file__).parent.parent.parent
    
    def get_default_configs_dir(self) -> Path:
        """
        获取包内默认配置目录路径
        
        Returns:
            Path: 默认配置目录路径
        """
        return self.get_package_dir() / "configs"
    
    def get_global_config_path(self) -> Path:
        """获取全局配置文件路径"""
        return self._config_dir / "config.toml"
    
    def get_program_parser_path_of_config(self, program_name: str) -> Path:
        """获取程序解析器配置文件路径"""
        return self._config_path_mgr.get_program_parser_path(program_name)
    
    def get_domain_base_path_of_config(self, domain_name: str) -> Path:
        """获取领域基础配置文件路径"""
        return self._config_path_mgr.get_domain_base_path(domain_name)
    
    def get_operation_domain_dir_of_config(self, domain_name: str) -> Path:
        """获取特定操作组的配置文件路径"""
        return self._config_path_mgr.get_operation_domain_dir(domain_name)
        
    def get_operation_group_path_of_config(self, domain_name: str, group_name: str) -> Path:
        """获取特定操作组的配置文件路径"""
        return self._config_path_mgr.get_operation_group_path(domain_name, group_name)
    
    def get_parser_config_dir_of_cache(self) -> Path:
        """获取解析器配置缓存目录"""
        return self._cache_path_mgr.get_parser_config_dir()
    
    def get_parser_config_path_of_cache(self, program_name: str) -> Path:
        """获取指定程序的解析器配置缓存文件路径"""
        return self._cache_path_mgr.get_parser_config_path(program_name)
    
    def get_operation_mappings_domain_dir_of_cache(self, domain_name: str) -> Path:
        """获取操作映射缓存文件路径"""
        return self._cache_path_mgr.get_operation_mappings_domain_dir(domain_name)
    
    def get_cmd_mappings_domain_dir_of_cache(self, domain_name: str) -> Path:
        """获取命令映射领域目录路径"""
        return self._cache_path_mgr.get_cmd_mappings_domain_dir(domain_name)
    
    def get_cmd_mappings_domain_of_cache(self, domain_name: str) -> Path:
        """获取命令映射缓存文件路径"""
        return self._cache_path_mgr.get_cmd_mappings_domain_dir(domain_name)
    
    def get_operation_to_program_path(self, domain_name: str) -> Path:
        """获取操作到程序映射文件路径"""
        return self._cache_path_mgr.get_operation_to_program_path(domain_name)
    
    def get_operation_mappings_group_dir_of_cache(self, domain_name: str, group_name: str) -> Path:
        """获取操作映射组目录路径"""
        return self._cache_path_mgr.get_operation_mappings_group_dir(domain_name, group_name)
    
    def get_operation_mappings_group_program_path_of_cache(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """获取操作映射组中特定程序的命令文件路径"""
        return self._cache_path_mgr.get_operation_mappings_group_program_path(domain_name, group_name, program_name)
    
    def get_cmd_mappings_group_dir_of_cache(self, domain_name: str, group_name: str) -> Path:
        """获取命令映射组目录路径"""
        return self._cache_path_mgr.get_cmd_mappings_group_dir(domain_name, group_name)
    
    def get_cmd_mappings_group_program_path_of_cache(self, domain_name: str, group_name: str, program_name: str) -> Path:
        """获取命令映射组中特定程序的命令文件路径"""
        return self._cache_path_mgr.get_cmd_mappings_group_program_path(domain_name, group_name, program_name)
    
    def get_cmd_to_operation_path(self, domain_name: str) -> Path:
        """获取命令到操作映射文件路径"""
        return self._cache_path_mgr.get_cmd_to_operation_path(domain_name)
    
    def ensure_cmd_mappings_group_dir(self, domain_name: str, group_name: str) -> None:
        """确保命令映射组目录存在"""
        group_dir = self.get_cmd_mappings_group_dir_of_cache(domain_name, group_name)
        group_dir.mkdir(parents=True, exist_ok=True)

    def ensure_operation_mappings_group_dir(self, domain_name: str, group_name: str) -> None:
        """确保操作映射组目录存在"""
        group_dir = self.get_operation_mappings_group_dir_of_cache(domain_name, group_name)
        group_dir.mkdir(parents=True, exist_ok=True)

    def ensure_cmd_mappings_domain_dir(self, domain_name: str) -> None:
        """确保命令映射领域目录存在"""
        cmd_mappings_dir = self.get_cmd_mappings_domain_dir_of_cache(domain_name)
        cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
    
    def domain_exists(self, domain_name: str) -> bool:
        """检查领域是否存在"""
        domain_path = self.get_operation_domain_dir_of_config(domain_name)
        return domain_path.exists() and domain_path.is_dir()
    
    def operation_group_exists(self, domain_name: str, group_name: str) -> bool:
        """检查操作组是否存在"""
        config_path = self.get_operation_group_path_of_config(domain_name, group_name)
        return config_path.exists()
    
    def program_parser_config_exists(self, program_name: str) -> bool:
        """检查程序解析器配置是否存在"""
        config_path = self.get_program_parser_path_of_config(program_name)
        return config_path.exists()
    
    def domain_base_config_exists(self, domain_name: str) -> bool:
        """检查领域基础配置文件是否存在"""
        return self.get_domain_base_path_of_config(domain_name).exists()

    def rm_cmd_mappings_dir(self, domain_name: Optional[str] = None) -> bool:
        """删除命令映射目录"""
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
                domain_cmd_mappings_dir = self.get_cmd_mappings_domain_dir_of_cache(domain_name)
                if domain_cmd_mappings_dir.exists():
                    shutil.rmtree(domain_cmd_mappings_dir)
                    debug(f"已删除 {domain_name} 领域的命令映射目录: {domain_cmd_mappings_dir}")
                return True
        except Exception as e:
            error(f"删除命令映射目录失败: {e}")
            return False

    def get_domains_from_config(self) -> List[str]:
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
    
    def get_operation_groups_from_config(self, domain_name: str) -> List[str]:
        """
        列出指定领域中的所有操作组名称
        
        Args:
            domain_name: 领域名称
            
        Returns:
            List[str]: 操作组名称列表，如 ["apt", "pacman", "brew"]
        """
        groups = []
        domain_dir = self.get_operation_domain_dir_of_config(domain_name)
        
        if not domain_dir.exists():
            return groups
        
        # 查找所有 .toml 配置文件（排除 base.toml）
        for config_file in domain_dir.glob("*.toml"):
            group_name = config_file.stem
            groups.append(group_name)
        
        return sorted(groups)
    
    def get_all_operation_groups_from_config(self) -> List[str]:
        """
        列出所有领域中的所有操作组名称
        
        Returns:
            List[str]: 所有操作组名称列表
        """
        all_groups = []
        domains = self.get_domains_from_config()
        
        for domain in domains:
            domain_groups = self.get_operation_groups_from_config(domain)
            all_groups.extend(domain_groups)
        
        return sorted(list(set(all_groups)))  # 去重并排序
    
    def get_programs_from_parser_configs(self) -> List[str]:
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
    
    def get_domain_for_group(self, group_name: str) -> Optional[str]:
        """根据程序组名称获取所属领域"""
        try:
            domains = self.get_domains_from_config()
            
            for domain in domains:
                groups = self.get_operation_groups_from_config(domain)
                if group_name in groups:
                    return domain
            return None
        except Exception:
            return None