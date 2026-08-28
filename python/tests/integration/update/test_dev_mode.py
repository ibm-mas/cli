#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Integration tests for mas update dev-mode behaviour with v9-master-amd64 catalog.

These tests verify that `mas update` completes gracefully when `getCatalog()` raises
`NoSuchCatalogError` (the v9-master-amd64 tag is only valid in master builds of
mas.devops, not in production releases).
"""

import sys
import os
from unittest import mock
from mas.devops.data import NoSuchCatalogError

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import UpdateTestConfig, run_update_test  # noqa: E402


def test_update_master_dev_mode(tmpdir):
    """Test that mas update --dev-mode succeeds when getCatalog raises NoSuchCatalogError.

    GIVEN --dev-mode and --mas-catalog-version v9-master-amd64 are passed
    WHEN getCatalog raises NoSuchCatalogError (catalog not present in production mas.devops)
    THEN the update proceeds without raising an exception and chosenCatalog remains None.
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id="v9-master-amd64",
        target_catalog_version="v9-master-amd64",
        mas_instances=[{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.7"}}}],
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--catalog",
            "v9-master-amd64",
            "--no-confirm",
        ],
    )

    with mock.patch("mas.cli.update.app.getCatalog", side_effect=NoSuchCatalogError("v9-master-amd64")):
        run_update_test(tmpdir, config)


def test_update_unknown_installed_catalog(tmpdir):
    """Test that mas update proceeds when the installed catalog ID cannot be determined.

    GIVEN the installed ibm-maximo-operator-catalog has a non-standard image tag (e.g. dev build)
    WHEN getCurrentCatalog returns catalogId=None
    THEN the update proceeds without AssertionError and prints 'Unknown' for the installed catalog.
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id=None,  # simulates getCurrentCatalog returning catalogId=None
        target_catalog_version="v9-master-amd64",
        mas_instances=[{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.7"}}}],
        timeout_seconds=30,
        argv=[
            "--dev-mode",
            "--catalog",
            "v9-master-amd64",
            "--no-confirm",
        ],
    )

    with mock.patch("mas.cli.update.app.getCatalog", side_effect=NoSuchCatalogError("v9-master-amd64")):
        run_update_test(tmpdir, config)


def test_update_master_no_dev_mode(tmpdir):
    """Test that mas update without --dev-mode succeeds when getCatalog raises NoSuchCatalogError.

    GIVEN --mas-catalog-version v9-master-amd64 is passed without --dev-mode
    WHEN getCatalog raises NoSuchCatalogError inside validateCatalog()
    THEN the update proceeds without raising an exception and chosenCatalog remains None.
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id="v9-master-amd64",
        target_catalog_version="v9-master-amd64",
        mas_instances=[{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.7"}}}],
        timeout_seconds=30,
        argv=[
            "--catalog",
            "v9-master-amd64",
            "--no-confirm",
        ],
    )

    with mock.patch("mas.cli.update.app.getCatalog", side_effect=NoSuchCatalogError("v9-master-amd64")):
        run_update_test(tmpdir, config)
