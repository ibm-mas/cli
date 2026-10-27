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

"""
Unit tests for InstallApp catalog-loading logic in nonInteractiveMode.

Fix 3 – Install non-interactive catalog handling:

  GIVEN dev mode is active and a custom image tag has no YAML definition
  WHEN the catalog-loading block runs
  THEN getCatalog falls back to getNewestCatalogTag() and processCatalogChoice is called

  GIVEN dev mode is active and the catalog tag resolves to an existing YAML
  WHEN the catalog-loading block runs
  THEN getCatalog is called once with the specified tag

  GIVEN non-dev mode and the specified catalog tag has no YAML definition
  WHEN the catalog-loading block runs
  THEN fatalError is called with a clear message and no fallback is attempted

  GIVEN non-dev mode and the specified catalog tag is valid
  WHEN the catalog-loading block runs
  THEN getCatalog is called once and chosenCatalog is set
"""

import pytest
from unittest.mock import MagicMock, patch, call

from mas.cli.install.app import InstallApp
from mas.devops.data import NoSuchCatalogError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(dev_mode: bool = True) -> InstallApp:
    """Build a minimal InstallApp instance for catalog-loading tests."""
    app = InstallApp.__new__(InstallApp)
    app.devMode = dev_mode
    app.noConfirm = True
    app.spinner = "dots"
    app.successIcon = "✅"
    app.failureIcon = "❌"
    app.params = {}
    app._dynClient = MagicMock()
    # Mock the methods called inside the catalog-loading block
    app.processCatalogChoice = MagicMock()
    app.fatalError = MagicMock()
    return app


def _run_catalog_block(app: InstallApp, catalog_version: str) -> None:
    """Execute the catalog-loading block from nonInteractiveMode in isolation."""
    from mas.devops.data import getCatalog, getNewestCatalogTag, NoSuchCatalogError

    app.params["mas_catalog_version"] = catalog_version
    try:
        app.chosenCatalog = getCatalog(app.getParam("mas_catalog_version"))
        app.processCatalogChoice()
    except NoSuchCatalogError:
        if app.devMode:
            app.chosenCatalog = getCatalog(getNewestCatalogTag())
            app.processCatalogChoice()
        else:
            app.fatalError(f"Catalog '{app.getParam('mas_catalog_version')}' is unknown. Use a valid catalog tag or run with --dev-mode for custom dev image tags")


# ---------------------------------------------------------------------------
# Dev mode catalog fallback tests
# ---------------------------------------------------------------------------


class TestInstallCatalogLoadingDevMode:
    """Test catalog loading in dev mode (Fix 3, dev mode path)."""

    @patch("mas.devops.data.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.devops.data.getCatalog")
    def test_dev_mode_known_tag_loaded_directly(self, mock_get_catalog, mock_newest):
        """Test that a known catalog tag is loaded without fallback in dev mode.

        GIVEN dev mode is active and the catalog tag has a matching YAML
        WHEN the catalog-loading block runs
        THEN getCatalog is called once with the given tag and chosenCatalog is set.
        """
        app = _make_app(dev_mode=True)
        known_catalog = {"cpd_product_version_default": "5.3.1"}
        mock_get_catalog.return_value = known_catalog

        _run_catalog_block(app, "v9-241205-amd64")

        mock_get_catalog.assert_called_once_with("v9-241205-amd64")
        assert app.chosenCatalog == known_catalog
        app.processCatalogChoice.assert_called_once()
        app.fatalError.assert_not_called()

    @patch("mas.devops.data.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.devops.data.getCatalog")
    def test_dev_mode_unknown_tag_falls_back_to_newest(self, mock_get_catalog, mock_newest):
        """Test that an unknown custom dev tag falls back to the newest catalog in dev mode.

        GIVEN dev mode is active and the catalog tag has no YAML definition
        WHEN getCatalog raises NoSuchCatalogError for the custom tag
        THEN getCatalog is retried with getNewestCatalogTag() and chosenCatalog is set.
        """
        app = _make_app(dev_mode=True)
        newest_catalog = {"cpd_product_version_default": "5.3.1"}
        mock_get_catalog.side_effect = [
            NoSuchCatalogError("v9-db2ucn3-amd64 is unknown"),
            newest_catalog,
        ]

        _run_catalog_block(app, "v9-db2ucn3-amd64")

        assert mock_get_catalog.call_count == 2
        mock_get_catalog.assert_any_call("v9-db2ucn3-amd64")
        mock_get_catalog.assert_any_call("v9-241205-amd64")
        assert app.chosenCatalog == newest_catalog
        assert app.processCatalogChoice.call_count == 1
        app.fatalError.assert_not_called()

    @patch("mas.devops.data.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.devops.data.getCatalog")
    def test_dev_mode_fallback_calls_process_catalog_choice(self, mock_get_catalog, mock_newest):
        """Test that processCatalogChoice is called once after the fallback in dev mode.

        GIVEN dev mode is active and the catalog tag has no YAML definition
        WHEN getCatalog falls back to the newest catalog
        THEN processCatalogChoice is called exactly once with the fallback catalog.
        """
        app = _make_app(dev_mode=True)
        newest_catalog = {"cpd_product_version_default": "5.4.0"}
        mock_get_catalog.side_effect = [
            NoSuchCatalogError("v9-custom-amd64 is unknown"),
            newest_catalog,
        ]

        _run_catalog_block(app, "v9-custom-amd64")

        app.processCatalogChoice.assert_called_once()
        assert app.chosenCatalog == newest_catalog


