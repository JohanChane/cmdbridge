# setup.py

from setuptools import setup, find_packages

setup(
    name="cmdbridge",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "tomli>=2.0.0",
        "tomli-w>=1.0.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'cmdbridge=cmdbridge.cli.cli:cli',
            'cmdbridge-edit=cmdbridge_edit.cli.cli:cli',  # 更新入口点路径
        ],
    },
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        'cmdbridge': ['configs/*', 'configs/*/*', 'configs/*/*/*', 'cli/*.py'],
        'cmdbridge_edit': ['cli/*.py'],  # 确保包含 CLI 文件
    },
)