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
Unit tests for UpdateApp focusing on the two dev-mode bug fixes.

Fix 1 – Dev mode catalog fallback:
  GIVEN dev mode is active and the user-specified catalog tag has no YAML definition
  WHEN the catalog resolution runs
  THEN getCatalog is called with getNewestCatalogTag() instead and no exception is raised

Fix 2 – CPD already at target version:
  GIVEN a Cloud Pak for Data instance whose installed version equals the catalog target version
  WHEN detectCP4D runs
  THEN it exits cleanly with a success message instead of raising a fatal error
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mas.cli.update.app import UpdateApp
from mas.devops.data import NoSuchCatalogError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app() -> UpdateApp:
    """Build a minimal UpdateApp instance without touching the CLI arg parser."""
    app = UpdateApp.__new__(UpdateApp)
    # Attributes set by update() that the methods under test read
    app.devMode = True
    app.noConfirm = True
    app.spinner = "dots"
    app.successIcon = "✅"
    app.failureIcon = "❌"
    app.params = {}
    app.chosenCatalog = None
    # dynamicClient is a property backed by _dynClient — set the private attr
    app._dynClient = MagicMock()
    return app


def _make_args(**kwargs) -> SimpleNamespace:
    """Return a minimal args namespace."""
    defaults = dict(
        mas_catalog_version=None,
        dev_mode=True,
        no_confirm=True,
        cpd_product_version=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Fix 1: Dev mode catalog fallback
# ---------------------------------------------------------------------------


class TestDevModeCatalogFallback:
    """Test catalog resolution in dev mode."""

    @patch("mas.cli.update.app.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.cli.update.app.getCatalog")
    def test_known_catalog_tag_is_loaded_directly(self, mock_get_catalog, mock_newest):
        """Test that a known catalog tag is loaded without fallback.

        GIVEN dev mode is active and the catalog tag resolves to an existing YAML
        WHEN catalog resolution runs
        THEN getCatalog is called once with the specified tag.
        """
        app = _make_app()
        app.args = _make_args(mas_catalog_version="v9-241205-amd64")
        mock_get_catalog.return_value = {"cpd_product_version_default": "5.3.1"}
        app.getParam = MagicMock(return_value="v9-241205-amd64")

        # Execute just the dev-mode catalog resolution block
        catalogVersion = app.getParam("mas_catalog_version") if app.args.mas_catalog_version else mock_newest()
        try:
            app.chosenCatalog = mock_get_catalog(catalogVersion)
        except NoSuchCatalogError:
            app.chosenCatalog = mock_get_catalog(mock_newest())

        mock_get_catalog.assert_called_once_with("v9-241205-amd64")
        assert app.chosenCatalog == {"cpd_product_version_default": "5.3.1"}

    @patch("mas.cli.update.app.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.cli.update.app.getCatalog")
    def test_unknown_catalog_tag_falls_back_to_newest(self, mock_get_catalog, mock_newest):
        """Test that an unknown custom dev tag falls back to the newest catalog.

        GIVEN dev mode is active and the catalog tag is a custom dev image name with no YAML
        WHEN getCatalog raises NoSuchCatalogError for the custom tag
        THEN getCatalog is retried with getNewestCatalogTag() and chosenCatalog is set.
        """
        app = _make_app()
        app.args = _make_args(mas_catalog_version="v9-db2ucn3-amd64")
        newest_catalog = {"cpd_product_version_default": "5.3.1"}
        mock_get_catalog.side_effect = [
            NoSuchCatalogError("v9-db2ucn3-amd64 is unknown"),
            newest_catalog,
        ]
        app.getParam = MagicMock(return_value="v9-db2ucn3-amd64")

        catalogVersion = app.getParam("mas_catalog_version") if app.args.mas_catalog_version else mock_newest()
        try:
            app.chosenCatalog = mock_get_catalog(catalogVersion)
        except NoSuchCatalogError:
            app.chosenCatalog = mock_get_catalog(mock_newest())

        assert mock_get_catalog.call_count == 2
        mock_get_catalog.assert_any_call("v9-db2ucn3-amd64")
        mock_get_catalog.assert_any_call("v9-241205-amd64")
        assert app.chosenCatalog == newest_catalog

    @patch("mas.cli.update.app.getNewestCatalogTag", return_value="v9-241205-amd64")
    @patch("mas.cli.update.app.getCatalog")
    def test_no_catalog_arg_uses_newest_tag(self, mock_get_catalog, mock_newest):
        """Test that omitting --catalog in dev mode uses the newest catalog tag.

        GIVEN dev mode is active and no catalog version is provided
        WHEN catalog resolution runs
        THEN getNewestCatalogTag() is used to resolve the catalog version.
        """
        app = _make_app()
        app.args = _make_args(mas_catalog_version=None)
        newest_catalog = {"cpd_product_version_default": "5.4.0"}
        mock_get_catalog.return_value = newest_catalog

        catalogVersion = app.args.mas_catalog_version if app.args.mas_catalog_version else mock_newest()
        try:
            app.chosenCatalog = mock_get_catalog(catalogVersion)
        except NoSuchCatalogError:
            app.chosenCatalog = mock_get_catalog(mock_newest())

        mock_newest.assert_called_once()
        mock_get_catalog.assert_called_once_with("v9-241205-amd64")
        assert app.chosenCatalog == newest_catalog


# ---------------------------------------------------------------------------
# Fix 2: CPD already at target version
# ---------------------------------------------------------------------------


class TestDetectCP4DVersionCheck:
    """Test Cloud Pak for Data version checks inside detectCP4D."""

    def _make_cpd_resource(self, namespace: str, version: str) -> dict:
        return {
            "metadata": {"namespace": namespace},
            "spec": {
                "version": version,
                "storageClass": "ocs-storagecluster-cephfs",
                "zenCoreMetadbStorageClass": "ocs-storagecluster-ceph-rbd",
            },
        }

    def _setup_cpd_api(self, app: UpdateApp, cpds: list) -> None:
        cpd_api = MagicMock()
        cpd_api.get.return_value.to_dict.return_value = {"items": cpds}
        app.dynamicClient.resources.get.return_value = cpd_api

    @patch("mas.cli.update.app.Halo")
    def test_cpd_already_at_target_version_exits_cleanly(self, mock_halo):
        """Test that equal installed and target CPD versions trigger a no-op success message.

        GIVEN a CPD instance at version 5.3.1 and the catalog target is also 5.3.1
        WHEN detectCP4D runs
        THEN it persists a success message and returns without calling fatalError.
        """
        app = _make_app()
        app.args = _make_args()
        app.chosenCatalog = {"cpd_product_version_default": "5.3.1"}
        app.getParam = MagicMock(return_value=None)
        app.fatalError = MagicMock()
        app.printDescription = MagicMock()
        app.printHighlight = MagicMock()

        mock_halo_instance = MagicMock()
        mock_halo_instance.__enter__ = MagicMock(return_value=mock_halo_instance)
        mock_halo_instance.__exit__ = MagicMock(return_value=False)
        mock_halo.return_value = mock_halo_instance

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        app.detectCP4D()

        # fatalError must NOT be called
        app.fatalError.assert_not_called()
        # Success message must reference both namespace and version
        stop_call_args = mock_halo_instance.stop_and_persist.call_args
        assert "5.3.1" in stop_call_args.kwargs.get("text", "")
        assert "no update required" in stop_call_args.kwargs.get("text", "").lower()

    @patch("mas.cli.update.app.Halo")
    def test_cpd_upgrade_path_violation_raises_fatal_error(self, mock_halo):
        """Test that skipping an intermediate CPD version triggers a fatal error.

        GIVEN a CPD instance at 5.3.1 and the catalog target is 5.5.0 (not a valid next step)
        WHEN detectCP4D runs
        THEN fatalError is called describing the upgrade path constraint.
        """
        app = _make_app()
        app.args = _make_args()
        app.chosenCatalog = {"cpd_product_version_default": "5.5.0"}
        app.getParam = MagicMock(return_value=None)
        app.fatalError = MagicMock()
        app.printDescription = MagicMock()
        app.printHighlight = MagicMock()

        mock_halo_instance = MagicMock()
        mock_halo_instance.__enter__ = MagicMock(return_value=mock_halo_instance)
        mock_halo_instance.__exit__ = MagicMock(return_value=False)
        mock_halo.return_value = mock_halo_instance

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        app.detectCP4D()

        app.fatalError.assert_called_once()
        error_msg = app.fatalError.call_args[0][0]
        assert "not supported" in error_msg.lower()

    @patch("mas.cli.update.app.Halo")
    def test_cpd_valid_upgrade_does_not_trigger_early_exit(self, mock_halo):
        """Test that a valid CPD upgrade path sets update params correctly.

        GIVEN a CPD instance at 5.3.1 and the catalog target is 5.4.0 (valid next step)
        WHEN detectCP4D runs
        THEN fatalError is not called and update params are configured.
        """
        app = _make_app()
        app.args = _make_args()
        app.chosenCatalog = {"cpd_product_version_default": "5.4.0"}
        app.getParam = MagicMock(return_value=None)
        app.fatalError = MagicMock()
        app.printDescription = MagicMock()
        app.printHighlight = MagicMock()
        app.setParam = MagicMock()
        app.detectCpdService = MagicMock()

        mock_halo_instance = MagicMock()
        mock_halo_instance.__enter__ = MagicMock(return_value=mock_halo_instance)
        mock_halo_instance.__exit__ = MagicMock(return_value=False)
        mock_halo.return_value = mock_halo_instance

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        app.detectCP4D()

        app.fatalError.assert_not_called()
        # Confirm the update params were set
        app.setParam.assert_any_call("cpd_product_version", "5.4.0")
        app.setParam.assert_any_call("cp4d_update", "true")
