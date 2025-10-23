# cmdbridge/cli.py

import click
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from log import set_level, LogLevel
import tomli

# 根据您的项目结构修正导入
from utils.config import ConfigUtils
from .config.cmd_mapping_creator import CmdMappingCreator
from .core.cmd_mapping import CmdMapping  # 根据您的文件，应该是 cmd_mapping.py
from .core.operation_mapping import OperationMapping


class CmdBridgeCLI:
    """cmdbridge 命令行接口"""
    
    def __init__(self):
        # 设置默认路径
        self.config_dir = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        ) / "cmdbridge"
        
        self.cache_dir = Path(
            os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        ) / "cmdbridge"
        
        # 获取包内默认配置路径
        self.package_dir = Path(__file__).parent.parent
        self.default_configs_dir = self.package_dir / "configs"
        
        # 初始化配置工具
        self.config_utils = ConfigUtils(
            configs_dir=self.config_dir,
            cache_dir=self.cache_dir
        )
        
        # 初始化命令映射器
        self.command_mapper = CmdMapping({})  # 初始化为空配置
        
        # 初始化操作映射器
        self.operation_mapper = OperationMapping(
            configs_dir=str(self.config_dir),
            cache_dir=str(self.cache_dir)  # 添加缓存目录参数
        )
        
        
        # 初始化映射创建器
        self.mapping_creator = CmdMappingCreator(
            domain_dir=str(self.config_dir),
            parser_configs_dir=str(self.config_dir / "program_parser_configs")
        )
        
        # 初始化映射配置缓存
        self._mapping_config_cache = {}
        
        # 加载全局配置
        self.global_config = self._load_global_config()

    def _get_mapping_config(self, domain: str) -> Dict[str, Any]:
        """获取指定领域的映射配置"""
        if domain not in self._mapping_config_cache:
            # 从缓存文件加载该领域的映射配置
            cache_file = self.cache_dir / "cmd_mappings" / domain / "cmd_mappings.toml"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        self._mapping_config_cache[domain] = tomli.load(f)
                except Exception as e:
                    click.echo(f"警告: 加载 {domain} 映射配置失败: {e}", err=True)
                    self._mapping_config_cache[domain] = {}
            else:
                self._mapping_config_cache[domain] = {}
        
        return self._mapping_config_cache[domain]

    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令"""
        try:
            # 将参数列表合并为命令字符串
            command_str = ' '.join(command_args)
            if not command_str:
                click.echo("错误: 必须提供要映射的命令", err=True)
                return False
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 自动识别源组（如果未指定）
            if not src_group:
                src_group = self._auto_detect_source_group(command_str, domain)
                if not src_group:
                    click.echo(f"错误: 无法自动识别命令 '{command_str}' 的源组，请使用 -s/--source-group 手动指定", err=True)
                    return False
            
            # 获取该领域的映射配置
            mapping_config = self._get_mapping_config(domain)
            
            # 创建命令映射器实例
            command_mapper = CmdMapping(mapping_config=mapping_config)
            
            # 调用映射逻辑
            result = command_mapper.map_command(
                command_str=command_str,
                src_group=src_group,
                dest_group=dest_group
            )
            
            if result:
                click.echo(result)
                return True
            else:
                click.echo(f"错误: 无法映射命令 '{command_str}'", err=True)
                return False
            
        except Exception as e:
            click.echo(f"错误: 命令映射失败: {e}", err=True)
            return False

    def _load_global_config(self) -> dict:
        """加载全局配置"""
        config_file = self.config_dir / "config.toml"
        if config_file.exists():
            try:
                with open(config_file, 'rb') as f:
                    return tomli.load(f)
            except Exception as e:
                click.echo(f"警告: 无法读取全局配置文件: {e}", err=True)
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
        groups = self.config_utils.list_groups_in_domain(domain)
        
        # 检查是否有组名与命令前缀匹配
        for group in groups:
            if first_word == group:
                return group
        
        return None
    
    def _init_config(self) -> bool:
        """初始化用户配置"""
        try:
            # 检查默认配置是否存在
            if not self.default_configs_dir.exists():
                click.echo(f"错误: 默认配置目录不存在: {self.default_configs_dir}", err=True)
                return False
            
            # 创建用户配置目录
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            click.echo(f"初始化配置目录: {self.config_dir}")
            click.echo(f"初始化缓存目录: {self.cache_dir}")
            
            # 复制 domain 配置
            domain_dirs = list(self.default_configs_dir.glob("*.domain"))
            if domain_dirs:
                click.echo("复制领域配置...")
                for domain_dir in domain_dirs:
                    dest_domain_dir = self.config_dir / domain_dir.name
                    if dest_domain_dir.exists():
                        click.echo(f"  跳过已存在的: {domain_dir.name}")
                    else:
                        shutil.copytree(domain_dir, dest_domain_dir)
                        click.echo(f"  已复制: {domain_dir.name}")
            
            # 复制 program_parser_configs
            parser_configs_dir = self.default_configs_dir / "program_parser_configs"
            if parser_configs_dir.exists():
                dest_parser_dir = self.config_dir / "program_parser_configs"
                if dest_parser_dir.exists():
                    click.echo("  跳过已存在的: program_parser_configs")
                else:
                    shutil.copytree(parser_configs_dir, dest_parser_dir)
                    click.echo("  已复制: program_parser_configs")
            
            # 复制 config.toml
            default_config_file = self.default_configs_dir / "config.toml"
            if default_config_file.exists():
                dest_config_file = self.config_dir / "config.toml"
                if not dest_config_file.exists():
                    shutil.copy2(default_config_file, dest_config_file)
                    click.echo("  已复制: config.toml")
                else:
                    click.echo("  跳过已存在的: config.toml")
            else:
                # 创建默认的 config.toml
                default_config = """[global_settings]
