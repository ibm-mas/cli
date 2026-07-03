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

"""Integration tests for mas update --mas-catalog-digest support.

These tests verify that the `--mas-catalog-digest` flag is accepted by
`mas update` and that the digest value is passed through to the Tekton
pipeline parameters.
"""

import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import UpdateTestConfig, UpdateTestHelper, run_update_test  # noqa: E402

_ONE_MAS_INSTANCE = [{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.7"}}}]


def test_mas_catalog_digest_arg_is_accepted(tmpdir):
    """Test that --mas-catalog-digest argument is accepted by mas update.

    GIVEN --catalog and --mas-catalog-digest are passed on the command line
    WHEN mas update parses the arguments
    THEN no SystemExit or 'unrecognized arguments' error is raised.
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        mas_instances=_ONE_MAS_INSTANCE,
        timeout_seconds=30,
        argv=[
            "--catalog",
            "v9-260129-amd64",
            "--mas-catalog-digest",
            "sha256:abc123def456",
            "--no-confirm",
        ],
    )
    run_update_test(tmpdir, config)


def test_mas_catalog_digest_passed_to_pipeline(tmpdir):
    """Test that mas_catalog_digest is passed to launchUpdatePipeline params.

    GIVEN --catalog v9-260129-amd64 and --mas-catalog-digest sha256:abc123def456
    WHEN mas update runs in non-interactive mode
    THEN launchUpdatePipeline is called with mas_catalog_digest set in params.
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        mas_instances=_ONE_MAS_INSTANCE,
        timeout_seconds=30,
        argv=[
            "--catalog",
            "v9-260129-amd64",
            "--mas-catalog-digest",
            "sha256:abc123def456",
            "--no-confirm",
        ],
    )

    helper = UpdateTestHelper(tmpdir, config)
    helper.run_update_test()

    assert helper.app is not None, "app should be set after update"
    assert helper.app.getParam("mas_catalog_digest") == "sha256:abc123def456", "mas_catalog_digest should be present in params passed to pipeline"


def test_mas_catalog_digest_omitted_defaults_empty(tmpdir):
    """Test that mas_catalog_digest defaults to empty string when not provided.

    GIVEN --catalog is passed without --mas-catalog-digest
    WHEN mas update runs in non-interactive mode
    THEN mas_catalog_digest is not set in params (i.e. None or absent).
    """
    config = UpdateTestConfig(
        prompt_handlers={},
        installed_catalog_id="v9-251231-amd64",
        target_catalog_version="v9-260129-amd64",
        mas_instances=_ONE_MAS_INSTANCE,
        timeout_seconds=30,
        argv=[
            "--catalog",
            "v9-260129-amd64",
            "--no-confirm",
        ],
    )

    helper = UpdateTestHelper(tmpdir, config)
    helper.run_update_test()

    assert helper.app is not None, "app should be set after update"
    digest = helper.app.getParam("mas_catalog_digest")
    assert digest is None or digest == "", f"mas_catalog_digest should be absent or empty when not provided, got: {digest!r}"
