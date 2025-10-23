# cmdbridge/cmdbridge.py

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import tomli

from .config.path_manager import PathManager
from utils.config import ConfigUtils
from .config.cmd_mapping_creator import CmdMappingCreator
from .core.cmd_mapping import CmdMapping
from .core.operation_mapping import OperationMapping
from log import debug, info, warning, error


class CmdBridge:
    """CmdBridge 核心功能类"""
    
    def __init__(self):
        # 初始化路径管理器
        self.path_manager = PathManager()
        
        # 初始化配置工具
        # self.config_utils = ConfigUtils(
        #     configs_dir=str(self.path_manager.config_dir),
        #     cache_dir=str(self.path_manager.cache_dir)
        # )
        self.config_utils = ConfigUtils()

        # 初始化命令映射器
        self.command_mapper = CmdMapping({})
        
        # 初始化操作映射器 - 简化构造函数
        self.operation_mapper = OperationMapping()
        
        # 初始化映射创建器
        self.mapping_creator = CmdMappingCreator(
            domain_dir=str(self.path_manager.config_dir),
            parser_configs_dir=str(self.path_manager.program_parser_config_dir)
        )
        
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

    def _get_mapping_config(self, domain: str) -> Dict[str, Any]:
        """获取指定领域的映射配置"""
        if domain not in self._mapping_config_cache:
            # 从缓存文件加载该领域的映射配置
            cache_file = self.path_manager.get_cmd_mappings_cache_path(domain)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._mapping_config_cache[domain] = tomli.load(f)
                except Exception as e:
                    warning(f"加载 {domain} 映射配置失败: {e}")
                    self._mapping_config_cache[domain] = {}
            else:
                self._mapping_config_cache[domain] = {}
        
        return self._mapping_config_cache[domain]

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
            mapping_config = self._get_mapping_config(domain)
            
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
                dst_operation_group_name=dest_group
            )
            
            return result_cmd
            
        except Exception as e:
            error(f"命令映射失败: {e}")
            return None

    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> Optional[str]:
        """映射操作和参数 - 调用 core 中的实现
        
        Args:
            domain: 领域名称
            dest_group: 目标程序组
            operation_args: 操作参数列表
            
        Returns:
            Optional[str]: 映射后的命令字符串，如果失败则返回 None
        """
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
        """刷新所有命令映射缓存
        
        Returns:
            bool: 刷新是否成功
        """
        try:
            success = self.config_utils.refresh_cmd_mapping()
            if success:
                # 先合并所有领域配置到缓存目录
                info("合并领域配置到缓存...")
                merge_success = self.config_utils.merge_all_domain_configs()
                if not merge_success:
                    warning("合并领域配置失败")
                
                # 为每个领域生成映射数据
                domains = self.path_manager.list_domains()
                for domain in domains:
                    # 确保缓存目录存在
                    self.path_manager.ensure_cmd_mappings_domain_dir(domain)
                    
                    # 构建领域目录路径
                    domain_config_dir = self.path_manager.get_config_operation_group_path(domain)
                    parser_configs_dir = self.path_manager.program_parser_config_dir
                    
                    if domain_config_dir.exists() and parser_configs_dir.exists():
                        # 为每个领域创建新的 CmdMappingCreator 实例
                        domain_creator = CmdMappingCreator(
                            domain_dir=str(domain_config_dir),
                            parser_configs_dir=str(parser_configs_dir)
                        )
                        
                        # 生成映射数据
                        mapping_data = domain_creator.create_mappings()
                        
                        # 写入映射文件
                        mapping_file = self.path_manager.get_cmd_mappings_cache_path(domain)
                        domain_creator.write_to(str(mapping_file))
                        
                        # 生成 operation_mapping.toml 文件
                        self._generate_operation_mapping_file(domain, domain_config_dir)
                        
                        info(f"✅ 已生成 {domain} 领域的命令映射")
                    else:
                        warning(f"⚠️  跳过 {domain} 领域：配置目录不存在")
                
                return True
            return False
        except Exception as e:
            error(f"刷新命令映射失败: {e}")
            return False

    def _generate_operation_mapping_file(self, domain: str, domain_config_dir: Path) -> bool:
        """为指定领域生成 operation_mapping.toml 文件
        
        Args:
            domain: 领域名称
            domain_config_dir: 领域配置目录路径
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 获取操作映射文件路径
            mapping_file = domain_config_dir / "operation_mapping.toml"
            
            # 收集所有操作组文件
            operation_groups = {}
            command_formats = {}
            
            # 遍历所有 .toml 配置文件（排除 base.toml）
            for config_file in domain_config_dir.glob("*.toml"):
                if config_file.stem == "base":
                    continue
                    
                program_name = config_file.stem
                debug(f"处理操作组文件: {config_file}")
                
                try:
                    with open(config_file, 'rb') as f:
                        group_data = tomli.load(f)
                    
                    # 收集操作到程序的映射
                    if "operations" in group_data:
                        for operation_key, operation_config in group_data["operations"].items():
                            # 从 operation_key 提取操作名（移除程序后缀）
                            operation_parts = operation_key.split('.')
                            if len(operation_parts) > 1 and operation_parts[-1] == program_name:
                                operation_name = '.'.join(operation_parts[:-1])
                            else:
                                operation_name = operation_key
                            
                            # 添加到操作到程序映射
                            if operation_name not in operation_groups:
                                operation_groups[operation_name] = []
                            
                            if program_name not in operation_groups[operation_name]:
                                operation_groups[operation_name].append(program_name)
                            
                            # 添加到命令格式映射
                            if program_name not in command_formats:
                                command_formats[program_name] = {}
                            
                            if "cmd_format" in operation_config:
                                command_formats[program_name][operation_name] = operation_config["cmd_format"]
                                
                except Exception as e:
                    warning(f"解析操作组文件 {config_file} 失败: {e}")
                    continue
            
            # 构建 operation_mapping 数据
            operation_mapping_data = {
                "operation_to_program": operation_groups,
                "command_formats": command_formats
            }
            
            # 写入文件
            with open(mapping_file, 'wb') as f:
                import tomli_w
                tomli_w.dump(operation_mapping_data, f)
            
            info(f"✅ 已生成 operation_mapping.toml 文件: {mapping_file}")
            return True
            
        except Exception as e:
            error(f"生成 operation_mapping.toml 文件失败: {e}")
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
            
            # 复制 domain 配置
            domain_dirs = list(default_configs_dir.glob("*.domain"))
            if domain_dirs:
                info("复制领域配置...")
                for domain_dir in domain_dirs:
                    dest_domain_dir = self.path_manager.get_config_operation_group_path(domain_dir.stem)
                    if dest_domain_dir.exists():
                        info(f"  跳过已存在的: {domain_dir.name}")
                    else:
                        shutil.copytree(domain_dir, dest_domain_dir)
                        info(f"  已复制: {domain_dir.name}")
            
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
            
            # 刷新缓存
            info("刷新命令映射缓存...")
            refresh_success = self.refresh_cmd_mappings()
            
            if refresh_success:
                info("✅ 配置初始化完成！")
                info(f"   配置目录: {self.path_manager.config_dir}")
                info(f"   缓存目录: self.path_manager.cache_dir")
                return True
            else:
                error("❌ 配置初始化完成，但刷新缓存失败")
                return False
                
        except Exception as e:
            error(f"初始化配置失败: {e}")
            return False