default_operation_domain = "package"
default_operation_group = "pacman"
"""
                dest_config_file = self.config_dir / "config.toml"
                if not dest_config_file.exists():
                    with open(dest_config_file, 'w') as f:
                        f.write(default_config)
                    click.echo("  已创建默认: config.toml")
            
            # 刷新缓存
            click.echo("刷新命令映射缓存...")
            refresh_success = self._refresh_cmd_mappings()
            
            if refresh_success:
                click.echo("✅ 配置初始化完成！")
                click.echo(f"   配置目录: {self.config_dir}")
                click.echo(f"   缓存目录: {self.cache_dir}")
                return True
            else:
                click.echo("❌ 配置初始化完成，但刷新缓存失败", err=True)
                return False
                
        except Exception as e:
            click.echo(f"错误: 初始化配置失败: {e}", err=True)
            return False
    
    def _refresh_cmd_mappings(self) -> bool:
        """刷新所有命令映射缓存"""
        try:
            success = self.config_utils.refresh_cmd_mapping()
            if success:
                # 先合并所有领域配置到缓存目录
                click.echo("合并领域配置到缓存...")
                merge_success = self.config_utils.merge_all_domain_configs()
                if not merge_success:
                    click.echo("警告: 合并领域配置失败")
                
                # 创建缓存目录结构
                cmd_mappings_dir = self.cache_dir / "cmd_mappings"
                cmd_mappings_dir.mkdir(parents=True, exist_ok=True)
                
                # 为每个领域生成映射数据
                domains = self.config_utils.list_domains()
                for domain in domains:
                    domain_dir = cmd_mappings_dir / domain
                    domain_dir.mkdir(exist_ok=True)
                    
                    # 构建领域目录路径
                    domain_config_dir = self.config_dir / f"{domain}.domain"
                    parser_configs_dir = self.config_dir / "program_parser_configs"
                    
                    if domain_config_dir.exists() and parser_configs_dir.exists():
                        # 为每个领域创建新的 CmdMappingCreator 实例
                        domain_creator = CmdMappingCreator(
                            domain_dir=str(domain_config_dir),
                            parser_configs_dir=str(parser_configs_dir)
                        )
                        
                        # 生成映射数据
                        mapping_data = domain_creator.create_mappings()
                        
                        # 写入映射文件
                        mapping_file = domain_dir / "cmd_mappings.toml"
                        domain_creator.write_to(str(mapping_file))
                        
                        click.echo(f"✅ 已生成 {domain} 领域的命令映射")
                    else:
                        click.echo(f"⚠️  跳过 {domain} 领域：配置目录不存在")
                
                return True
            return False
        except Exception as e:
            click.echo(f"错误: 刷新命令映射失败: {e}", err=True)
            return False
        
    def map_command(self, domain: Optional[str], src_group: Optional[str], 
                   dest_group: Optional[str], command_args: List[str]) -> bool:
        """映射完整命令 - 调用 core 中的实现"""
        try:
            # 将参数列表合并为命令字符串
            command_str = ' '.join(command_args)
            if not command_str:
                click.echo("错误: 必须提供要映射的命令", err=True)
                return False
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 自动识别源组（如果未指定）
            if not src_group:
                src_group = self._auto_detect_source_group(command_str, domain)
                if not src_group:
                    click.echo(f"错误: 无法自动识别命令 '{command_str}' 的源组，请使用 -s/--source-group 手动指定", err=True)
                    return False
            
            # 调用 core 中的 map_command 实现
            result = self.command_mapper.map_command(
                domain=domain,
                src_group=src_group,
                dest_group=dest_group,
                command_str=command_str
            )
            
            if result:
                click.echo(result)
                return True
            else:
                click.echo(f"错误: 无法映射命令 '{command_str}'", err=True)
                return False
            
        except Exception as e:
            click.echo(f"错误: 命令映射失败: {e}", err=True)
            return False
    
    def map_operation(self, domain: Optional[str], dest_group: Optional[str], 
                    operation_args: List[str]) -> bool:
        """映射操作和参数 - 调用 core 中的实现"""
        try:
            # 将参数列表合并为操作字符串
            operation_str = ' '.join(operation_args)
            if not operation_str:
                click.echo("错误: 必须提供要映射的操作", err=True)
                return False
            
            # 设置默认值
            domain = domain or self._get_default_domain()
            dest_group = dest_group or self._get_default_group()
            
            # 调试信息
            click.echo(f"🔧 调试: 映射操作 domain={domain}, dest_group={dest_group}, operation='{operation_str}'")
            
            # 解析操作字符串，提取操作名和参数
            parts = operation_str.split()
            if not parts:
                click.echo("错误: 操作字符串为空", err=True)
                return False
            
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
            
            if result:
                click.echo(result)
                return True
            else:
                click.echo(f"错误: 无法映射操作 '{operation_str}'", err=True)
                return False
                
        except Exception as e:
            click.echo(f"错误: 操作映射失败: {e}", err=True)
            import traceback
            traceback.print_exc()  # 打印完整堆栈跟踪
            return False


class CustomCommand(click.Command):
    """自定义命令类，支持 -- 分隔符"""
    
    def parse_args(self, ctx, args):
        """解析参数，处理 -- 分隔符"""
        if '--' in args:
            idx = args.index('--')
            # 使用 ctx.meta 来存储保护参数
            ctx.meta['protected_args'] = args[idx+1:]
            args = args[:idx]
        
        return super().parse_args(ctx, args)


# Click 命令行接口
@click.group()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, debug):
    """cmdbridge: 输出映射后的命令"""
    # 设置日志级别
    if debug:
        set_level(LogLevel.DEBUG)
        click.echo("🔧 调试模式已启用")
    ctx.obj = CmdBridgeCLI()


@cli.group()
def config():
    """配置管理命令"""
    pass


@cli.group()
def cache():
    """缓存管理命令"""
    pass


@config.command()
@click.pass_obj
def init(cli_obj):
    """初始化用户配置目录"""
    success = cli_obj._init_config()
    sys.exit(0 if success else 1)


@cache.command()
@click.pass_obj
def refresh(cli_obj):
    """刷新命令映射缓存"""
    success = cli_obj._refresh_cmd_mappings()
    if success:
        click.echo("命令映射缓存已刷新")
    else:
        click.echo("错误: 刷新命令映射缓存失败", err=True)
    sys.exit(0 if success else 1)


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-s', '--source-group', help='源程序组（只有无法识别才需要使用）')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def map(ctx, domain, source_group, dest_group):
    """映射完整命令
    
    使用 -- 分隔符将命令参数与 cmdbridge 选项分开：
    cmdbridge map -t apt -- pacman -S vim
    """
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    command_args = ctx.meta.get('protected_args', [])
    if not command_args:
        click.echo("错误: 必须提供要映射的命令，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_command(domain, source_group, dest_group, command_args)
    sys.exit(0 if success else 1)


@cli.command(cls=CustomCommand)
@click.option('-d', '--domain', help='领域名称')
@click.option('-t', '--dest-group', help='目标程序组')
@click.pass_context
def op(ctx, domain, dest_group):
    """映射操作和参数
    
    使用 -- 分隔符将操作参数与 cmdbridge 选项分开：
    cmdbridge op -t apt -- install vim
    """
    cli_obj = ctx.obj
    
    # 获取 -- 后面的参数（从 ctx.meta 中获取）
    operation_args = ctx.meta.get('protected_args', [])
    if not operation_args:
        click.echo("错误: 必须提供要映射的操作，使用 -- 分隔", err=True)
        sys.exit(1)
    
    success = cli_obj.map_operation(domain, dest_group, operation_args)
    sys.exit(0 if success else 1)


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()