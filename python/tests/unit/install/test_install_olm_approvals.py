#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""
Unit tests for OLM install plan approval support on the install command.

In install the user is informing the CLI how to set things up, so the mode
is a flag (--olm-approval-mode) with an OLM_APPROVAL_MODE environment
fallback, plus an optional --olm-approval-timeout. These tests cover the
parser surface, the wizard prompt and the non-interactive command round-trip.
"""

from unittest.mock import MagicMock

import pytest

from mas.cli.common.olmApprovals import DEFAULT_OLM_APPROVAL_TIMEOUT
from mas.cli.install.app import InstallApp
from mas.cli.install.argParser import installArgParser
from mas.cli.install.params import optionalParams

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_app(params=None, **attrs) -> InstallApp:
    """Build a minimal InstallApp instance with real param get/set helpers."""
    app = InstallApp.__new__(InstallApp)
    app.params = params or {}
    app.printH1 = MagicMock()
    app.printDescription = MagicMock()
    for key, value in attrs.items():
        setattr(app, key, value)
    return app


# Minimal wizard state for buildCommand, mirroring the harness in
# test_install_arg_builder.py (the OLM flags need none of the app-specific
# attributes, only a complete-enough scenario for the renderer)
COMMAND_PARAMS = {
    "mas_catalog_version": "9.2.x",
    "mas_channel": "9.2.x",
    "mas_instance_id": "inst1",
    "mas_workspace_id": "ws1",
    "mas_workspace_name": "My Workspace",
    "storage_class_rwo": "rwo-sc",
    "storage_class_rwx": "rwx-sc",
    "dro_contact_email": "admin@example.com",
    "dro_contact_firstname": "Ada",
    "dro_contact_lastname": "Lovelace",
}

COMMAND_ATTRS = {
    "operationalMode": 1,
    "mas_admin_mode": "",
    "devMode": False,
    "skipGrafanaInstall": False,
    "useCliDigest": False,
    "cliDigest": None,
    "localConfigDir": None,
    "podTemplatesKeyword": None,
    "manualCertsDir": None,
    "pipelineStorageClass": "pipeline-sc",
    "pipelineStorageAccessMode": "ReadWriteMany",
    "slsLicenseFileLocal": None,
    "db2LicenseFileLocal": None,
    "facilitiesPropertiesFileLocal": None,
    "aiserviceTenantSchedulingConfigFileLocal": None,
    "aiserviceTenantOperatorConfigFileLocal": None,
    "installAssist": False,
    "installIoT": False,
    "installMonitor": False,
    "installManage": False,
    "installOptimizer": False,
    "installPredict": False,
    "installInspection": False,
    "installFacilities": False,
    "installAIService": False,
    "installMcpi": False,
    "installArcgis": False,
}


def make_command_app(params=None) -> InstallApp:
    """Build a minimal InstallApp whose state buildCommand can render."""
    app = InstallApp.__new__(InstallApp)
    app.params = dict(COMMAND_PARAMS)
    app.params.update(params or {})
    for key, value in COMMAND_ATTRS.items():
        setattr(app, key, value)
    return app


# ---------------------------------------------------------------------------
# Parser surface
# ---------------------------------------------------------------------------


class TestInstallOlmApprovalFlags:
    """Tests for the --olm-approval-mode / --olm-approval-timeout flags."""

    @pytest.mark.parametrize("mode", ["Automatic", "Manual"])
    def test_mode_accepts_valid_choices(self, mode):
        args = installArgParser.parse_args(["--olm-approval-mode", mode])
        assert args.olm_approval_mode == mode

    def test_mode_rejects_invalid_choice(self):
        with pytest.raises(SystemExit):
            installArgParser.parse_args(["--olm-approval-mode", "banana"])

    def test_timeout_parses_as_int(self):
        args = installArgParser.parse_args(["--olm-approval-timeout", "300"])
        assert args.olm_approval_timeout == 300

    def test_flags_default_to_none(self):
        args = installArgParser.parse_args([])
        assert args.olm_approval_mode is None
        assert args.olm_approval_timeout is None

    def test_params_are_optional_pipelinerun_params(self):
        """Both params flow through the optionalParams passthrough when set."""
        assert "olm_approval_mode" in optionalParams
        assert "olm_approval_timeout" in optionalParams


# ---------------------------------------------------------------------------
# Wizard prompt
# ---------------------------------------------------------------------------


class TestInstallOlmApprovalPrompt:
    """Tests for the interactive configOLMApprovals prompt."""

    def test_manual_selection_prompts_for_timeout(self):
        """GIVEN the user selects Manual in the wizard
        WHEN configOLMApprovals runs
        THEN the timeout is prompted with the collection default of 7200s
        """

        def selectManual(message, options, param=None, default=None):
            app.setParam(param, "Manual")
            return "Manual"

        app = make_app()
        app.promptForSelect = MagicMock(side_effect=selectManual)
        app.promptForInt = MagicMock(return_value=7200)

        app.configOLMApprovals()

        assert app.getParam("olm_approval_mode") == "Manual"
        app.promptForInt.assert_called_once()
        assert app.promptForInt.call_args.kwargs["default"] == DEFAULT_OLM_APPROVAL_TIMEOUT

    def test_automatic_selection_skips_timeout_prompt(self):
        """GIVEN the user selects Automatic in the wizard
        WHEN configOLMApprovals runs
        THEN no timeout is prompted (it only applies to Manual mode)
        """

        def selectAutomatic(message, options, param=None, default=None):
            app.setParam(param, "Automatic")
            return "Automatic"

        app = make_app()
        app.promptForSelect = MagicMock(side_effect=selectAutomatic)
        app.promptForInt = MagicMock()

        app.configOLMApprovals()

        assert app.getParam("olm_approval_mode") == "Automatic"
        app.promptForInt.assert_not_called()

    def test_resolved_mode_is_the_pre_selected_choice(self):
        """GIVEN the mode was already resolved from the flag or environment
        WHEN configOLMApprovals runs
        THEN the select list offers that mode as the pre-selected choice
        """
        app = make_app({"olm_approval_mode": "Manual"})
        app.promptForSelect = MagicMock(return_value="Manual")
        app.promptForInt = MagicMock(return_value=7200)

        app.configOLMApprovals()

        assert app.promptForSelect.call_args.kwargs["default"] == "Manual"

    def test_unresolved_mode_defaults_to_automatic(self):
        """GIVEN no mode was resolved before the wizard prompt
        WHEN configOLMApprovals runs
        THEN Automatic is the pre-selected choice
        """
        app = make_app()
        app.promptForSelect = MagicMock(return_value="Automatic")
        app.promptForInt = MagicMock()

        app.configOLMApprovals()

        assert app.promptForSelect.call_args.kwargs["default"] == "Automatic"
        app.promptForInt.assert_not_called()

    def test_resolved_timeout_is_the_prompt_default(self):
        """GIVEN a timeout was already resolved from the flag or environment
        WHEN Manual is selected in the wizard
        THEN the timeout prompt offers the resolved value, not 7200
        """

        def selectManual(message, options, param=None, default=None):
            app.setParam(param, "Manual")
            return "Manual"

        app = make_app({"olm_approval_mode": "Manual", "olm_approval_timeout": "300"})
        app.promptForSelect = MagicMock(side_effect=selectManual)
        app.promptForInt = MagicMock(return_value=300)

        app.configOLMApprovals()

        assert app.promptForInt.call_args.kwargs["default"] == 300

    def test_cancelled_dialog_aborts_the_install(self):
        """GIVEN the user cancels the selection dialog (Esc)
        WHEN configOLMApprovals runs
        THEN the install is aborted
        """
        app = make_app()
        app.promptForSelect = MagicMock(return_value=None)

        with pytest.raises(SystemExit):
            app.configOLMApprovals()


# ---------------------------------------------------------------------------
# Non-interactive command round-trip
# ---------------------------------------------------------------------------


class TestInstallOlmApprovalCommand:
    """Tests for the generated non-interactive install command."""

    def test_command_carries_olm_params(self):
        """GIVEN the wizard resolved Manual mode with a timeout
        WHEN the non-interactive command is generated
        THEN both flags are carried so the run is repeatable
        """
        app = make_command_app({"olm_approval_mode": "Manual", "olm_approval_timeout": "300"})
        command = app.buildCommand()

        assert "--olm-approval-mode Manual" in command
        assert "--olm-approval-timeout 300" in command

    def test_command_round_trips_through_the_parser(self):
        """GIVEN a generated command carrying the OLM flags
        WHEN it is re-parsed by the real install parser
        THEN the flag values round-trip
        """
        import shlex

        app = make_command_app({"olm_approval_mode": "Manual", "olm_approval_timeout": "300"})
        commandLines = [line for line in app.buildCommand().splitlines() if not line.startswith("export ")]
        command = "\n".join(commandLines).replace(" \\\n", " ").replace("\\\n", " ")
        tokens = shlex.split(command)
        assert tokens[:2] == ["mas", "install"]

        args = installArgParser.parse_args(tokens[2:])
        assert args.olm_approval_mode == "Manual"
        assert args.olm_approval_timeout == 300

    def test_command_omits_unset_olm_params(self):
        """GIVEN no approval mode or timeout was chosen
        WHEN the non-interactive command is generated
        THEN neither flag appears (the pipeline defaults apply)
        """
        app = make_command_app({})
        command = app.buildCommand()

        assert "--olm-approval-mode" not in command
        assert "--olm-approval-timeout" not in command
