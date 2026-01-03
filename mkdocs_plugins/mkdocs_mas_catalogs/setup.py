"""Setup for mkdocs-mas-catalogs plugin."""

from setuptools import setup, find_packages

setup(
    name="mkdocs-mas-catalogs",
    version="0.1.0",
    description="MkDocs plugin to dynamically render MAS catalog documentation",
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "mas_catalogs = mkdocs_mas_catalogs:MASCatalogsPlugin",
        ]
    },
    install_requires=[
        "mkdocs>=1.0",
        "pyyaml",
    ],
    python_requires=">=3.8",
)

# Made with Bob
