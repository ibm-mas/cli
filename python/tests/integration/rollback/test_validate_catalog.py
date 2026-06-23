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

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput

from mas.cli.rollback.app import RollbackApp


def _make_app(installed_catalog_id: str, target_catalog: str) -> RollbackApp:
    """Return a RollbackApp with installedCatalogId and mas_catalog_version pre-set."""
    with create_app_session(output=DummyOutput()):
        app = RollbackApp()
        app.installedCatalogId = installed_catalog_id
        app.params = {"mas_catalog_version": target_catalog}
        return app


def test_validate_catalog_older_version_passes():
    """
    validateCatalog should NOT raise when rolling back to an older catalog.

    GIVEN the target catalog is older than the installed catalog
    WHEN validateCatalog() is called
    THEN no error is raised.
    """
    with create_app_session(output=DummyOutput()):
        app = _make_app("v9-260527-amd64", "v9-260430-amd64")
        app.validateCatalog()  # must not raise


def test_validate_catalog_same_version_passes():
    """
    validateCatalog should NOT raise when rolling back to the same catalog version.

    GIVEN the target catalog equals the installed catalog
    WHEN validateCatalog() is called
    THEN no error is raised.
    """
    with create_app_session(output=DummyOutput()):
        app = _make_app("v9-260430-amd64", "v9-260430-amd64")
        app.validateCatalog()  # must not raise


def test_validate_catalog_newer_version_raises():
    """
    validateCatalog should raise SystemExit when target catalog is newer than installed.

    GIVEN the target catalog is newer than the installed catalog
    WHEN validateCatalog() is called
    THEN SystemExit(1) is raised.
    """
    with create_app_session(output=DummyOutput()):
        app = _make_app("v9-260129-amd64", "v9-260430-amd64")
        with pytest.raises(SystemExit) as exc_info:
            app.validateCatalog()
        assert exc_info.value.code == 1


def test_validate_catalog_none_installed_skips():
    """
    validateCatalog should NOT raise when installedCatalogId is None.

    GIVEN installedCatalogId is None (catalog not detected)
    WHEN validateCatalog() is called
    THEN no error is raised (comparison is skipped).
    """
    with create_app_session(output=DummyOutput()):
        app = _make_app(None, "v9-260430-amd64")
        app.validateCatalog()  # must not raise
