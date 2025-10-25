# cmdbridge/cmdbridge.py

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import tomli

from .config.path_manager import PathManager
from cmdbridge.config.config_mgr import ConfigMgr
from .config.cmd_mapping_mgr import CmdMappingMgr
from .core.cmd_mapping import CmdMapping
from .core.operation_mapping import OperationMapping
from log import debug, info, warning, error


class CmdBridge:
    """CmdBridge 核心功能类"""
    
    def __init__(self):
        # 初始化路径管理器
        self.path_manager = PathManager()
        
        # 初始化配置工具
        self.config_mgr = ConfigMgr()

        # 初始化命令映射器
        self.command_mapper = CmdMapping({})
        
        # 初始化操作映射器 - 简化构造函数
        self.operation_mapper = OperationMapping()
        
        # 初始化映射配置缓存
        self._mapping_config_cache = {}
        
        # 加载全局配置
        self.global_config = self._load_global_config()

    def _load_global_config(self) -> dict:
        """加载全局配置"""
        config_file = self.path_manager.get_global_config_path()
        if config_file.exists():
            try:
                with open(config_file, 'rb') as f:
                    return tomli.load(f)
            except Exception as e:
                warning(f"无法读取全局配置文件: {e}")
        return {}

    def _get_default_domain(self) -> str:
        """获取默认领域"""
        return self.global_config.get('global_settings', {}).get('default_operation_domain', 'package')
    
    def _get_default_group(self) -> str:
        """获取默认程序组"""
        return self.global_config.get('global_settings', {}).get('default_operation_group', 'pacman')
    
    def _auto_detect_source_group(self, command: str, domain: str) -> Optional[str]:
        """自动识别源命令所属的组"""
        if not command.strip():
            return None
        
        # 获取命令的第一个单词
        first_word = command.strip().split()[0]
        
        # 列出该领域的所有组
        groups = self.path_manager.list_operation_groups(domain)
        
        # 检查是否有组名与命令前缀匹配
        for group in groups:
            if first_word == group:
                return group
        
        return None

    def _get_mapping_config(self, domain: str, group_name: str) -> Dict[str, Any]:
        """获取指定领域和程序组的映射配置"""
        cache_key = f"{domain}.{group_name}"
        if cache_key not in self._mapping_config_cache:
            # 从缓存文件加载该程序组的映射配置
            cache_file = self.path_manager.get_cmd_mappings_domain_dir(domain) / f"{group_name}.toml"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._mapping_config_cache[cache_key] = tomli.load(f)
                except Exception as e:
                    warning(f"加载 {cache_key} 映射配置失败: {e}")
                    self._mapping_config_cache[cache_key] = {}
            else:
                self._mapping_config_cache[cache_key] = {}
        
        return self._mapping_config_cache[cache_key]

    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                dest_group: Optional[str], command_args: List[str]) -> Optional[str]:
        """映射完整命令"""
        try:
            # 将参数列表合并为命令字符串
            command_str = ' '.join(command_args)
            if not command_str:
                return None
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 自动识别源组（如果未指定）
            if not src_group:
                src_group = self._auto_detect_source_group(command_str, domain)
                if not src_group:
                    return None
            
            # 动态加载映射配置
            mapping_config = self._get_mapping_config(domain, src_group)
            
            # 重新初始化命令映射器
            self.command_mapper = CmdMapping(mapping_config)
            
            # 加载源程序的解析器配置
            parser_config_file = self.path_manager.get_program_parser_config_path(src_group)
            if not parser_config_file.exists():
                error(f"找不到 {src_group} 的解析器配置")
                return None
            
            from parsers.config_loader import load_parser_config_from_file
            source_parser_config = load_parser_config_from_file(str(parser_config_file), src_group)
            
            # 使用正确的 map_to_operation 方法
            operation_result = self.command_mapper.map_to_operation(
                source_cmdline=command_args,  # 直接使用参数列表
                source_parser_config=source_parser_config,
                dst_operation_group=dest_group
            )
            
            if not operation_result:
                return None
            
            # 使用 OperationMapping 生成最终命令
            result_cmd = self.operation_mapper.generate_command(
                operation_name=operation_result["operation_name"],
                params=operation_result["params"],
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group,
            )
            
            return result_cmd
            
        except Exception as e:
            error(f"命令映射失败: {e}")
            return None

    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> Optional[str]:
        """映射操作和参数"""
        try:
            # 将参数列表合并为操作字符串
            operation_str = ' '.join(operation_args)
            if not operation_str:
                return None
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 解析操作字符串，提取操作名和参数
            parts = operation_str.split()
            if not parts:
                return None
            
            # 第一个参数是操作名，其余是包名
            operation_name = parts[0]
            params = {}
            
            # 简单参数解析：假设后续参数都是包名
            if len(parts) > 1:
                params = {"pkgs": " ".join(parts[1:])}
            
            # 调用 OperationMapping 生成命令
            result = self.operation_mapper.generate_command(
                operation_name=operation_name,
                params=params,
                dst_operation_domain_name=domain,
                dst_operation_group_name=dest_group
            )
            
            return result
                
        except Exception as e:
            error(f"操作映射失败: {e}")
            return None

    def refresh_cmd_mappings(self) -> bool:
        """刷新所有命令映射缓存"""
        try:
            success = self.config_mgr.remove_cmd_mapping()
            if success:
                # 先合并所有领域配置到缓存目录
                info("合并领域配置到缓存...")
                merge_success = self.config_mgr.merge_all_domain_configs()
                if not merge_success:
                    warning("合并领域配置失败")
                
                # 为每个领域生成映射数据
                domains = self.path_manager.list_domains()
                for domain in domains:
                    # 确保缓存目录存在
                    self.path_manager.get_cmd_mappings_cache_path(domain).mkdir(parents=True, exist_ok=True)
                    self.path_manager.get_operation_mappings_cache_path(domain).mkdir(parents=True, exist_ok=True)
                    
                    # 获取领域配置目录
                    domain_config_dir = self.path_manager.get_config_operation_group_path(domain)
                    parser_configs_dir = self.path_manager.program_parser_config_dir
                    
                    if domain_config_dir.exists() and parser_configs_dir.exists():
                        # 获取该领域的所有程序组
                        groups = self.path_manager.list_operation_groups(domain)
                        
                        for group_name in groups:
                            try:
                                # 为每个程序组创建 CmdMappingCreator 实例
                                group_creator = CmdMappingMgr(domain, group_name)
                                
                                # 生成映射数据
                                mapping_data = group_creator.create_mappings()
                                
                                if mapping_data:  # 如果有映射数据才写入
                                    # 写入映射文件
                                    group_creator.write_to()
                                    info(f"✅ 已生成 {domain}.{group_name} 的命令映射")
                                else:
                                    warning(f"⚠️ {domain}.{group_name} 没有生成映射数据")
                                    
                            except Exception as e:
                                error(f"❌ 生成 {domain}.{group_name} 的命令映射失败: {e}")
                                continue
                        
                        # 使用 OperationMappingCreator 生成操作映射文件
                        from .config.operation_mapping_mgr import create_operation_mappings_for_domain
                        op_mapping_success = create_operation_mappings_for_domain(domain)
                        if op_mapping_success:
                            info(f"✅ 已完成 {domain} 领域的操作映射生成")
                        else:
                            warning(f"⚠️ {domain} 领域的操作映射生成失败")
                        
                        info(f"✅ 已完成 {domain} 领域所有程序组的命令映射生成")
                    else:
                        warning(f"⚠️  跳过 {domain} 领域：配置目录不存在")
                
                return True
            return False
        except Exception as e:
            error(f"刷新命令映射失败: {e}")
            return False

    def init_config(self) -> bool:
        """初始化用户配置"""
        try:
            # 获取包内默认配置路径
            package_dir = Path(__file__).parent.parent
            default_configs_dir = package_dir / "configs"
            
            # 检查默认配置是否存在
            if not default_configs_dir.exists():
                error(f"默认配置目录不存在: {default_configs_dir}")
                return False
            
            info(f"初始化配置目录: {self.path_manager.config_dir}")
            info(f"初始化缓存目录: {self.path_manager.cache_dir}")
            
            # 复制领域基础文件
            base_files = list(default_configs_dir.glob("*.domain.base.toml"))
            if base_files:
                info("复制领域基础文件...")
                for base_file in base_files:
                    dest_file = self.path_manager.config_dir / base_file.name
                    if dest_file.exists():
                        info(f"  跳过已存在的: {base_file.name}")
                    else:
                        shutil.copy2(base_file, dest_file)
                        info(f"  已复制: {base_file.name}")
            else:
                warning("未找到任何领域基础文件")
            
            # 复制领域配置目录
            domain_dirs = list(default_configs_dir.glob("*.domain"))
            if domain_dirs:
                info("复制领域配置目录...")
                for domain_dir in domain_dirs:
                    # 检查是否是目录（排除 .domain.base.toml 文件）
                    if domain_dir.is_dir():
                        dest_domain_dir = self.path_manager.get_config_operation_group_path(domain_dir.stem)
                        if dest_domain_dir.exists():
                            info(f"  跳过已存在的: {domain_dir.name}")
                        else:
                            shutil.copytree(domain_dir, dest_domain_dir)
                            info(f"  已复制: {domain_dir.name}")
            else:
                warning("未找到任何领域配置目录")
            
            # 复制 program_parser_configs
            parser_configs_dir = default_configs_dir / "program_parser_configs"
            if parser_configs_dir.exists():
                dest_parser_dir = self.path_manager.program_parser_config_dir
                
                # 确保目标目录存在
                dest_parser_dir.mkdir(parents=True, exist_ok=True)
                
                info(f"复制解析器配置从 {parser_configs_dir} 到 {dest_parser_dir}")
                
                # 复制所有 .toml 文件
                config_files = list(parser_configs_dir.glob("*.toml"))
                if config_files:
                    copied_count = 0
                    for config_file in config_files:
                        dest_file = dest_parser_dir / config_file.name
                        if not dest_file.exists():
                            shutil.copy2(config_file, dest_file)
                            info(f"  已复制: {config_file.name}")
                            copied_count += 1
                        else:
                            info(f"  跳过已存在的: {config_file.name}")
                    
                    info(f"解析器配置复制完成: {copied_count} 个文件")
                else:
                    warning(f"源目录中没有找到任何 .toml 文件: {parser_configs_dir}")
            else:
                error(f"源解析器配置目录不存在: {parser_configs_dir}")
                return False
            
            # 复制 config.toml
            default_config_file = default_configs_dir / "config.toml"
            if default_config_file.exists():
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    shutil.copy2(default_config_file, dest_config_file)
                    info("  已复制: config.toml")
                else:
                    info("  跳过已存在的: config.toml")
            else:
                # 创建默认的 config.toml
                default_config = """[global_settings]
    default_operation_domain = "package"
    default_operation_group = "pacman"
    """
                dest_config_file = self.path_manager.get_global_config_path()
                if not dest_config_file.exists():
                    with open(dest_config_file, 'w') as f:
                        f.write(default_config)
                    info("  已创建默认: config.toml")
            
            return True
        except Exception as e:
            error(f"初始化配置失败: {e}")
            return False  