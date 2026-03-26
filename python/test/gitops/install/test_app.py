#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Unit tests for GitOps Install Application

These tests verify the GitOpsInstallApp class functionality including:
- Non-interactive installation with command-line arguments
- Configuration validation
- Parameter combination validation
- Error handling
- Execution flow
"""

import pytest
from unittest.mock import MagicMock, patch
from mas.cli.gitops.install.app import GitOpsInstallApp
from mas.cli.gitops.install.argParser import GitOpsArgumentParser


class TestGitOpsInstallApp:
    """Test suite for GitOpsInstallApp"""

    def test_init(self):
        """Test GitOpsInstallApp initialization"""
        app = GitOpsInstallApp()

        assert app is not None
        assert isinstance(app.arg_parser, GitOpsArgumentParser)
        assert app.executor is None

    @patch('mas.cli.gitops.install.app.GitOpsInstallExecutor')
    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_minimal_success(self, mock_halo, mock_executor_class):
        """Test successful installation with minimal required parameters"""
        # Setup mocks
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        mock_executor = MagicMock()
        mock_executor.execute.return_value = True
        mock_executor_class.return_value = mock_executor

        # Create app and run install
        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mas_workspace_id': 'testws',
                'mas_channel': '9.0.x',
                'sls_channel': '3.x'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []  # No missing params

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mas-workspace-id', 'testws',
                    '--mas-channel', '9.0.x',
                    '--sls-channel', '3.x'
                ])

        assert result == 0
        mock_executor.execute.assert_called_once()

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_missing_required_params(self, mock_halo):
        """Test installation fails when required parameters are missing"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                # Missing cluster_id and other required params
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = ['--cluster-id', '--mas-instance-id']

                result = app.install(['--account-id', 'test-account'])

        assert result == 1

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_invalid_dns_provider(self, mock_halo):
        """Test installation fails with invalid DNS provider"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'dns_provider': 'invalid-provider'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--dns-provider', 'invalid-provider'
                ])

        assert result == 1

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_mongodb_without_provider(self, mock_halo):
        """Test installation fails when mongodb_action is specified without mongo_provider"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mongodb_action': 'install',
                # Missing mongo_provider
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mongodb-action', 'install'
                ])

        assert result == 1

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_kafka_without_provider(self, mock_halo):
        """Test installation fails when kafka_action is specified without kafka_provider"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'kafka_action': 'install',
                # Missing kafka_provider
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--kafka-action', 'install'
                ])

        assert result == 1

    @patch('mas.cli.gitops.install.app.GitOpsInstallExecutor')
    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_with_mongodb(self, mock_halo, mock_executor_class):
        """Test installation with MongoDB configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        mock_executor = MagicMock()
        mock_executor.execute.return_value = True
        mock_executor_class.return_value = mock_executor

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mas_workspace_id': 'testws',
                'mas_channel': '9.0.x',
                'sls_channel': '3.x',
                'mongodb_action': 'install',
                'mongo_provider': 'aws'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mas-workspace-id', 'testws',
                    '--mas-channel', '9.0.x',
                    '--sls-channel', '3.x',
                    '--mongodb-action', 'install',
                    '--mongo-provider', 'aws'
                ])

        assert result == 0
        mock_executor.execute.assert_called_once()

    @patch('mas.cli.gitops.install.app.GitOpsInstallExecutor')
    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_with_kafka(self, mock_halo, mock_executor_class):
        """Test installation with Kafka configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        mock_executor = MagicMock()
        mock_executor.execute.return_value = True
        mock_executor_class.return_value = mock_executor

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mas_workspace_id': 'testws',
                'mas_channel': '9.0.x',
                'sls_channel': '3.x',
                'kafka_action': 'install',
                'kafka_provider': 'strimzi'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mas-workspace-id', 'testws',
                    '--mas-channel', '9.0.x',
                    '--sls-channel', '3.x',
                    '--kafka-action', 'install',
                    '--kafka-provider', 'strimzi'
                ])

        assert result == 0
        mock_executor.execute.assert_called_once()

    @patch('mas.cli.gitops.install.app.GitOpsInstallExecutor')
    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_execution_failure(self, mock_halo, mock_executor_class):
        """Test installation handles executor failure"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        mock_executor = MagicMock()
        mock_executor.execute.return_value = False  # Execution fails
        mock_executor_class.return_value = mock_executor

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mas_workspace_id': 'testws',
                'mas_channel': '9.0.x',
                'sls_channel': '3.x'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mas-workspace-id', 'testws',
                    '--mas-channel', '9.0.x',
                    '--sls-channel', '3.x'
                ])

        assert result == 1

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_keyboard_interrupt(self, mock_halo):
        """Test installation handles keyboard interrupt gracefully"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.side_effect = KeyboardInterrupt()

            result = app.install(['--account-id', 'test-account'])

        assert result == 130

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_unexpected_exception(self, mock_halo):
        """Test installation handles unexpected exceptions"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.side_effect = Exception("Unexpected error")

            result = app.install(['--account-id', 'test-account'])

        assert result == 1

    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_system_exit_from_help(self, mock_halo):
        """Test installation handles SystemExit from --help"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.side_effect = SystemExit(0)

            with pytest.raises(SystemExit) as exc_info:
                app.install(['--help'])

            assert exc_info.value.code == 0

    @patch('mas.cli.gitops.install.app.GitOpsInstallExecutor')
    @patch('mas.cli.gitops.install.app.Halo')
    def test_install_with_all_dependencies(self, mock_halo, mock_executor_class):
        """Test installation with all dependency configurations"""
        mock_spinner = MagicMock()
        mock_halo.return_value = mock_spinner

        mock_executor = MagicMock()
        mock_executor.execute.return_value = True
        mock_executor_class.return_value = mock_executor

        app = GitOpsInstallApp()

        with patch.object(app.arg_parser, 'parse_args') as mock_parse:
            mock_parse.return_value = {
                'account_id': 'test-account',
                'cluster_id': 'test-cluster',
                'mas_instance_id': 'testinst',
                'mas_workspace_id': 'testws',
                'mas_channel': '9.0.x',
                'sls_channel': '3.x',
                'mongodb_action': 'install',
                'mongo_provider': 'aws',
                'kafka_action': 'install',
                'kafka_provider': 'strimzi',
                'cos_action': 'install'
            }

            with patch.object(app.arg_parser, 'validate_required_params') as mock_validate:
                mock_validate.return_value = []

                result = app.install([
                    '--account-id', 'test-account',
                    '--cluster-id', 'test-cluster',
                    '--mas-instance-id', 'testinst',
                    '--mas-workspace-id', 'testws',
                    '--mas-channel', '9.0.x',
                    '--sls-channel', '3.x',
                    '--mongodb-action', 'install',
                    '--mongo-provider', 'aws',
                    '--kafka-action', 'install',
                    '--kafka-provider', 'strimzi',
                    '--cos-action', 'install'
                ])

        assert result == 0
        mock_executor.execute.assert_called_once()

    def test_validate_parameter_combinations_valid_dns(self):
        """Test parameter validation with valid DNS provider"""
        app = GitOpsInstallApp()
        app.params = {
            'dns_provider': 'cloudflare'
        }

        result = app._validate_parameter_combinations()
        assert result is True

    def test_validate_parameter_combinations_invalid_dns(self):
        """Test parameter validation with invalid DNS provider"""
        app = GitOpsInstallApp()
        app.params = {
            'dns_provider': 'invalid'
        }

        result = app._validate_parameter_combinations()
        assert result is False

    def test_log_configuration_summary(self):
        """Test configuration summary logging"""
        app = GitOpsInstallApp()
        app.params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_workspace_id': 'testws',
            'mas_channel': '9.0.x',
            'ibm_entitlement_key': 'secret-key',  # Should be redacted
            'github_token': 'secret-token'  # Should be redacted
        }

        # Should not raise any exceptions
        app._log_configuration_summary()


def test_main_function():
    """Test the main entry point function"""
    with patch('mas.cli.gitops.install.app.GitOpsInstallApp') as mock_app_class:
        mock_app = MagicMock()
        mock_app.install.return_value = 0
        mock_app_class.return_value = mock_app

        from mas.cli.gitops.install.app import main

        with pytest.raises(SystemExit) as exc_info:
            main(['--account-id', 'test'])

        assert exc_info.value.code == 0
        mock_app.install.assert_called_once()

# Made with Bob
