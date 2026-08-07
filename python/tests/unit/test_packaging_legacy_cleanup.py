# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Regression tests for legacy packaging cleanup."""

from pathlib import Path

import tomllib


def test_legacy_setup_py_and_manifest_are_removed() -> None:
    """Test that legacy packaging files are removed.

    GIVEN the migrated root packaging configuration
    WHEN legacy packaging files are checked
    THEN python/setup.py and python/MANIFEST.in no longer exist.
    """
    repository_root = Path(__file__).resolve().parents[2]

    assert not (repository_root / "python" / "setup.py").exists()
    assert not (repository_root / "python" / "MANIFEST.in").exists()


def test_root_pyproject_remains_the_single_packaging_source() -> None:
    """Test that root pyproject remains the single packaging source.

    GIVEN the repository root pyproject configuration
    WHEN packaging metadata is inspected after cleanup
    THEN the project metadata and setuptools package data remain defined at the root.
    """
    pyproject_path = Path(__file__).resolve().parents[3] / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert pyproject_data["project"]["name"] == "mas-cli"
    assert "package-data" in pyproject_data["tool"]["setuptools"]


# Made with Bob
