# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for UpdateApp stage methods."""

from unittest.mock import Mock, patch


def test_validate_openshift_pipelines_success():
    """Test _validateOpenShiftPipelines returns success when operator installs.

    GIVEN an UpdateApp instance
    WHEN _validateOpenShiftPipelines is called and operator installs successfully
    THEN it returns (True, success_message).
    """
    from mas.cli.update.app import UpdateApp

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
    from mas.cli.update.app import UpdateApp

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
    from mas.cli.update.app import UpdateApp

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
        )

    assert success is True
    assert detail == "test-namespace"


def test_install_tekton_definitions_updates_definitions():
    """Test _installTektonDefinitions updates Tekton definitions.

    GIVEN an UpdateApp instance with version and tektonDefsPath set
    WHEN _installTektonDefinitions is called
    THEN Tekton definitions are updated and version is returned.
    """
    from mas.cli.update.app import UpdateApp

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
    from mas.cli.update.app import UpdateApp

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
    from mas.cli.update.app import UpdateApp

    app = UpdateApp()
    app._dynClient = Mock()
    app.params = {}

    with patch("mas.cli.update.app.launchUpdatePipeline", return_value=None):
        success, detail = app._submitPipelineRun()

    assert success is False
    assert "failed" in detail.lower()
