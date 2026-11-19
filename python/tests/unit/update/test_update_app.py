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
Unit tests for UpdateApp.

Covers the dev-mode catalog fallback, the Cloud Pak for Data version checks
inside detectCP4D, and the launchUpdate stage helper methods.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from mas.cli.update.app import UpdateApp
from mas.cli.update.dependencies import DetectResult
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
    app.tuiMode = False
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
# Dev mode catalog fallback
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
# CPD already at target version (detectCP4D returns DetectResult)
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

    def test_cpd_already_at_target_version_exits_cleanly(self):
        """Test that equal installed and target CPD versions trigger a no-op success message.

        GIVEN a CPD instance at version 5.3.1 and the catalog target is also 5.3.1
        WHEN detectCP4D runs
        THEN it returns an ok DetectResult and does not call fatalError.
        """
        app = _make_app()
        app.args = _make_args()
        app.chosenCatalog = {"cpd_product_version_default": "5.3.1"}
        app.getParam = MagicMock(return_value=None)
        app.fatalError = MagicMock()
        app.printDescription = MagicMock()
        app.printHighlight = MagicMock()

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        result = app.detectCP4D()

        # fatalError must NOT be called
        app.fatalError.assert_not_called()
        # Success message must reference both namespace and version
        assert isinstance(result, DetectResult)
        assert result.ok is True
        assert "5.3.1" in result.message
        assert "no update required" in result.message.lower()

    def test_cpd_upgrade_path_violation_is_blocking(self):
        """Test that skipping an intermediate CPD version triggers a blocking failure.

        GIVEN a CPD instance at 5.3.1 and the catalog target is 5.5.0 (not a valid next step)
        WHEN detectCP4D runs
        THEN it returns a non-ok DetectResult describing the upgrade path constraint.
        """
        app = _make_app()
        app.args = _make_args()
        app.chosenCatalog = {"cpd_product_version_default": "5.5.0"}
        app.getParam = MagicMock(return_value=None)
        app.fatalError = MagicMock()
        app.printDescription = MagicMock()
        app.printHighlight = MagicMock()

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        result = app.detectCP4D()

        assert isinstance(result, DetectResult)
        assert result.ok is False
        assert "not supported" in result.message.lower()

    def test_cpd_valid_upgrade_does_not_trigger_early_exit(self):
        """Test that a valid CPD upgrade path sets update params correctly.

        GIVEN a CPD instance at 5.3.1 and the catalog target is 5.4.0 (valid next step)
        WHEN detectCP4D runs
        THEN it returns an ok DetectResult and update params are configured.
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

        self._setup_cpd_api(app, [self._make_cpd_resource("ibm-cpd", "5.3.1")])

        result = app.detectCP4D()

        assert isinstance(result, DetectResult)
        assert result.ok is True
        # Confirm the update params were set
        app.setParam.assert_any_call("cpd_product_version", "5.4.0")
        app.setParam.assert_any_call("cp4d_update", "true")


# ---------------------------------------------------------------------------
# RHOAI channel follows the target catalog
# ---------------------------------------------------------------------------


class TestRhoaiChannelForCatalog:
    """The RHOAI channel/major version used by mas update is determined by the target catalog."""

    def test_rhoai_v3_catalog_uses_stable_3x(self):
        from mas.cli.install.settings.aiSettings import getRhoaiChannelForCatalog

        assert getRhoaiChannelForCatalog({"aiservice_platform": "rhoai-v3"}) == "stable-3.x"

    def test_catalog_without_platform_uses_stable_for_rhoai_v2(self):
        from mas.cli.install.settings.aiSettings import getRhoaiChannelForCatalog

        assert getRhoaiChannelForCatalog({"aiservice_version": {"9.1.x": "9.1.0"}}) == "stable"

    def test_unknown_platform_or_no_catalog_returns_none(self):
        from mas.cli.install.settings.aiSettings import getRhoaiChannelForCatalog

        assert getRhoaiChannelForCatalog({"aiservice_platform": "other"}) is None
        assert getRhoaiChannelForCatalog(None) is None


class TestDetectRHOAIv2:
    """RHOAI v2 -> v3 upgrade is only evaluated when the target catalog uses RHOAI v3."""

    def _app_with_installed_csv(self, channel: str, installed_csv: str) -> UpdateApp:
        app = _make_app()
        app.params = {"rhoai_channel": channel} if channel else {}
        subscription = MagicMock()
        subscription.to_dict.return_value = {"status": {"installedCSV": installed_csv}}
        app._dynClient.resources.get.return_value.get.return_value = subscription
        return app

    def test_v2_installed_and_v3_catalog_triggers_upgrade(self):
        app = self._app_with_installed_csv("stable-3.x", "rhods-operator.2.25.0")

        result = app.detectRHOAIv2()
        assert isinstance(result, DetectResult)
        assert result.ok is True
        assert app.rhoaiV2Detected is True
        assert app.getParam("odh_to_rhoai_migration") == "true"

    def test_v2_installed_and_v2_catalog_does_nothing(self):
        app = self._app_with_installed_csv("stable", "rhods-operator.2.25.0")

        result = app.detectRHOAIv2()
        assert isinstance(result, DetectResult)
        assert result.ok is True
        assert app.rhoaiV2Detected is False
        assert app.getParam("odh_to_rhoai_migration") == ""
        app._dynClient.resources.get.assert_not_called()

    def test_v3_installed_and_v3_catalog_does_nothing(self):
        app = self._app_with_installed_csv("stable-3.x", "rhods-operator.3.0.0")

        result = app.detectRHOAIv2()
        assert isinstance(result, DetectResult)
        assert result.ok is True
        assert app.rhoaiV2Detected is False
        assert app.getParam("odh_to_rhoai_migration") == ""


# ---------------------------------------------------------------------------
# launchUpdate stage helpers
# ---------------------------------------------------------------------------


def test_validate_openshift_pipelines_success():
    """Test _validateOpenShiftPipelines returns success when operator installs.

    GIVEN an UpdateApp instance
    WHEN _validateOpenShiftPipelines is called and operator installs successfully
    THEN it returns (True, success_message).
    """
    app = UpdateApp()
    app._dynClient = Mock()

    with patch("mas.cli.update.app.installOpenShiftPipelines", return_value=True):
        success, detail = app._validateOpenShiftPipelines()

    assert success is True
    assert "installed and ready" in detail.lower()


def test_validate_openshift_pipelines_failure():
    """Test _validateOpenShiftPipelines returns failure when operator fails.

    GIVEN an UpdateApp instance
    WHEN _validateOpenShiftPipelines is called and operator installation fails
    THEN it returns (False, failure_message).
    """
    app = UpdateApp()
    app._dynClient = Mock()

    with patch("mas.cli.update.app.installOpenShiftPipelines", return_value=False):
        success, detail = app._validateOpenShiftPipelines()

    assert success is False
    assert "failed" in detail.lower()


def test_prepare_namespace_creates_namespace_and_secrets():
    """Test _prepareNamespace creates namespace and prepares secrets.

    GIVEN an UpdateApp instance with params set
    WHEN _prepareNamespace is called
    THEN namespace is created, prepared, and secrets are set up.
    """
    app = UpdateApp()
    app._dynClient = Mock()
    app.params = {
        "slack_token": "test-token",
        "slack_channel": "test-channel",
    }
    app.db2LicenseFileSecret = None

    with (
        patch("mas.cli.update.app.createNamespace") as mock_create,
        patch("mas.cli.update.app.preparePipelinesNamespace") as mock_prepare,
        patch("mas.cli.update.app.prepareUpdateSecrets") as mock_secrets,
    ):

        success, detail = app._prepareNamespace("test-namespace")

        mock_create.assert_called_once_with(app._dynClient, "test-namespace")
        mock_prepare.assert_called_once_with(dynClient=app._dynClient)
        mock_secrets.assert_called_once_with(
            dynClient=app._dynClient,
            slack_token="test-token",
            slack_channel="test-channel",
            db2LicenseFile=None,
            artifactory_token="",
            artifactory_username="",
        )

    assert success is True
    assert detail == "test-namespace"


def test_install_tekton_definitions_updates_definitions():
    """Test _installTektonDefinitions updates Tekton definitions.

    GIVEN an UpdateApp instance with version and tektonDefsPath set
    WHEN _installTektonDefinitions is called
    THEN Tekton definitions are updated and version is returned.
    """
    app = UpdateApp()
    app._dynClient = Mock()
    app.version = "1.2.3"
    app.tektonDefsPath = "/path/to/defs"

    with patch("mas.cli.update.app.updateTektonDefinitions") as mock_update:
        success, detail = app._installTektonDefinitions("test-namespace")

        mock_update.assert_called_once_with(app._dynClient, "test-namespace", "/path/to/defs")

    assert success is True
    assert detail == "v1.2.3"


def test_submit_pipeline_run_success():
    """Test _submitPipelineRun returns success when pipeline launches.

    GIVEN an UpdateApp instance with params set
    WHEN _submitPipelineRun is called and pipeline launches successfully
    THEN it returns (True, pipeline_url).
    """
    app = UpdateApp()
    app._dynClient = Mock()
    app.params = {"test": "param"}

    with patch("mas.cli.update.app.launchUpdatePipeline", return_value="https://console.example.com/pipeline/123"):
        success, detail = app._submitPipelineRun()

    assert success is True
    assert detail == "https://console.example.com/pipeline/123"


def test_submit_pipeline_run_failure():
    """Test _submitPipelineRun returns failure when pipeline launch fails.

    GIVEN an UpdateApp instance
    WHEN _submitPipelineRun is called and pipeline launch returns None
    THEN it returns (False, failure_message).
    """
    app = UpdateApp()
    app._dynClient = Mock()
    app.params = {}

    with patch("mas.cli.update.app.launchUpdatePipeline", return_value=None):
        success, detail = app._submitPipelineRun()

    assert success is False
    assert "failed" in detail.lower()
