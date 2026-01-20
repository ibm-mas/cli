"""Setup for mkdocs-mas-plugins."""

from setuptools import setup, find_packages

setup(
    name="mkdocs-mas-plugins",
    version="0.2.0",
    description="MkDocs plugins for MAS documentation (catalogs and CLI)",
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "mas_catalogs = mkdocs_mas_catalogs:MASCatalogsPlugin",
            "mas_cli = mkdocs_mas_cli:MASCLIPlugin",
        ]
    },
    install_requires=[
        "mkdocs>=1.0",
        "pyyaml",
    ],
    python_requires=">=3.8",
)

# Made with Bob
