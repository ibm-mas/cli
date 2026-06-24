#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rollback_test_helper import RollbackTestConfig, run_rollback_test  # noqa: E402


def test_rollback_non_interactive_core_only(tmpdir):
    """Test non-interactive rollback rolling back only MAS core.

    Expected behavior:
    - Catalog and instance ID are provided via argv
    - Only mas_core_version is specified
    - Pipeline is launched without prompts
    - Rollback proceeds successfully
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--no-confirm",
            ],
        ),
    )


def test_rollback_non_interactive_core_and_manage(tmpdir):
    """Test non-interactive rollback rolling back core and Manage app.

    Expected behavior:
    - Both mas_core_version and mas_app_manage_version are provided
    - Both parameters are set in the pipeline
    - Rollback proceeds successfully
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--manage-version",
                "9.0.x",
                "--no-confirm",
            ],
        ),
    )


def test_rollback_non_interactive_all_versions(tmpdir):
    """Test non-interactive rollback with core, Manage, and IoT versions.

    Expected behavior:
    - All three app versions (core, manage, iot) are provided
    - All three parameters are set in the pipeline
    - Rollback proceeds successfully
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--manage-version",
                "9.0.x",
                "--iot-version",
                "9.0.x",
                "--no-confirm",
            ],
        ),
    )


def test_rollback_non_interactive_newer_catalog_is_rejected(tmpdir):
    """Test non-interactive rollback fails when target catalog is newer than installed.

    Expected behavior:
    - Target catalog version is newer than the installed one
    - validateCatalog() detects this forward-rollback attempt
    - SystemExit(1) is raised (fatalError path)
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260129-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",  # newer than installed
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--no-confirm",
            ],
            expect_system_exit=True,
            expected_exit_code=1,
        ),
    )


def test_rollback_non_interactive_dev_mode_skips_catalog_validation(tmpdir):
    """Test that --dev-mode bypasses validateCatalog.

    Expected behavior:
    - Target catalog is newer than installed (normally rejected)
    - --dev-mode flag is set so validateCatalog() is skipped
    - Pipeline is launched successfully despite the newer catalog
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260129-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",  # newer — normally rejected
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--no-confirm",
                "--dev-mode",
            ],
        ),
    )


def test_rollback_non_interactive_with_artifactory_creds(tmpdir):
    """Test non-interactive rollback with Artifactory credentials for dev catalogs.

    Expected behavior:
    - --artifactory-username and --artifactory-token are provided alongside --dev-mode
    - Those optional params are stored and passed through to the pipeline
    - Rollback proceeds without error
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            argv=[
                "--catalog",
                "v9-260430-amd64",
                "--mas-instance-id",
                "inst1",
                "--mas-version",
                "9.0.x",
                "--no-confirm",
                "--dev-mode",
                "--artifactory-username",
                "testuser",
                "--artifactory-token",
                "testtoken",
            ],
        ),
    )
