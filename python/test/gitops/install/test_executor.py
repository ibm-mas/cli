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
Unit tests for GitOps Install Executor

These tests verify the GitOpsInstallExecutor class functionality including:
- Execution of GitOps commands
- Parameter preparation for applications
- Environment variable handling
- Command execution flow
- Error handling
"""

from unittest.mock import MagicMock, patch
from mas.cli.gitops.install.executor import GitOpsInstallExecutor


class TestGitOpsInstallExecutor:
    """Test suite for GitOpsInstallExecutor"""

    def test_init(self):
        """Test GitOpsInstallExecutor initialization"""
        params = {'account_id': 'test', 'cluster_id': 'test'}
        executor = GitOpsInstallExecutor(params)

        assert executor is not None
        assert executor.params == params
        assert executor.spinner == 'dots'
        assert executor.success_icon == '✔'
        assert executor.failure_icon == '✖'

    def test_init_custom_icons(self):
        """Test initialization with custom spinner and icons"""
        params = {'account_id': 'test', 'cluster_id': 'test'}
        executor = GitOpsInstallExecutor(
            params,
            spinner='line',
            success_icon='✓',
            failure_icon='✗'
        )

        assert executor.spinner == 'line'
        assert executor.success_icon == '✓'
        assert executor.failure_icon == '✗'

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_minimal_success(self, mock_run, mock_halo):
        """Test successful execution with minimal configuration"""
        # Setup mocks
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should call gitops-cluster and gitops-suite at minimum
        assert mock_run.call_count >= 2

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_with_mongodb(self, mock_run, mock_halo):
        """Test execution with MongoDB configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mongodb_action': 'install',
            'mongo_provider': 'aws'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should include gitops-mongo call
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any('gitops-mongo' in str(c) for c in calls)

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_with_kafka(self, mock_run, mock_halo):
        """Test execution with Kafka configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'kafka_action': 'install',
            'kafka_provider': 'strimzi'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should include gitops-kafka call
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any('gitops-kafka' in str(c) for c in calls)

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_with_cos(self, mock_run, mock_halo):
        """Test execution with COS configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'cos_action': 'install'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should include gitops-cos call
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any('gitops-cos' in str(c) for c in calls)

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_with_efs(self, mock_run, mock_halo):
        """Test execution with EFS configuration"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'efs_action': 'install'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should include gitops-efs call
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any('gitops-efs' in str(c) for c in calls)

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_with_applications(self, mock_run, mock_halo):
        """Test execution with MAS applications"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_app_id_iot': 'iot',
            'mas_app_id_manage': 'manage'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is True
        # Should include gitops-suite-app-install and gitops-suite-app-config calls
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any('gitops-suite-app-install' in str(c) for c in calls)
        assert any('gitops-suite-app-config' in str(c) for c in calls)

    @patch('mas.cli.gitops.install.executor.Halo')
    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_command_failure(self, mock_run, mock_halo):
        """Test execution handles command failure"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Error occurred'
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is False

    @patch('mas.cli.gitops.install.executor.Halo')
    def test_execute_missing_instance_id(self, mock_halo):
        """Test execution fails when instance ID is missing"""
        mock_spinner = MagicMock()
        mock_halo.return_value.__enter__.return_value = mock_spinner

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster'
            # Missing mas_instance_id
        }

        executor = GitOpsInstallExecutor(params)
        result = executor.execute()

        assert result is False

    def test_prepare_app_params_install(self):
        """Test preparing app-specific parameters for install operation"""
        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_app_channel_MANAGE': '9.0.x',
            'db2_channel_MANAGE': '11.5.x'
        }

        executor = GitOpsInstallExecutor(params)
        app_params = executor._prepare_app_params('manage', 'install')

        assert app_params['mas_app_id'] == 'manage'
        assert app_params['mas_app_channel'] == '9.0.x'
        assert app_params['db2_channel'] == '11.5.x'

    def test_prepare_app_params_config(self):
        """Test preparing app-specific parameters for config operation"""
        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_appws_spec_yaml_IOT': 'spec.yaml'
        }

        executor = GitOpsInstallExecutor(params)
        app_params = executor._prepare_app_params('iot', 'config')

        assert app_params['mas_app_id'] == 'iot'
        assert app_params['mas_appws_spec_yaml'] == 'spec.yaml'

    def test_prepare_app_params_preserves_common(self):
        """Test that common parameters are preserved"""
        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_workspace_id': 'testws'
        }

        executor = GitOpsInstallExecutor(params)
        app_params = executor._prepare_app_params('manage', 'install')

        assert app_params['account_id'] == 'test-account'
        assert app_params['cluster_id'] == 'test-cluster'
        assert app_params['mas_instance_id'] == 'testinst'
        assert app_params['mas_workspace_id'] == 'testws'

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_env_vars(self, mock_run):
        """Test that environment variables are set correctly"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'mas_instance_id': 'testinst',
            'mas_channel': '9.0.x',
            'github_org': 'myorg',
            'github_repo': 'myrepo'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is True
        # Check that environment variables were set
        call_env = mock_run.call_args[1]['env']
        assert call_env['MAS_INSTANCE_ID'] == 'testinst'
        assert call_env['MAS_CHANNEL'] == '9.0.x'
        assert call_env['GITHUB_ORG'] == 'myorg'
        assert call_env['GITHUB_REPO'] == 'myrepo'

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_git_identity(self, mock_run):
        """Test that git identity environment variables are set"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is True
        # Check that git identity variables were set
        call_env = mock_run.call_args[1]['env']
        assert 'GIT_AUTHOR_NAME' in call_env
        assert 'GIT_AUTHOR_EMAIL' in call_env
        assert 'GIT_COMMITTER_NAME' in call_env
        assert 'GIT_COMMITTER_EMAIL' in call_env

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.requests.get')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_github_user_fetch(self, mock_get, mock_run):
        """Test fetching GitHub user identity from PAT"""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Test User',
            'email': 'test@example.com',
            'login': 'testuser'
        }
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'gitops_repo_token_secret': 'test-token'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is True
        # Check that git identity was set from GitHub API
        call_env = mock_run.call_args[1]['env']
        assert call_env['GIT_AUTHOR_NAME'] == 'Test User'
        assert call_env['GIT_AUTHOR_EMAIL'] == 'test@example.com'

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_boolean_conversion(self, mock_run):
        """Test that boolean parameters are converted to lowercase strings"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'github_push': True,
            'install_redhat_cert_manager': False
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is True
        # Check that booleans were converted to lowercase strings
        call_env = mock_run.call_args[1]['env']
        assert call_env['GITHUB_PUSH'] == 'true'
        assert call_env['INSTALL_REDHAT_CERT_MANAGER'] == 'false'

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_icr_password_from_entitlement(self, mock_run):
        """Test that ICR_PASSWORD is set from ibm_entitlement_key"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster',
            'ibm_entitlement_key': 'test-key'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is True
        # Check that ICR_PASSWORD was set from entitlement key
        call_env = mock_run.call_args[1]['env']
        assert call_env['ICR_PASSWORD'] == 'test-key'

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_gitops_command_missing_account_id(self, mock_run):
        """Test that command fails when account_id is missing"""
        params = {
            'cluster_id': 'test-cluster'
            # Missing account_id
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is False
        mock_run.assert_not_called()

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    def test_execute_gitops_command_missing_cluster_id(self, mock_run):
        """Test that command fails when cluster_id is missing"""
        params = {
            'account_id': 'test-account'
            # Missing cluster_id
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is False
        mock_run.assert_not_called()

    @patch('mas.cli.gitops.install.executor.subprocess.run')
    @patch('mas.cli.gitops.install.executor.os.environ', {})
    def test_execute_gitops_command_exception_handling(self, mock_run):
        """Test that exceptions during command execution are handled"""
        mock_run.side_effect = Exception("Command failed")

        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster'
        }

        executor = GitOpsInstallExecutor(params)
        result = executor._executeGitOpsCommand('gitops-cluster', params)

        assert result is False

# Made with Bob
