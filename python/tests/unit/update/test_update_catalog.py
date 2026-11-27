# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the catalog selection and review methods on UpdateApp.

All tests follow the GIVEN-WHEN-THEN convention and verify that:
- All catalog methods are present on UpdateApp
- getCatalogOptions returns the curated option list
- checkCatalog raises ValueError on validation failures
- validateCatalog converts a checkCatalog failure into fatalError
"""

from unittest.mock import MagicMock, patch

import pytest

from mas.cli.update.app import UpdateApp


def _make_app() -> UpdateApp:
    """Return a minimal UpdateApp instance with a mocked dynamic client."""
    app = UpdateApp()
    app._dynClient = MagicMock()
    app.installedCatalogId = None
    return app


def test_catalog_methods_present_on_update_app():
    """Test that all catalog methods are accessible on UpdateApp.

    GIVEN the UpdateApp class
    WHEN each catalog method name is looked up on the class
    THEN each method is present.
    """
    expectedMethods = [
        "reviewCurrentCatalog",
        "reviewMASInstance",
        "reviewAiServiceInstance",
        "reviewInstances",
        "getCatalogOptions",
        "checkCatalog",
        "validateCatalog",
        "validateCatalogSelection",
    ]
    for methodName in expectedMethods:
        assert hasattr(UpdateApp, methodName), f"UpdateApp is missing method: {methodName}"


def test_get_catalog_options_returns_list():
    """Test that getCatalogOptions returns a non-empty list of strings.

    GIVEN an UpdateApp instance
    WHEN getCatalogOptions is called
    THEN it returns a non-empty list of strings.
    """
    options = _make_app().getCatalogOptions()
    assert isinstance(options, list)
    assert len(options) > 0
    for option in options:
        assert isinstance(option, str)


@patch("mas.cli.update.app.getClusterVersion", return_value="4.18.0")
@patch("mas.cli.update.app.getCatalog")
def test_check_catalog_accepts_compatible_catalog(mock_get_catalog, mock_cluster_version):
    """Test that checkCatalog passes for a compatible catalog.

    GIVEN a catalog compatible with the cluster version and newer than the installed one
    WHEN checkCatalog is called
    THEN it does not raise and sets chosenCatalog.
    """
    app = _make_app()
    app.setParam("mas_catalog_version", "v9-261105-amd64")
    app.installedCatalogId = "v9-260924-amd64"
    mock_get_catalog.return_value = {"ocp_compatibility": ["4.16", "4.17", "4.18"]}

    app.checkCatalog()

    assert app.chosenCatalog == {"ocp_compatibility": ["4.16", "4.17", "4.18"]}


@patch("mas.cli.update.app.getClusterVersion", return_value="4.15.0")
@patch("mas.cli.update.app.getCatalog")
def test_check_catalog_rejects_incompatible_ocp(mock_get_catalog, mock_cluster_version):
    """Test that checkCatalog raises ValueError for an incompatible OCP version.

    GIVEN a catalog that does not support the cluster's OCP version
    WHEN checkCatalog is called
    THEN ValueError is raised describing the compatible releases.
    """
    app = _make_app()
    app.setParam("mas_catalog_version", "v9-261105-amd64")
    mock_get_catalog.return_value = {"ocp_compatibility": ["4.16", "4.17", "4.18"]}

    with pytest.raises(ValueError) as excInfo:
        app.checkCatalog()

    assert "not compatible" in str(excInfo.value)


@patch("mas.cli.update.app.getClusterVersion", return_value="4.18.0")
@patch("mas.cli.update.app.getCatalog")
def test_check_catalog_rejects_older_catalog(mock_get_catalog, mock_cluster_version):
    """Test that checkCatalog raises ValueError when the selected catalog is older than installed.

    GIVEN an installed catalog newer than the selected target
    WHEN checkCatalog is called
    THEN ValueError is raised describing the downgrade attempt.
    """
    app = _make_app()
    app.setParam("mas_catalog_version", "v9-260924-amd64")
    app.installedCatalogId = "v9-261105-amd64"
    mock_get_catalog.return_value = {"ocp_compatibility": []}

    with pytest.raises(ValueError) as excInfo:
        app.checkCatalog()

    assert "older than the currently installed catalog" in str(excInfo.value)


@patch("mas.cli.update.app.getClusterVersion", return_value="4.18.0")
@patch("mas.cli.update.app.getCatalog")
def test_validate_catalog_converts_value_error_to_fatal(mock_get_catalog, mock_cluster_version):
    """Test that validateCatalog calls fatalError when checkCatalog raises.

    GIVEN a catalog selection that fails checkCatalog
    WHEN validateCatalog is called
    THEN fatalError is invoked with the validation message.
    """
    app = _make_app()
    app.setParam("mas_catalog_version", "v9-260924-amd64")
    app.installedCatalogId = "v9-261105-amd64"
    mock_get_catalog.return_value = {"ocp_compatibility": []}
    app.fatalError = MagicMock()

    app.validateCatalog()

    app.fatalError.assert_called_once()
