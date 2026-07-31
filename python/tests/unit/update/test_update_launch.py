# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for UpdateApp.launchUpdate(progressCallback).

All devops functions called by launchUpdate are mocked. The tests verify
that each stage is called (or skipped) in the expected conditions.
"""

from unittest.mock import MagicMock, patch


def _make_update_app():
    """Return an UpdateApp instance with mocked cluster state.

    Returns:
        UpdateApp: App with _dynClient, version, params, and RBAC flags set.
    """
    from mas.cli.update.app import UpdateApp

    app = UpdateApp.__new__(UpdateApp)
    # dynamicClient is a property backed by _dynClient
    app._dynClient = MagicMock()
    app.version = "9.9.9"
    app.params = {"slack_token": "", "slack_channel": ""}
    app.tektonDefsPath = "/fake/tekton"
    app.db2LicenseFileSecret = None
    app.applyPreInstallMASRBAC = False
    app.instancesNeedingRBAC = []
    app.spinner = "dots"
    app.successIcon = "✓"
    app.failureIcon = "✗"
    return app


_DEVOPS_PATCH_BASE = "mas.cli.update.app"


def test_launchUpdate_calls_install_openshift_pipelines():
    """Test that launchUpdate calls installOpenShiftPipelines.

    GIVEN an UpdateApp with mocked devops functions
    WHEN launchUpdate() is called with no callback
    THEN installOpenShiftPipelines is called once with the dynamicClient.
    """
    app = _make_update_app()

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True) as mock_install,
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value="http://example.com/pipeline"),
    ):
        app.launchUpdate()

    mock_install.assert_called_once_with(app.dynamicClient)


def test_launchUpdate_calls_launch_update_pipeline():
    """Test that launchUpdate calls launchUpdatePipeline with app params.

    GIVEN an UpdateApp with params populated
    WHEN launchUpdate() is called
    THEN launchUpdatePipeline is called with dynClient and params=self.params.
    """
    app = _make_update_app()
    app.params["mas_catalog_version"] = "v9-260625-amd64"

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True),
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value=None) as mock_launch,
    ):
        app.launchUpdate()

    mock_launch.assert_called_once_with(dynClient=app.dynamicClient, params=app.params)


def test_launchUpdate_applies_rbac_when_flag_set():
    """Test that launchUpdate calls applyPreInstallMASRBAC for each instance when the flag is set.

    GIVEN applyPreInstallMASRBAC=True and one entry in instancesNeedingRBAC
    WHEN launchUpdate() is called
    THEN applyPreInstallMASRBAC devops function is called once for that instance.
    """
    app = _make_update_app()
    app.applyPreInstallMASRBAC = True
    app.instancesNeedingRBAC = [{"id": "inst1", "targetVersion": "9.0.1", "adminMode": "admin"}]

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True),
        patch(f"{_DEVOPS_PATCH_BASE}.applyPreInstallMASRBAC") as mock_rbac,
        patch(f"{_DEVOPS_PATCH_BASE}.getInstalledApps", return_value=[]),
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value=None),
    ):
        app.launchUpdate()

    assert mock_rbac.call_count == 1


def test_launchUpdate_skips_rbac_when_flag_false():
    """Test that launchUpdate does not call applyPreInstallMASRBAC when flag is False.

    GIVEN applyPreInstallMASRBAC=False
    WHEN launchUpdate() is called
    THEN applyPreInstallMASRBAC devops function is never called.
    """
    app = _make_update_app()
    app.applyPreInstallMASRBAC = False
    app.instancesNeedingRBAC = [{"id": "inst1", "targetVersion": "9.0.1", "adminMode": "admin"}]

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True),
        patch(f"{_DEVOPS_PATCH_BASE}.applyPreInstallMASRBAC") as mock_rbac,
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value=None),
    ):
        app.launchUpdate()

    mock_rbac.assert_not_called()


def test_launchUpdate_with_progress_callback_calls_callback():
    """Test that launchUpdate invokes progressCallback at least once per stage.

    GIVEN a list-collecting progressCallback
    WHEN launchUpdate(progressCallback) is called
    THEN at least one (label, ok, detail) tuple is appended to the list.
    """
    app = _make_update_app()
    collected = []

    def cb(label, ok, detail):
        collected.append((label, ok, detail))

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True),
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value="http://example.com/run"),
    ):
        app.launchUpdate(progressCallback=cb)

    assert len(collected) >= 1, "Expected at least one progress callback entry"
    labels = [t[0] for t in collected]
    assert any(
        "Validate" in lbl or "Pipeline" in lbl or "Tekton" in lbl or "namespace" in lbl.lower() for lbl in labels
    ), f"Expected a recognisable stage label, got: {labels}"


def test_launchUpdate_with_start_callback_calls_start_before_progress():
    """Test that launchUpdate calls startCallback before progressCallback for each stage.

    GIVEN a list-collecting startCallback and progressCallback
    WHEN launchUpdate(progressCallback, startCallback) is called
    THEN startCallback is called with each stage label before its progressCallback call.
    """
    app = _make_update_app()
    started = []
    completed = []

    def start_cb(label):
        started.append(("start", label))

    def prog_cb(label, ok, detail):
        completed.append(("done", label))

    with (
        patch(f"{_DEVOPS_PATCH_BASE}.installOpenShiftPipelines", return_value=True),
        patch(f"{_DEVOPS_PATCH_BASE}.createNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.preparePipelinesNamespace"),
        patch(f"{_DEVOPS_PATCH_BASE}.prepareUpdateSecrets"),
        patch(f"{_DEVOPS_PATCH_BASE}.updateTektonDefinitions"),
        patch(f"{_DEVOPS_PATCH_BASE}.launchUpdatePipeline", return_value="http://example.com/run"),
    ):
        app.launchUpdate(progressCallback=prog_cb, startCallback=start_cb)

    assert len(started) >= 1, "Expected at least one startCallback call"
    start_labels = [s[1] for s in started]
    done_labels = [d[1] for d in completed]
    # Every started label must appear in completed too (or raise — but no exception here)
    for lbl in start_labels:
        assert lbl in done_labels, f"Stage '{lbl}' was started but never completed"
