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
Test suite to verify Slack integration parameters are properly configured.

This test ensures that slack_token and slack_channel parameters are included
in the optionalParams list for the install command, allowing them to be passed
through to Tekton pipelines for Slack notifications.
"""

from mas.cli.install.params import optionalParams


class TestSlackParameters:
    """Test that Slack parameters are properly configured"""

    def test_slack_token_in_optional_params(self):
        """Verify slack_token is in the optionalParams list"""
        assert "slack_token" in optionalParams, "slack_token should be in optionalParams to support Slack notifications"

    def test_slack_channel_in_optional_params(self):
        """Verify slack_channel is in the optionalParams list"""
        assert "slack_channel" in optionalParams, "slack_channel should be in optionalParams to support Slack notifications"

    def test_slack_notify_on_fail_in_optional_params(self):
        """Verify slack_notify_on_fail is in the optionalParams list"""
        assert "slack_notify_on_fail" in optionalParams, (
            "slack_notify_on_fail should be in optionalParams to support tagging a user on pipeline failure"
        )

    def test_slack_params_are_optional(self):
        """Verify Slack parameters are optional (not required)"""
        from mas.cli.install.params import requiredParams

        assert "slack_token" not in requiredParams, "slack_token should be optional, not required"
        assert "slack_channel" not in requiredParams, "slack_channel should be optional, not required"
        assert "slack_notify_on_fail" not in requiredParams, "slack_notify_on_fail should be optional, not required"

    def test_slack_params_documentation(self):
        """Document the purpose of Slack parameters"""
        # This test serves as documentation
        slack_params_doc = {
            "slack_token": "OAuth token for Slack API authentication (optional)",
            "slack_channel": "Comma-separated list of Slack channels for notifications (optional)",
            "slack_notify_on_fail": "Slack user ID (e.g. U012AB3CD) to tag in the thread when the pipeline fails (optional)",
        }

        # Verify all parameters exist
        for param, description in slack_params_doc.items():
            assert param in optionalParams, f"{param} should be in optionalParams. Purpose: {description}"
