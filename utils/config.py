# utils/config.py

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import tomli
import shutil


class ConfigUtils:
    """配置工具类 - 管理配置和缓存目录，包含所有功能实现"""
    
    def __init__(self, configs_dir: str = "configs", cache_dir: str = "output"):
        """
        初始化配置工具
        
        Args:
            configs_dir: 配置目录路径
            cache_dir: 缓存目录路径
        """
        self.configs_dir = Path(configs_dir)
        self.cache_dir = Path(cache_dir)
        self.cmd_mappings_cache_dir = self.cache_dir / "cmd_mappings"
    
    def refresh_cmd_mapping(self, domain_name: str = None) -> bool:
        """
        刷新命令映射缓存
        
        删除指定领域的缓存文件，然后重新生成
        
        Args:
            domain_name: 领域名称，如果为 None 则刷新所有领域
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if domain_name is None:
                # 刷新所有领域
                if self.cmd_mappings_cache_dir.exists():
                    shutil.rmtree(self.cmd_mappings_cache_dir)
                    self.cmd_mappings_cache_dir.mkdir(parents=True, exist_ok=True)
            else:
                # 刷新指定领域
                domain_cache_dir = self.cmd_mappings_cache_dir / domain_name
                if domain_cache_dir.exists():
                    shutil.rmtree(domain_cache_dir)
                    domain_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 重新生成命令映射
            # 这里需要调用 cmd_mapping_creator 的功能
            # 由于 cmd_mapping_creator 的具体实现不在当前文件中，
            # 这里返回 True 表示删除操作成功，生成操作由外部调用
            return True
            
        except Exception as e:
            print(f"刷新命令映射失败: {e}")
            return False
    
    def list_domains(self) -> List[str]:
        """
        列出所有可用的领域名称 (domains)
        
        Returns:
            List[str]: 领域名称列表，如 ["package", "process"]
        """
        domains = []
        
        if not self.configs_dir.exists():
            return domains
        
        # 查找所有 *.domain 目录
        for item in self.configs_dir.iterdir():
            if item.is_dir() and item.name.endswith('.domain'):
                domain_name = item.name[:-7]  # 移除 .domain 后缀
                domains.append(domain_name)
        
        return sorted(domains)
    
    def list_groups_in_domain(self, domain_name: str) -> List[str]:
        """
        列出指定领域中的所有程序组名称 (groups)
        
        Args:
            domain_name: 领域名称
            
        Returns:
            List[str]: 程序组名称列表，如 ["apt", "pacman", "brew"]
        """
        groups = []
        domain_dir = self.configs_dir / f"{domain_name}.domain"
        
        if not domain_dir.exists():
            return groups
        
        # 查找所有 .toml 配置文件
        for config_file in domain_dir.glob("*.toml"):
            group_name = config_file.stem
            groups.append(group_name)
        
        return sorted(groups)
    
    def _get_commands_from_cache(self, domain: str, group: str = None) -> List[str]:
        """从缓存获取命令"""
        cmds = []
        if self.cmd_mappings_cache_dir.exists():
            domain_cache_dir = self.cmd_mappings_cache_dir / domain
            mappings_file = domain_cache_dir / "cmd_mappings.toml"
            
            if mappings_file.exists():
                try:
                    with open(mappings_file, 'rb') as f:
                        mappings_data = tomli.load(f)
                    
                    if group is None:
                        # 获取所有组的命令
                        for grp in mappings_data.keys():
                            command_mappings = mappings_data[grp].get("command_mappings", [])
                            for mapping in command_mappings:
                                if "operation" in mapping:
                                    cmds.append(mapping["operation"])
                    else:
                        # 获取指定组的命令
                        if group in mappings_data:
                            command_mappings = mappings_data[group].get("command_mappings", [])
                            for mapping in command_mappings:
                                if "operation" in mapping:
                                    cmds.append(mapping["operation"])
                                
                except Exception:
                    pass
        return cmds
    
    def _get_commands_from_config(self, domain: str, group: str = None) -> List[str]:
        """从配置文件获取命令"""
        cmds = []
        if group is None:
            # 获取所有组的命令
            domain_dir = self.configs_dir / f"{domain}.domain"
            if domain_dir.exists():
                for config_file in domain_dir.glob("*.toml"):
                    try:
                        with open(config_file, 'rb') as f:
                            config_data = tomli.load(f)
                        
                        if 'operations' in config_data:
                            for operation_key in config_data['operations'].keys():
                                if '.' in operation_key:
                                    cmd_name, cmd_group = operation_key.split('.')
                                    cmds.append(cmd_name)
                                else:
                                    cmds.append(operation_key)
                                    
                    except Exception:
                        continue
        else:
            # 获取指定组的命令
            config_file = self.configs_dir / f"{domain}.domain" / f"{group}.toml"
            if config_file.exists():
                try:
                    with open(config_file, 'rb') as f:
                        config_data = tomli.load(f)
                    
                    if 'operations' in config_data:
                        for operation_key in config_data['operations'].keys():
                            if '.' in operation_key:
                                cmd_name, cmd_group = operation_key.split('.')
                                if cmd_group == group:
                                    cmds.append(cmd_name)
                            else:
                                cmds.append(operation_key)
                                
                except Exception:
                    pass
        return cmds
    
    def list_commands_in_domain_group(self, domain_name: str, group_name: str = None) -> List[str]:
        """
        列出指定领域和程序组中的所有命令名称
        
        如果 group_name 为 None，则列出整个 domain 下的所有命令
        
        Args:
            domain_name: 领域名称
            group_name: 程序组名称 (可选)
            
        Returns:
            List[str]: 命令名称列表
        """
        commands = []
        
        # 优先从缓存获取
        commands = self._get_commands_from_cache(domain_name, group_name)
        
        # 如果缓存中没有找到，回退到配置文件
        if not commands:
            commands = self._get_commands_from_config(domain_name, group_name)
        
        # 去重并排序
        return sorted(list(set(commands)))
    
    def merge_all_domain_configs(self) -> bool:
        """
        合并所有领域的配置并保存到缓存目录
        
        Returns:
            bool: 操作是否成功
        """
        try:
            domains = self.list_domains()
            for domain in domains:
                # 创建领域缓存目录
                domain_cache_dir = self.cache_dir / "domains" / f"{domain}.domain"
                domain_cache_dir.mkdir(parents=True, exist_ok=True)
                
                # 获取该领域的所有程序组
                groups = self.list_groups_in_domain(domain)
                
                for group in groups:
                    # 为每个程序组合并配置
                    merged_config = self._merge_domain_group_config(domain, group)
                    if merged_config:
                        # 保存合并后的配置到缓存文件
                        cache_file = domain_cache_dir / f"{group}.toml"
                        with open(cache_file, 'wb') as f:
                            tomli_w = __import__('tomli_w')
                            tomli_w.dump({"operations": merged_config}, f)
                        print(f"✅ 已合并 {domain}.{group} 配置到缓存")
                    else:
                        print(f"⚠️  跳过 {domain}.{group}：无配置可合并")
            
            return True
            
        except Exception as e:
            print(f"合并领域配置失败: {e}")
            return False

    def _merge_domain_group_config(self, domain_name: str, program_name: str) -> Dict[str, Dict[str, Any]]:
        """
        合并指定领域和程序组的配置
        
        Args:
            domain_name: 领域名称
            program_name: 程序名称
            
        Returns:
            Dict[str, Dict[str, Any]]: 合并后的操作配置字典
        """
        merged_operations = {}
        
        try:
            domain_dir = self.configs_dir / f"{domain_name}.domain"
            base_config_file = domain_dir / "base.toml"
            program_config_file = domain_dir / f"{program_name}.toml"
            
            # 加载基础配置中的所有操作
            base_operations = {}
            if base_config_file.exists():
                with open(base_config_file, 'rb') as f:
                    base_config_data = tomli.load(f)
                base_operations = base_config_data.get("operations", {})
            
            # 加载程序特定配置
            program_operations = {}
            if program_config_file.exists():
                with open(program_config_file, 'rb') as f:
                    program_config_data = tomli.load(f)
                program_operations = program_config_data.get("operations", {})
            
            # 合并配置
            for op_key, op_config in base_operations.items():
                # 基础配置中的操作（如 "install_remote"）
                if '.' not in op_key:  # 只处理不包含程序名的操作键
                    merged_operations[op_key] = op_config.copy()
            
            for op_key, op_config in program_operations.items():
                # 程序特定配置中的操作
                if '.' in op_key and op_key.endswith(f".{program_name}"):
                    # 格式: "install_remote.apt" -> 提取操作名 "install_remote"
                    op_name = op_key.split('.')[0]
                    if op_name in merged_operations:
                        # 合并配置，程序特定配置优先
                        merged_operations[op_name].update(op_config)
                    else:
                        merged_operations[op_name] = op_config.copy()
                elif '.' not in op_key:
                    # 直接使用操作名
                    merged_operations[op_key] = op_config.copy()
            
            return merged_operations
            
        except Exception as e:
            print(f"合并 {domain_name}.{program_name} 配置失败: {e}")
            return {}

    def get_merged_operation_config(self, domain_name: str, program_name: str, operation_name: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取合并的操作配置
        
        Args:
            domain_name: 领域名称
            program_name: 程序名称
            operation_name: 操作名称
            
        Returns:
            Optional[Dict[str, Any]]: 合并后的操作配置
        """
        try:
            # 首先尝试从缓存加载
            cache_file = self.cache_dir / "domains" / f"{domain_name}.domain" / f"{program_name}.toml"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = tomli.load(f)
                return cached_data.get("operations", {}).get(operation_name)
            
            # 如果缓存不存在，实时合并
            return self._merge_domain_group_config(domain_name, program_name).get(operation_name)
            
        except Exception as e:
            print(f"获取合并操作配置失败: {e}")
            return None