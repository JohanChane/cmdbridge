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
    entry_points={
        'console_scripts': [
            'cmdbridge=cmdbridge.cli:cli',
        ],
    },
    python_requires=">=3.7",
    include_package_data=True,
    package_data={
        'cmdbridge': ['configs/*', 'configs/*/*', 'configs/*/*/*'],
    },
)