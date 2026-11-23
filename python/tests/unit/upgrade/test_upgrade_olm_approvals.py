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
Unit tests for OLM install plan approval support on the upgrade command.

mas upgrade detects the approval mode over the instance's own namespaces
(mas-{instance_id}-*), not the whole cluster: the upgrade is scoped to those
namespaces and even within them the core subscription cannot be assumed to
represent the applications. These tests cover the scoped detection and the
--olm-approval-timeout flag plumbing.
"""

from unittest.mock import MagicMock, patch

from mas.cli.upgrade.app import UpgradeApp
from mas.cli.upgrade.argParser import upgradeArgParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_app() -> UpgradeApp:
    """Build a minimal UpgradeApp instance with real param get/set helpers."""
    app = UpgradeApp.__new__(UpgradeApp)
    app.params = {}
    app.olmApprovalStatus = None
    app._dynClient = MagicMock()
    return app


def make_command_app(params=None) -> UpgradeApp:
    """Build a minimal UpgradeApp whose state buildCommand can render."""
    app = UpgradeApp.__new__(UpgradeApp)
    app.params = params or {}
    app.masInstanceId = "inst1"
    app.nextChannel = "9.1.x"
    app.pipelineStorageClass = "pipeline-sc"
    app.pipelineStorageAccessMode = "ReadWriteMany"
    app.skipPreCheck = False
    app.devMode = False
    app.licenseAccepted = False
    return app


def detectionResult(approvalMode, counts=None, namespaces=None, subscriptions=0):
    """Build a getClusterApprovalMode-style result dict."""
    return {
        "approvalMode": approvalMode,
        "counts": counts or {},
        "namespaces": namespaces or [],
        "subscriptions": subscriptions,
    }


# ---------------------------------------------------------------------------
# Detection (mode is detected over the instance's namespaces, not chosen)
# ---------------------------------------------------------------------------


class TestUpgradeOlmApprovalDetection:
    """Tests for UpgradeApp.detectOLMApprovalMode / olmApprovalSummary."""

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_detection_is_scoped_to_the_instance_namespaces(self, mock_detect):
        """GIVEN an instance is being upgraded
        WHEN the approval mode is detected
        THEN only the mas-{instance_id}- namespaces are inspected (the core
        subscription alone can never represent the applications)
        """
        mock_detect.return_value = detectionResult("Manual", {"Manual": 8}, ["mas-inst1-core"], 8)
        app = make_app()

        app.detectOLMApprovalMode(namespacePrefix="mas-inst1-")

        mock_detect.assert_called_once()
        assert mock_detect.call_args.kwargs == {"namespacePrefix": "mas-inst1-"}
        assert app.getParam("olm_approval_mode") == "Manual"
        assert "wait for your approval" in app.olmApprovalSummary()

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_mixed_instance_namespaces_treated_as_manual(self, mock_detect):
        """GIVEN the instance namespaces contain both modes
        WHEN the approval mode is detected
        THEN Mixed is treated as Manual with the counts reported
        """
        mock_detect.return_value = detectionResult("Mixed", {"Automatic": 2, "Manual": 6}, ["mas-inst1-core", "mas-inst1-manage"], 8)
        app = make_app()

        app.detectOLMApprovalMode(namespacePrefix="mas-inst1-")

        assert app.getParam("olm_approval_mode") == "Manual"
        summary = app.olmApprovalSummary()
        assert "2 Automatic" in summary
        assert "6 Manual" in summary
        assert "treating as Manual" in summary

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_automatic_instance_namespaces(self, mock_detect):
        """GIVEN every subscription in the instance namespaces is Automatic
        WHEN the approval mode is detected
        THEN olm_approval_mode is set to Automatic
        """
        mock_detect.return_value = detectionResult("Automatic", {"Automatic": 8}, ["mas-inst1-core"], 8)
        app = make_app()

        app.detectOLMApprovalMode(namespacePrefix="mas-inst1-")

        assert app.getParam("olm_approval_mode") == "Automatic"
        assert app.olmApprovalSummary() == "Automatic"


# ---------------------------------------------------------------------------
# Timeout flag plumbing
# ---------------------------------------------------------------------------


class TestUpgradeOlmApprovalTimeoutFlag:
    """Tests for the --olm-approval-timeout flag on mas upgrade."""

    def test_flag_parses_as_int(self):
        args = upgradeArgParser.parse_args(["--mas-instance-id", "inst1", "--olm-approval-timeout", "300"])
        assert args.olm_approval_timeout == 300

    def test_flag_defaults_to_none(self):
        args = upgradeArgParser.parse_args(["--mas-instance-id", "inst1"])
        assert args.olm_approval_timeout is None

    def test_command_includes_timeout_when_set(self):
        app = make_command_app({"olm_approval_timeout": "300"})
        command = app.buildCommand()

        assert "--olm-approval-timeout 300" in command

    def test_command_omits_timeout_when_unset(self):
        app = make_command_app({})
        command = app.buildCommand()

        assert "--olm-approval-timeout" not in command
