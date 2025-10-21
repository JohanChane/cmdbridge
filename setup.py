from setuptools import setup, find_packages

setup(
    name="cmdbridge",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "tomli-w>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'cmdbridge=cmdbridge.cli:cli',
            'cmdbridge-config=cmdbridge_config.main:main',
            'cmdbridge-edit=cmdbridge_execute.main:main',
        ],
    },
    python_requires=">=3.7",
)