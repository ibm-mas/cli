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
Unit tests for GitOps Argument Parser

These tests verify the GitOpsArgumentParser class functionality including:
- Dynamic argument extraction from bash functions
- Argument grouping and organization
- Environment variable merging
- Required parameter validation
"""

import os
from unittest.mock import MagicMock, patch
from mas.cli.gitops.install.argParser import GitOpsArgumentParser
from mas.cli.gitops.install.argBuilder import Argument


class TestGitOpsArgumentParser:
    """Test suite for GitOpsArgumentParser"""

    def test_init(self):
        """Test GitOpsArgumentParser initialization"""
        parser = GitOpsArgumentParser()

        assert parser is not None
        assert parser.extractor is not None
        assert parser.parser is None

    def test_init_with_custom_functions_dir(self):
        """Test initialization with custom functions directory"""
        parser = GitOpsArgumentParser(functions_dir='/custom/path')

        assert parser.extractor.functions_dir == '/custom/path'

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_build_parser(self, mock_extractor_class):
        """Test building argument parser from bash functions"""
        # Setup mock extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        # Mock unique arguments
        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=True
            ),
            '--cluster-id': Argument(
                short_option='-c',
                long_option='--cluster-id',
                env_var='CLUSTER_ID',
                description='Cluster ID',
                required=True
            )
        }

        # Mock per-app arguments
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()
        result = parser.build_parser()

        assert result is not None
        assert parser.parser is not None
        assert parser.parser == result

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_build_parser_caching(self, mock_extractor_class):
        """Test that build_parser caches the result"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.get_unique_arguments.return_value = {}
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()
        result1 = parser.build_parser()
        result2 = parser.build_parser()

        assert result1 is result2
        # Should only call get_unique_arguments once due to caching
        assert mock_extractor.get_unique_arguments.call_count == 1

    def test_group_arguments_required(self):
        """Test grouping of required arguments"""
        parser = GitOpsArgumentParser()

        args = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=True
            ),
            '--cluster-id': Argument(
                short_option='-c',
                long_option='--cluster-id',
                env_var='CLUSTER_ID',
                description='Cluster ID',
                required=False
            )
        }

        grouped = parser._group_arguments(args)

        assert 'Required Arguments' in grouped
        assert len(grouped['Required Arguments']) == 1
        assert grouped['Required Arguments'][0].env_var == 'ACCOUNT_ID'

    def test_group_arguments_gitops(self):
        """Test grouping of GitOps configuration arguments"""
        parser = GitOpsArgumentParser()

        args = {
            '--github-org': Argument(
                short_option=None,
                long_option='--github-org',
                env_var='GITHUB_ORG',
                description='GitHub organization',
                required=False
            ),
            '--github-repo': Argument(
                short_option=None,
                long_option='--github-repo',
                env_var='GITHUB_REPO',
                description='GitHub repository',
                required=False
            )
        }

        grouped = parser._group_arguments(args)

        assert 'GitOps Configuration' in grouped
        assert len(grouped['GitOps Configuration']) == 2

    def test_group_arguments_mas(self):
        """Test grouping of MAS configuration arguments"""
        parser = GitOpsArgumentParser()

        args = {
            '--mas-instance-id': Argument(
                short_option=None,
                long_option='--mas-instance-id',
                env_var='MAS_INSTANCE_ID',
                description='MAS instance ID',
                required=False
            ),
            '--sls-channel': Argument(
                short_option=None,
                long_option='--sls-channel',
                env_var='SLS_CHANNEL',
                description='SLS channel',
                required=False
            )
        }

        grouped = parser._group_arguments(args)

        assert 'MAS Configuration' in grouped
        assert len(grouped['MAS Configuration']) == 2

    def test_group_arguments_dependencies(self):
        """Test grouping of dependency arguments"""
        parser = GitOpsArgumentParser()

        args = {
            '--mongo-provider': Argument(
                short_option=None,
                long_option='--mongo-provider',
                env_var='MONGODB_PROVIDER',
                description='MongoDB provider',
                required=False
            ),
            '--kafka-provider': Argument(
                short_option=None,
                long_option='--kafka-provider',
                env_var='KAFKA_PROVIDER',
                description='Kafka provider',
                required=False
            )
        }

        grouped = parser._group_arguments(args)

        assert 'Dependencies' in grouped
        assert len(grouped['Dependencies']) == 2

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_parse_args_from_cli(self, mock_extractor_class):
        """Test parsing arguments from command line"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=False
            )
        }
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()

        with patch.dict(os.environ, {}, clear=True):
            params = parser.parse_args(['--account-id', 'test-account'])

        assert params['account_id'] == 'test-account'

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_parse_args_from_env(self, mock_extractor_class):
        """Test parsing arguments from environment variables"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=False
            )
        }
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()

        with patch.dict(os.environ, {'ACCOUNT_ID': 'env-account'}, clear=True):
            params = parser.parse_args([])

        assert params['account_id'] == 'env-account'

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_parse_args_cli_overrides_env(self, mock_extractor_class):
        """Test that CLI arguments override environment variables"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=False
            )
        }
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()

        with patch.dict(os.environ, {'ACCOUNT_ID': 'env-account'}, clear=True):
            params = parser.parse_args(['--account-id', 'cli-account'])

        assert params['account_id'] == 'cli-account'

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_validate_required_params_all_present(self, mock_extractor_class):
        """Test validation when all required parameters are present"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=True
            ),
            '--cluster-id': Argument(
                short_option='-c',
                long_option='--cluster-id',
                env_var='CLUSTER_ID',
                description='Cluster ID',
                required=True
            )
        }

        parser = GitOpsArgumentParser()
        params = {
            'account_id': 'test-account',
            'cluster_id': 'test-cluster'
        }

        missing = parser.validate_required_params(params)

        assert len(missing) == 0

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_validate_required_params_missing(self, mock_extractor_class):
        """Test validation when required parameters are missing"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=True
            ),
            '--cluster-id': Argument(
                short_option='-c',
                long_option='--cluster-id',
                env_var='CLUSTER_ID',
                description='Cluster ID',
                required=True
            )
        }

        parser = GitOpsArgumentParser()
        params = {
            'account_id': 'test-account'
            # cluster_id is missing
        }

        missing = parser.validate_required_params(params)

        assert len(missing) == 1
        assert '--cluster-id' in missing

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_validate_required_params_empty_value(self, mock_extractor_class):
        """Test validation treats empty string as missing"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--account-id': Argument(
                short_option='-a',
                long_option='--account-id',
                env_var='ACCOUNT_ID',
                description='Account ID',
                required=True
            )
        }

        parser = GitOpsArgumentParser()
        params = {
            'account_id': ''  # Empty string should be treated as missing
        }

        missing = parser.validate_required_params(params)

        assert len(missing) == 1
        assert '--account-id' in missing

    def test_add_argument_to_group(self):
        """Test adding an argument to an argument group"""
        import argparse

        parser = GitOpsArgumentParser()
        arg_parser = argparse.ArgumentParser()
        group = arg_parser.add_argument_group('Test Group')

        arg = Argument(
            short_option='-a',
            long_option='--account-id',
            env_var='ACCOUNT_ID',
            description='Account ID',
            required=False
        )

        parser._add_argument_to_group(group, arg)

        # Parse to verify argument was added correctly
        args = arg_parser.parse_args(['--account-id', 'test'])
        assert args.account_id == 'test'

    def test_add_argument_to_group_no_short_option(self):
        """Test adding an argument without short option"""
        import argparse

        parser = GitOpsArgumentParser()
        arg_parser = argparse.ArgumentParser()
        group = arg_parser.add_argument_group('Test Group')

        arg = Argument(
            short_option=None,
            long_option='--github-org',
            env_var='GITHUB_ORG',
            description='GitHub organization',
            required=False
        )

        parser._add_argument_to_group(group, arg)

        # Parse to verify argument was added correctly
        args = arg_parser.parse_args(['--github-org', 'myorg'])
        assert args.github_org == 'myorg'

    @patch('mas.cli.gitops.install.argParser.BashFunctionArgumentExtractor')
    def test_parse_args_with_dashes_to_underscores(self, mock_extractor_class):
        """Test that argument names with dashes are converted to underscores"""
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_unique_arguments.return_value = {
            '--mas-instance-id': Argument(
                short_option=None,
                long_option='--mas-instance-id',
                env_var='MAS_INSTANCE_ID',
                description='MAS instance ID',
                required=False
            )
        }
        mock_extractor.get_per_app_arguments.return_value = {}

        parser = GitOpsArgumentParser()

        with patch.dict(os.environ, {}, clear=True):
            params = parser.parse_args(['--mas-instance-id', 'testinst'])

        # Should be converted to underscore
        assert params['mas_instance_id'] == 'testinst'

# Made with Bob
