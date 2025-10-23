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
            'cmdbridge=cmdbridge.cli:cli',
            'cmdbridge-edit=cmdbridge_edit.cli:cli',
        ],
    },
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        'cmdbridge': ['configs/*', 'configs/*/*', 'configs/*/*/*'],
        'cmdbridge_edit': ['*.py'],  # 确保包含所有 Python 文件
    },
)