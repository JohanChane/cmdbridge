# test/test_parsers/conftest.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 这个文件可以为 test_parsers 目录提供特定的测试配置