# ---------------------------------------------------------------------------
# Non-dev mode catalog error tests
# ---------------------------------------------------------------------------


class TestInstallCatalogLoadingNonDevMode:
    """Test catalog loading in non-dev mode (Fix 3, non-dev mode path)."""

    @patch("mas.devops.data.getCatalog")
    def test_non_dev_mode_known_tag_loaded_directly(self, mock_get_catalog):
        """Test that a valid catalog tag loads normally in non-dev mode.

        GIVEN non-dev mode and a known catalog tag
        WHEN the catalog-loading block runs
        THEN getCatalog is called once, chosenCatalog is set, and fatalError is not called.
        """
        app = _make_app(dev_mode=False)
        known_catalog = {"cpd_product_version_default": "5.3.1"}
        mock_get_catalog.return_value = known_catalog

        _run_catalog_block(app, "v9-260924-amd64")

        mock_get_catalog.assert_called_once_with("v9-260924-amd64")
        assert app.chosenCatalog == known_catalog
        app.processCatalogChoice.assert_called_once()
        app.fatalError.assert_not_called()

    @patch("mas.devops.data.getCatalog")
    def test_non_dev_mode_unknown_tag_triggers_fatal_error(self, mock_get_catalog):
        """Test that an unknown catalog tag raises a fatalError in non-dev mode.

        GIVEN non-dev mode and a catalog tag that has no YAML definition
        WHEN getCatalog raises NoSuchCatalogError
        THEN fatalError is called with a descriptive message and no fallback is attempted.
        """
        app = _make_app(dev_mode=False)
        mock_get_catalog.side_effect = NoSuchCatalogError("v9-bad-tag-amd64 is unknown")

        _run_catalog_block(app, "v9-bad-tag-amd64")

        mock_get_catalog.assert_called_once_with("v9-bad-tag-amd64")
        app.fatalError.assert_called_once()
        error_msg = app.fatalError.call_args[0][0]
        assert "v9-bad-tag-amd64" in error_msg
        assert "--dev-mode" in error_msg
        # chosenCatalog should not be set — attribute was never assigned
        assert not hasattr(app, "chosenCatalog")

    @patch("mas.devops.data.getCatalog")
    def test_non_dev_mode_unknown_tag_does_not_fall_back(self, mock_get_catalog):
        """Test that no fallback to newest catalog happens in non-dev mode.

        GIVEN non-dev mode and an unknown catalog tag
        WHEN getCatalog raises NoSuchCatalogError
        THEN getCatalog is called exactly once (no retry with getNewestCatalogTag).
        """
        app = _make_app(dev_mode=False)
        mock_get_catalog.side_effect = NoSuchCatalogError("v9-bad-tag-amd64 is unknown")

        _run_catalog_block(app, "v9-bad-tag-amd64")

        mock_get_catalog.assert_called_once()
        app.processCatalogChoice.assert_not_called()
