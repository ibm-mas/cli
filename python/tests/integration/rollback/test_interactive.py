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


def test_interactive_rollback_select_catalog_and_confirm(tmpdir):
    """Test interactive rollback: user selects catalog and confirms.

    Expected behavior:
    - No --catalog flag → interactive mode
    - User is prompted to select a catalog version
    - User confirms the summary
    - Pipeline is launched successfully
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            mas_instances=[{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.4"}}}],
            prompt_handlers={
                r".*Select catalog version to rollback to.*": lambda m: "2",  # index 2 = v9-260430-amd64
                r".*Proceed with these settings.*": lambda m: "y",
            },
            argv=[],  # no --catalog → interactive
        ),
    )


def test_interactive_rollback_user_aborts_at_confirmation(tmpdir):
    """Test interactive rollback: user declines the final confirmation prompt.

    Expected behavior:
    - User selects a catalog version
    - User answers 'n' at the final "Proceed with these settings" prompt
    - Pipeline is NOT launched
    - Rollback exits without error
    """
    run_rollback_test(
        tmpdir,
        RollbackTestConfig(
            installed_catalog_id="v9-260527-amd64",
            mas_instances=[{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.4"}}}],
            prompt_handlers={
                r".*Select catalog version to rollback to.*": lambda m: "2",  # index 2 = v9-260430-amd64
                r".*Proceed with these settings.*": lambda m: "n",
            },
            argv=[],
        ),
    )
