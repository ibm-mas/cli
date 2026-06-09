# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Regression tests for root pyproject packaging metadata."""

from pathlib import Path

import tomllib


def test_root_pyproject_declares_mas_cli_package_metadata() -> None:
    """Test that root pyproject declares mas-cli package metadata.

    GIVEN the repository root pyproject configuration
    WHEN the packaging metadata is inspected
    THEN it declares the mas-cli project, root-based package discovery, and CLI entry point.
    """
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    project = pyproject_data["project"]
    setuptools_tool = pyproject_data["tool"]["setuptools"]

    assert project["name"] == "mas-cli"
    assert project["dynamic"] == ["version"]
    assert project["license"] == "EPL-1.0"
    assert project["scripts"]["mas-cli"] == "mas.cli.__main__:main"
    assert setuptools_tool["package-dir"] == {"": "python/src"}


def test_root_pyproject_console_script_targets_importable_main() -> None:
    """Test that root pyproject console script targets an importable main function.

    GIVEN the repository root pyproject configuration
    WHEN the mas-cli console script target is resolved
    THEN it points to a module and callable that can be imported by installers such as uvx.
    """
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    module_name, function_name = pyproject_data["project"]["scripts"]["mas-cli"].split(":")

    module = __import__(module_name, fromlist=[function_name])

    assert callable(getattr(module, function_name))
