# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Unit tests for UpgradeApp.applyCliArgs and its TUI bootstrap wiring.

applyCliArgs is the arg-to-state mapping shared by the non-interactive
preamble (upgrade()) and the TUI bootstrap (serveTuiMode): optional flags
pre-set the same params and attributes in both modes, so a guided run
carries them into the PipelineRun exactly as a fully-specified command
line does.
"""

from unittest.mock import MagicMock, patch

import pytest

from mas.cli.upgrade.app import UpgradeApp
from mas.cli.upgrade.argParser import upgradeArgParser

pytestmark = pytest.mark.upgrade


def _make_app() -> UpgradeApp:
    """Build a minimal UpgradeApp in the state serveTuiMode constructs."""
    app = UpgradeApp()
    app.tuiMode = True
    app._dynClient = MagicMock()
    app._isSNO = False
    app.lookupTargetArchitecture = MagicMock()
    return app


def _parse(*argv):
    return upgradeArgParser.parse_args(args=list(argv))


@pytest.fixture(autouse=True)
def _no_approval_env(monkeypatch):
    """Keep OLM_APPROVAL_TIMEOUT out of the environment so the flag is the only input."""
    monkeypatch.delenv("OLM_APPROVAL_TIMEOUT", raising=False)


class TestApplyCliArgs:
    """Tests for the arg-to-state mapping itself."""

    def test_image_pull_policy_sets_the_param(self):
        app = _make_app()

        app.applyCliArgs(_parse("--image-pull-policy", "Always"))

        assert app.getParam("image_pull_policy") == "Always"

    def test_image_pull_policy_absent_leaves_the_param_unset(self):
        app = _make_app()

        app.applyCliArgs(_parse())

        assert app.getParam("image_pull_policy") == ""

    def test_olm_approval_timeout_sets_the_param_as_a_string(self):
        app = _make_app()

        app.applyCliArgs(_parse("--olm-approval-timeout", "600"))

        assert app.getParam("olm_approval_timeout") == "600"

    def test_invalid_olm_approval_timeout_fails_fatal(self, monkeypatch):
        """The ValueError from the resolver surfaces via fatalError.

        The flag itself is type=int in argparse, so an invalid value can
        only arrive via the OLM_APPROVAL_TIMEOUT environment variable --
        which is exactly what the resolver validates. Under tuiMode
        fatalError raises RuntimeError (the bootstrap has no screen to
        display it inline), which is the contract serveTuiMode translates
        into a clean process exit.
        """
        app = _make_app()
        monkeypatch.setenv("OLM_APPROVAL_TIMEOUT", "soon")

        with pytest.raises(RuntimeError, match="OLM_APPROVAL_TIMEOUT must be an integer"):
            app.applyCliArgs(_parse())

    def test_storage_flags_pre_populate_attributes_and_params(self):
        app = _make_app()

        app.applyCliArgs(_parse("--storage-pipeline", "ocs-cephfs", "--storage-accessmode", "ReadWriteMany", "--storage-class-rwo", "rwo-class"))

        assert app.pipelineStorageClass == "ocs-cephfs"
        assert app.pipelineStorageAccessMode == "ReadWriteMany"
        assert app.getParam("storage_class_rwo") == "rwo-class"
        assert app.getParam("storage_class_rwx") == ""

    def test_skip_pre_check_sets_attribute_and_param(self):
        app = _make_app()

        app.applyCliArgs(_parse("--skip-pre-check"))

        assert app.skipPreCheck is True
        assert app.getParam("skip_pre_check") == "true"

    def test_flow_flags_set_attributes(self):
        app = _make_app()

        app.applyCliArgs(_parse("--no-confirm", "--accept-license", "--dev-mode", "--next-channel", "9.2.x"))

        assert app.noConfirm is True
        assert app.licenseAccepted is True
        assert app.devMode is True
        assert app.nextChannel == "9.2.x"


class TestServeTuiModePassthrough:
    """Tests for the TUI bootstrap applying command-line flags to the app."""

    def test_flags_reach_the_app_the_workflow_is_built_from(self):
        """Optional flags passed to serveTuiMode are applied before the workflow is built.

        GIVEN the dispatch routed ['--image-pull-policy', 'Always'] into the TUI
        WHEN serveTuiMode runs
        THEN the workflow definition is built from an app whose params already
             carry the flag value (nothing in the workflow can lose it).
        """
        with (
            patch("mas.cli.upgrade.workflow.buildUpgradeWorkflow") as mockBuild,
            patch("mas.cli.tui.shell.TextualShell"),
        ):
            from mas.cli.tui.shell import serveTuiMode

            serveTuiMode("upgrade", ["--image-pull-policy", "Always"])

        mockBuild.assert_called_once()
        mas_app = mockBuild.call_args[0][0]
        assert mas_app.getParam("image_pull_policy") == "Always"
        assert mas_app.tuiMode is True

    def test_bare_invocation_builds_the_workflow_without_flags(self):
        with (
            patch("mas.cli.upgrade.workflow.buildUpgradeWorkflow") as mockBuild,
            patch("mas.cli.tui.shell.TextualShell"),
        ):
            from mas.cli.tui.shell import serveTuiMode

            serveTuiMode("upgrade", [])

        mockBuild.assert_called_once()
        mas_app = mockBuild.call_args[0][0]
        assert mas_app.getParam("image_pull_policy") == ""

    def test_fatal_error_at_bootstrap_exits_the_process(self, monkeypatch):
        """A fatalError during applyCliArgs becomes a clean exit, not a traceback.

        GIVEN the OLM_APPROVAL_TIMEOUT environment variable holds an invalid
            value (the flag itself is type=int, so only the env var can
            carry garbage this far)
        WHEN serveTuiMode applies the args (no screen exists yet to display
             the error inline)
        THEN the process exits with the message rather than raising
             RuntimeError out of the bootstrap.
        """
        monkeypatch.setenv("OLM_APPROVAL_TIMEOUT", "soon")
        with (
            patch("mas.cli.upgrade.workflow.buildUpgradeWorkflow") as mockBuild,
            patch("mas.cli.tui.shell.TextualShell"),
        ):
            from mas.cli.tui.shell import serveTuiMode

            with pytest.raises(SystemExit, match="OLM_APPROVAL_TIMEOUT must be an integer"):
                serveTuiMode("upgrade", [])

        # The workflow was never built: the bootstrap failed before it
        mockBuild.assert_not_called()
