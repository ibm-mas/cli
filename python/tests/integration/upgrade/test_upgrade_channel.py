#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/licenses/v10.html
#
# *****************************************************************************

import pytest
from unittest.mock import Mock, patch
from mas.cli.upgrade.app import UpgradeApp
from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


def _mock_args(next_channel):
    """Build CLI args for the classic upgrade() flow.

    Every argument the flow reads is given a realistic value: auto-Mock
    attributes leak into the generated command string and the HTML output
    (an ExpatError) long before the launch.
    """
    args = Mock()
    args.mas_instance_id = "test-inst"
    args.no_confirm = True
    args.skip_pre_check = False
    args.accept_license = True
    args.dev_mode = False
    args.next_channel = next_channel
    args.storage_pipeline = None
    args.storage_accessmode = None
    args.storage_class_rwo = None
    args.storage_class_rwx = None
    args.image_pull_policy = None
    args.olm_approval_timeout = None
    return args


def _run_upgrade(app, next_channel, current_channel, installed_apps=None):
    """Run the classic upgrade() flow through to the PipelineRun submission.

    Patches every cluster-query function where upgrade/app.py binds it
    (``mas.cli.upgrade.app.*`` — patching the defining module has no effect
    on names imported by value) and returns the launchUpgradePipeline mock
    for call assertions.
    """
    if installed_apps is None:
        installed_apps = []
    with (
        patch("mas.cli.upgrade.app.getMasChannel", return_value=current_channel),
        patch("mas.cli.upgrade.app.getAppsSubscriptionChannel", return_value=installed_apps),
        patch("mas.cli.upgrade.app.lookupPipelineStorageClass", return_value=("ocs-sc", "ReadWriteMany")),
        patch("mas.cli.upgrade.app.getPermissionMode", return_value="cluster"),
        patch("mas.cli.upgrade.app.evaluatePreinstallRBACAccess", return_value=False),
        patch("mas.cli.upgrade.app.getWorkspaceId", return_value=None),
        # Manage is installed (its subscription channel is what the scenario
        # varies) so the 9.1.x Manage Foundation branch is not taken
        patch("mas.cli.upgrade.app.verifyAppInstance", return_value=True),
        patch("mas.cli.upgrade.app.launchUpgradePipeline", return_value="https://example.com/pipelinerun") as mock_launch,
        patch("mas.cli.upgrade.app.installOpenShiftPipelines", return_value=True),
        patch("mas.cli.upgrade.app.updateTektonDefinitions"),
        patch("mas.cli.upgrade.app.createNamespace"),
        # Namespace preparation walks a 30-iteration PVC force-delete loop
        # against the mock client — it is infrastructure, not the behaviour
        # under test
        patch("mas.cli.upgrade.app.preparePipelinesNamespace"),
        patch("mas.cli.upgrade.app.prepareUpgradeSecrets"),
        patch("mas.cli.upgrade.argParser.upgradeArgParser.parse_args", return_value=_mock_args(next_channel)),
    ):
        app.upgrade([])
    return mock_launch


