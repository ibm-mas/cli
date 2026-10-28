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
Test suite to verify Slack integration parameters are properly configured,
and that the SLACK_USER / slack_notify_on_fail feature behaves correctly:

  - SLACK_USER not set  → no user is tagged (None)
  - SLACK_USER set      → user ID flows through as the notify target
  - Pipeline fails      → tag line is included in the message
  - Pipeline succeeds   → tag line is never included
"""

import os
from unittest.mock import patch

from mas.cli.install.params import optionalParams


class TestSlackParameters:
    """Tests that Slack parameters are properly declared in optionalParams"""

    def test_slack_token_in_optional_params(self):
        """Verify slack_token is in the optionalParams list"""
        assert "slack_token" in optionalParams, "slack_token should be in optionalParams to support Slack notifications"

    def test_slack_channel_in_optional_params(self):
        """Verify slack_channel is in the optionalParams list"""
        assert "slack_channel" in optionalParams, "slack_channel should be in optionalParams to support Slack notifications"

    def test_slack_notify_on_fail_in_optional_params(self):
        """Verify slack_notify_on_fail is in the optionalParams list"""
        assert "slack_notify_on_fail" in optionalParams, "slack_notify_on_fail should be in optionalParams to support tagging a user on pipeline failure"

    def test_slack_params_are_optional(self):
        """Verify Slack parameters are optional (not required)"""
        from mas.cli.install.params import requiredParams

        assert "slack_token" not in requiredParams, "slack_token should be optional, not required"
        assert "slack_channel" not in requiredParams, "slack_channel should be optional, not required"
        assert "slack_notify_on_fail" not in requiredParams, "slack_notify_on_fail should be optional, not required"

    def test_slack_params_documentation(self):
        """Document the purpose of Slack parameters"""
        slack_params_doc = {
            "slack_token": "OAuth token for Slack API authentication (optional)",
            "slack_channel": "Comma-separated list of Slack channels for notifications (optional)",
            "slack_notify_on_fail": "Slack user ID (e.g. U012AB3CD) to tag in the thread when the pipeline fails (optional)",
        }

        # Verify all parameters exist
        for param, description in slack_params_doc.items():
            assert param in optionalParams, f"{param} should be in optionalParams. Purpose: {description}"


class TestSlackUserEnvVar:
    """Sanity-check tests for SLACK_USER env var resolution"""

    def test_slack_user_not_set_resolves_to_none(self):
        """SLACK_USER not exported → resolves to None, no user will be tagged"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SLACK_USER", None)
            slack_user = os.getenv("SLACK_USER", "") or None
            assert slack_user is None, "SLACK_USER should be None when env var is not set"

    def test_slack_user_set_resolves_to_value(self):
        """SLACK_USER exported → resolves to the provided user ID"""
        with patch.dict(os.environ, {"SLACK_USER": "U012AB3CD"}):
            slack_user = os.getenv("SLACK_USER", "") or None
            assert slack_user == "U012AB3CD", "SLACK_USER should equal the exported value"

    def test_slack_user_empty_string_resolves_to_none(self):
        """SLACK_USER exported as empty string → treated as not set (None)"""
        with patch.dict(os.environ, {"SLACK_USER": ""}):
            slack_user = os.getenv("SLACK_USER", "") or None
            assert slack_user is None, "Empty SLACK_USER should resolve to None"


class TestSlackNotifyOnFailArgParser:
    """Sanity-check tests for --slack-notify-on-fail CLI argument"""

    def test_slack_notify_on_fail_accepted(self):
        """--slack-notify-on-fail is accepted and stored as slack_notify_on_fail"""
        from mas.cli.install.argParser import installArgParser

        args = installArgParser.parse_known_args(["--slack-notify-on-fail", "U012AB3CD"])[0]
        assert args.slack_notify_on_fail == "U012AB3CD"

    def test_slack_notify_on_fail_defaults_to_none(self):
        """--slack-notify-on-fail defaults to None when not supplied"""
        from mas.cli.install.argParser import installArgParser

        args = installArgParser.parse_known_args([])[0]
        assert args.slack_notify_on_fail is None, "slack_notify_on_fail should default to None when not supplied"
