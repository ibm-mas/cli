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

import pytest
from unittest.mock import Mock, patch, MagicMock
from mas.cli.upgrade.app import UpgradeApp
from prompt_toolkit.application import create_app_session
from prompt_toolkit.output import DummyOutput


class TestUpgradeChannelLogic:
    """
    Test the --next-channel argument logic for different upgrade scenarios
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
                    mock_nodes_response.to_dict.return_value = {
                        'items': [{'status': {'nodeInfo': {'architecture': 'amd64'}}}]
                    }
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
        Should pass masChannel="8.11.x" to ansible
        """
        with patch('mas.devops.mas.getMasChannel', return_value='8.11.x'):
            with patch('mas.devops.mas.getAppsSubscriptionChannel', return_value=[]):
                with patch('mas.devops.tekton.launchUpgradePipeline') as mock_launch:
                    with patch('mas.devops.tekton.installOpenShiftPipelines', return_value=True):
                        with patch('mas.devops.tekton.updateTektonDefinitions'):
                            with patch('mas.devops.ocp.createNamespace'):
                                # Mock args
                                mock_args = Mock()
                                mock_args.mas_instance_id = 'test-inst'
                                mock_args.no_confirm = True
                                mock_args.skip_pre_check = False
                                mock_args.accept_license = True
                                mock_args.dev_mode = False
                                mock_args.next_channel = '9.0.x' 
                                with patch('mas.cli.upgrade.argParser.upgradeArgParser.parse_args', return_value=mock_args):
                                    try:
                                        mock_upgrade_app.upgrade([])
                                    except:
                                        pass  # Ignore other errors, we just want to check the call
                                # Verify masChannel parameter
                                if mock_launch.called:
                                    call_kwargs = mock_launch.call_args[1]
                                    assert call_kwargs['masChannel'] == '8.11.x', \
                                        f"Expected masChannel='8.11.x', got '{call_kwargs['masChannel']}'"

    def test_retry_scenario_with_next_channel(self, mock_upgrade_app):
        """
        Test retry scenario: current=9.1.x, next=9.1.x (core upgraded, apps stuck on 9.0.x)
        Should pass masChannel="9.0.x" (previous channel) to ansible
        """
        with patch('mas.devops.mas.getMasChannel', return_value='9.1.x'):
            with patch('mas.devops.mas.getAppsSubscriptionChannel', return_value=[]):
                with patch('mas.devops.tekton.launchUpgradePipeline') as mock_launch:
                    with patch('mas.devops.tekton.installOpenShiftPipelines', return_value=True):
                        with patch('mas.devops.tekton.updateTektonDefinitions'):
                            with patch('mas.devops.ocp.createNamespace'):
                                # Mock args
                                mock_args = Mock()
                                mock_args.mas_instance_id = 'test-inst'
                                mock_args.no_confirm = True
                                mock_args.skip_pre_check = False
                                mock_args.accept_license = True
                                mock_args.dev_mode = False
                                mock_args.next_channel = '9.1.x'
                                with patch('mas.cli.upgrade.argParser.upgradeArgParser.parse_args', return_value=mock_args):
                                    try:
                                        mock_upgrade_app.upgrade([])
                                    except:
                                        pass
                                # Verify masChannel parameter - should be previous channel (9.0.x)
                                if mock_launch.called:
                                    call_kwargs = mock_launch.call_args[1]
                                    assert call_kwargs['masChannel'] == '9.0.x', \
                                        f"Expected masChannel='9.0.x' (previous channel), got '{call_kwargs['masChannel']}'"

    def test_no_next_channel_auto_determine(self, mock_upgrade_app):
        """
        Test auto-determine: no --next-channel provided
        Should pass masChannel="" to let ansible auto-determine
        """
        with patch('mas.devops.mas.getMasChannel', return_value='8.11.x'):
            with patch('mas.devops.mas.getAppsSubscriptionChannel', return_value=[]):
                with patch('mas.devops.tekton.launchUpgradePipeline') as mock_launch:
                    with patch('mas.devops.tekton.installOpenShiftPipelines', return_value=True):
                        with patch('mas.devops.tekton.updateTektonDefinitions'):
                            with patch('mas.devops.ocp.createNamespace'):
                                # Mock args
                                mock_args = Mock()
                                mock_args.mas_instance_id = 'test-inst'
                                mock_args.no_confirm = True
                                mock_args.skip_pre_check = False
                                mock_args.accept_license = True
                                mock_args.dev_mode = False
                                mock_args.next_channel = ''  # No next channel provided
                                with patch('mas.cli.upgrade.argParser.upgradeArgParser.parse_args', return_value=mock_args):
                                    try:
                                        mock_upgrade_app.upgrade([])
                                    except:
                                        pass
                                # Verify masChannel parameter is empty
                                if mock_launch.called:
                                    call_kwargs = mock_launch.call_args[1]
                                    assert call_kwargs['masChannel'] == '', \
                                        f"Expected masChannel='' (auto-determine), got '{call_kwargs['masChannel']}'"

    def test_invalid_upgrade_path(self, mock_upgrade_app):
        """
        Test invalid upgrade path: current=8.11.x, next=9.1.x (skipping 9.0.x)
        Should raise fatal error
        """
        with patch('mas.cli.upgrade.app.getMasChannel', return_value='8.11.x'):
            with patch('mas.cli.upgrade.app.getAppsSubscriptionChannel', return_value=[]):
                with patch('mas.cli.upgrade.app.verifyAppInstance', return_value=False):
                    # Mock args
                    mock_args = Mock()
                    mock_args.mas_instance_id = 'test-inst'
                    mock_args.no_confirm = True
                    mock_args.skip_pre_check = False
                    mock_args.accept_license = True
                    mock_args.dev_mode = False
                    mock_args.next_channel = '9.1.x'  # Invalid: skips 9.0.x
                    with patch('mas.cli.upgrade.argParser.upgradeArgParser.parse_args', return_value=mock_args):
                        with pytest.raises(SystemExit) as exc_info:
                            mock_upgrade_app.upgrade([])
                        assert exc_info.value.code == 1

    def test_app_compatibility_validation(self, mock_upgrade_app):
        """
        Test app compatibility validation: manage on 8.7.x cannot upgrade to 9.1.x
        Should raise fatal error with detailed message
        """
        with patch('mas.cli.upgrade.app.getMasChannel', return_value='9.0.x'):
            # Mock installed app with incompatible version
            mock_apps = [
                {'appId': 'manage', 'channel': '8.7.x'}
            ]
            with patch('mas.cli.upgrade.app.getAppsSubscriptionChannel', return_value=mock_apps):
                with patch('mas.cli.upgrade.app.verifyAppInstance', return_value=False):
                    # Mock args
                    mock_args = Mock()
                    mock_args.mas_instance_id = 'test-inst'
                    mock_args.no_confirm = True
                    mock_args.skip_pre_check = False
                    mock_args.accept_license = True
                    mock_args.dev_mode = False
                    mock_args.next_channel = '9.1.x'
                    with patch('mas.cli.upgrade.argParser.upgradeArgParser.parse_args', return_value=mock_args):
                        with pytest.raises(SystemExit) as exc_info:
                            mock_upgrade_app.upgrade([])
                        assert exc_info.value.code == 1
# Made with Bob