class TestUpgradeChannelLogic:
    """
    Test the mas_channel PipelineRun param for different upgrade scenarios.

    mas_channel is the upgrade's TARGET channel (the channel we are upgrading
    TO) — matching the suite_upgrade role's semantics, where an unset value
    auto-selects the next release and an explicit value is used as-is.
    """

    @pytest.fixture
    def mock_upgrade_app(self):
        """Create a mock UpgradeApp with necessary attributes"""
        with create_app_session(output=DummyOutput()):
            app = UpgradeApp()
            app.noConfirm = True
            app.skipPreCheck = False
            app.licenseAccepted = True
            app.devMode = False
            # Mock the underlying _dynClient attribute (dynamicClient is a property)
            mock_client = Mock()
            # Create a function to return different mocks based on the kind parameter

            def mock_resources_get(api_version=None, kind=None):
                if kind == "Node":
                    # Mock for getNodes
                    mock_nodes_api = Mock()
                    mock_nodes_response = Mock()
                    mock_nodes_response.to_dict.return_value = {"items": [{"status": {"nodeInfo": {"architecture": "amd64"}}}]}
                    mock_nodes_api.get.return_value = mock_nodes_response
                    return mock_nodes_api
                elif kind == "Subscription":
                    # Mock for getSubscription
                    mock_sub_api = Mock()
                    mock_sub_response = Mock()
                    mock_sub_response.items = []  # Empty list for subscriptions
                    mock_sub_api.get.return_value = mock_sub_response
                    return mock_sub_api
                elif kind == "ImageDigestMirrorSet":
                    # Mock for isAirgapInstall
                    mock_idms_api = Mock()
                    mock_idms_response = Mock()
                    mock_idms_response.items = []  # Empty list - not airgap
                    mock_idms_api.get.return_value = mock_idms_response
                    return mock_idms_api
                else:
                    # Default mock
                    return Mock()

            mock_client.resources.get.side_effect = mock_resources_get
            app._dynClient = mock_client
            app.params = {}
            return app

    def test_regular_upgrade_with_next_channel(self, mock_upgrade_app):
        """
        Test regular upgrade: current=8.11.x, next=9.0.x
        mas_channel is the target channel (9.0.x)
        """
        mock_launch = _run_upgrade(mock_upgrade_app, next_channel="9.0.x", current_channel="8.11.x")

        mock_launch.assert_called_once()
        params = mock_launch.call_args[1]["params"]
        assert params["mas_channel"] == "9.0.x", f"Expected mas_channel='9.0.x' (target), got '{params['mas_channel']}'"
        assert params["mas_instance_id"] == "test-inst"

    def test_retry_scenario_with_next_channel(self, mock_upgrade_app):
        """
        Test retry scenario: current=9.1.x, next=9.1.x (core upgraded, apps stuck on 9.0.x)
        mas_channel is the target channel (9.1.x): the suite_upgrade role recognises
        core is already on it and the app upgrade tasks bring the apps up to it
        """
        mock_launch = _run_upgrade(
            mock_upgrade_app,
            next_channel="9.1.x",
            current_channel="9.1.x",
            installed_apps=[{"appId": "manage", "channel": "9.0.x"}],
        )

        mock_launch.assert_called_once()
        params = mock_launch.call_args[1]["params"]
        assert params["mas_channel"] == "9.1.x", f"Expected mas_channel='9.1.x' (target), got '{params['mas_channel']}'"

    def test_no_next_channel_auto_determine(self, mock_upgrade_app):
        """
        Test auto-determine: no --next-channel provided
        The target is derived from the effective current channel (8.11.x), so
        mas_channel is the next release (9.0.x)
        """
        mock_launch = _run_upgrade(mock_upgrade_app, next_channel="", current_channel="8.11.x")

        mock_launch.assert_called_once()
        params = mock_launch.call_args[1]["params"]
        assert params["mas_channel"] == "9.0.x", f"Expected mas_channel='9.0.x' (derived target), got '{params['mas_channel']}'"

    def test_invalid_upgrade_path(self, mock_upgrade_app):
        """
        Test invalid upgrade path: current=8.11.x, next=9.1.x (skipping 9.0.x)
        Should raise fatal error
        """
        with patch("mas.cli.upgrade.app.getMasChannel", return_value="8.11.x"):
            with patch("mas.cli.upgrade.app.getAppsSubscriptionChannel", return_value=[]):
                with patch("mas.cli.upgrade.app.verifyAppInstance", return_value=False):
                    # Mock args
                    mock_args = _mock_args("9.1.x")  # Invalid: skips 9.0.x
                    with patch("mas.cli.upgrade.argParser.upgradeArgParser.parse_args", return_value=mock_args):
                        with pytest.raises(SystemExit) as exc_info:
                            mock_upgrade_app.upgrade([])
                        assert exc_info.value.code == 1

    def test_app_compatibility_validation(self, mock_upgrade_app):
        """
        Test app compatibility validation: manage on 8.7.x cannot upgrade to 9.1.x
        Should raise fatal error with detailed message
        """
        with patch("mas.cli.upgrade.app.getMasChannel", return_value="9.0.x"):
            # Mock installed app with incompatible version
            mock_apps = [{"appId": "manage", "channel": "8.7.x"}]
            with patch("mas.cli.upgrade.app.getAppsSubscriptionChannel", return_value=mock_apps):
                with patch("mas.cli.upgrade.app.verifyAppInstance", return_value=False):
                    # Mock args
                    mock_args = _mock_args("9.1.x")
                    with patch("mas.cli.upgrade.argParser.upgradeArgParser.parse_args", return_value=mock_args):
                        with pytest.raises(SystemExit) as exc_info:
                            mock_upgrade_app.upgrade([])
                        assert exc_info.value.code == 1

    def test_upgrade_from_9_2_x_to_9_3_x_feature(self, mock_upgrade_app):
        """
        Test upgrade from 9.2.x to 9.3.x-feature with explicit --next-channel
        mas_channel is the target channel (9.3.x-feature)
        """
        mock_launch = _run_upgrade(mock_upgrade_app, next_channel="9.3.x-feature", current_channel="9.2.x")

        mock_launch.assert_called_once()
        params = mock_launch.call_args[1]["params"]
        assert params["mas_channel"] == "9.3.x-feature", f"Expected mas_channel='9.3.x-feature' (target), got '{params['mas_channel']}'"

    def test_upgrade_from_9_2_x_auto_determine_next_channel(self, mock_upgrade_app):
        """
        Test upgrade from 9.2.x without --next-channel resolves to 9.3.x-feature
        """
        mock_launch = _run_upgrade(mock_upgrade_app, next_channel="", current_channel="9.2.x")

        assert mock_upgrade_app.nextChannel == "9.3.x-feature"
        mock_launch.assert_called_once()
        params = mock_launch.call_args[1]["params"]
        assert params["mas_channel"] == "9.3.x-feature"
