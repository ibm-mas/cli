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
Unit tests for OLM install plan approval support on the update command.

mas update does not ask for the approval mode: it was chosen at install time
and is a property of the cluster. These tests cover the detection mixin
(OlmApprovalDetectionMixin) as mixed into UpdateApp -- the aggregate mode is
detected over the whole cluster (the update's blast radius), reported in the
review summary, and passed to the PipelineRun with Mixed treated as Manual --
plus the --olm-approval-timeout flag plumbing.
"""

from unittest.mock import MagicMock, patch

from mas.cli.update.app import UpdateApp
from mas.cli.update.argParser import updateArgParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_app() -> UpdateApp:
    """Build a minimal UpdateApp instance with real param get/set helpers."""
    app = UpdateApp.__new__(UpdateApp)
    app.params = {}
    app.olmApprovalStatus = None
    app._dynClient = MagicMock()
    return app


def make_command_app(params=None) -> UpdateApp:
    """Build a minimal UpdateApp whose state buildCommand can render."""
    app = UpdateApp.__new__(UpdateApp)
    app.params = {"mas_catalog_version": "v9-261105-amd64"}
    app.params.update(params or {})
    app.devMode = False
    app.db2LicenseFileLocal = None
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
# Detection (mode is detected over the whole cluster, not chosen)
# ---------------------------------------------------------------------------


class TestUpdateOlmApprovalDetection:
    """Tests for UpdateApp.detectOLMApprovalMode / olmApprovalSummary."""

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_automatic_cluster_detected_and_passed(self, mock_detect):
        """GIVEN every subscription in the cluster is Automatic
        WHEN the update detects the approval mode
        THEN olm_approval_mode is set to Automatic for the PipelineRun
        """
        mock_detect.return_value = detectionResult("Automatic", {"Automatic": 40}, ["ns1"], 40)
        app = make_app()

        app.detectOLMApprovalMode()

        mock_detect.assert_called_once()
        assert mock_detect.call_args.kwargs == {"namespacePrefix": None}
        assert app.getParam("olm_approval_mode") == "Automatic"
        assert app.olmApprovalSummary() == "Automatic"

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_manual_cluster_detected_and_passed(self, mock_detect):
        """GIVEN every subscription in the cluster is Manual
        WHEN the update detects the approval mode
        THEN olm_approval_mode is set to Manual and the summary explains the wait
        """
        mock_detect.return_value = detectionResult("Manual", {"Manual": 40}, ["ns1"], 40)
        app = make_app()

        app.detectOLMApprovalMode()

        assert app.getParam("olm_approval_mode") == "Manual"
        assert "Manual" in app.olmApprovalSummary()
        assert "wait for your approval" in app.olmApprovalSummary()

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_mixed_cluster_treated_as_manual_with_counts(self, mock_detect):
        """GIVEN the cluster has both Automatic and Manual subscriptions
        WHEN the update detects the approval mode
        THEN Mixed is treated as Manual and the summary reports the counts
        """
        mock_detect.return_value = detectionResult("Mixed", {"Automatic": 40, "Manual": 2}, ["ns1", "ns2"], 42)
        app = make_app()

        app.detectOLMApprovalMode()

        assert app.getParam("olm_approval_mode") == "Manual"
        summary = app.olmApprovalSummary()
        assert summary.startswith("Mixed (")
        assert "40 Automatic" in summary
        assert "2 Manual" in summary
        assert "treating as Manual" in summary

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode")
    def test_no_subscriptions_in_scope_leaves_mode_unset(self, mock_detect):
        """GIVEN no subscriptions exist in scope
        WHEN the update detects the approval mode
        THEN olm_approval_mode stays unset (pipeline defaults apply)
        """
        mock_detect.return_value = detectionResult(None, {}, [], 0)
        app = make_app()

        app.detectOLMApprovalMode()

        assert app.getParam("olm_approval_mode") == ""
        assert "No subscriptions in scope" in app.olmApprovalSummary()

    @patch("mas.cli.common.olmApprovals.getClusterApprovalMode", side_effect=RuntimeError("api down"))
    def test_detection_failure_is_non_fatal(self, mock_detect):
        """GIVEN the detection API call fails
        WHEN the update detects the approval mode
        THEN the failure is swallowed and the mode stays unset
        """
        app = make_app()

        app.detectOLMApprovalMode()

        assert app.getParam("olm_approval_mode") == ""
        assert app.olmApprovalStatus is None
        assert "No subscriptions in scope" in app.olmApprovalSummary()

    def test_summary_before_detection(self):
        """GIVEN detection has not run (e.g. a fresh TUI app)
        WHEN the summary is requested
        THEN the no-scope placeholder is returned rather than raising
        """
        app = make_app()
        app.olmApprovalStatus = None

        assert "No subscriptions in scope" in app.olmApprovalSummary()


# ---------------------------------------------------------------------------
# Timeout flag plumbing
# ---------------------------------------------------------------------------


class TestUpdateOlmApprovalTimeoutFlag:
    """Tests for the --olm-approval-timeout flag on mas update."""

    def test_flag_parses_as_int(self):
        args = updateArgParser.parse_args(["-c", "v9-261105-amd64", "--olm-approval-timeout", "300"])
        assert args.olm_approval_timeout == 300

    def test_flag_defaults_to_none(self):
        args = updateArgParser.parse_args(["-c", "v9-261105-amd64"])
        assert args.olm_approval_timeout is None

    def test_command_includes_timeout_when_set(self):
        """GIVEN the wizard resolved an approval timeout
        WHEN the non-interactive command is generated
        THEN --olm-approval-timeout is carried (so the run is repeatable)
        """
        app = make_command_app({"olm_approval_timeout": "300"})
        command = app.buildCommand()

        assert "--olm-approval-timeout 300" in command

    def test_command_omits_timeout_when_unset(self):
        app = make_command_app({})
        command = app.buildCommand()

        assert "--olm-approval-timeout" not in command
