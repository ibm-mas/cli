# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test argument parser for must-gather command."""

from mas.cli.must_gather.arg_parser import createArgumentParser


class TestArgumentParser:
    """Test argument parsing for must-gather command."""

    def test_parser_accepts_directory_short_flag(self):
        """Test that -d flag sets directory parameter.

        GIVEN argument parser
        WHEN -d flag is provided
        THEN directory parameter is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["-d", "/tmp/test"])
        assert args.directory == "/tmp/test"

    def test_parser_accepts_directory_long_flag(self):
        """Test that --directory flag sets directory parameter.

        GIVEN argument parser
        WHEN --directory flag is provided
        THEN directory parameter is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--directory", "/tmp/test"])
        assert args.directory == "/tmp/test"

    def test_parser_has_default_directory(self):
        """Test that directory has default value.

        GIVEN argument parser
        WHEN no directory flag is provided
        THEN directory defaults to /tmp/must-gather.
        """
        parser = createArgumentParser()
        args = parser.parse_args([])
        assert args.directory == "/tmp/must-gather"

    def test_parser_accepts_keep_files_short_flag(self):
        """Test that -k flag sets keep_files parameter.

        GIVEN argument parser
        WHEN -k flag is provided
        THEN keep_files is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["-k"])
        assert args.keep_files is True

    def test_parser_accepts_keep_files_long_flag(self):
        """Test that --keep-files flag sets keep_files parameter.

        GIVEN argument parser
        WHEN --keep-files flag is provided
        THEN keep_files is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--keep-files"])
        assert args.keep_files is True

    def test_parser_keep_files_defaults_to_false(self):
        """Test that keep_files defaults to False.

        GIVEN argument parser
        WHEN no keep-files flag is provided
        THEN keep_files is False.
        """
        parser = createArgumentParser()
        args = parser.parse_args([])
        assert args.keep_files is False

    def test_parser_accepts_summary_only_flag(self):
        """Test that --summary-only flag sets summary_only parameter.

        GIVEN argument parser
        WHEN --summary-only flag is provided
        THEN summary_only is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--summary-only"])
        assert args.summary_only is True

    def test_parser_accepts_no_logs_flag(self):
        """Test that --no-logs flag sets no_logs parameter.

        GIVEN argument parser
        WHEN --no-logs flag is provided
        THEN no_logs is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--no-logs"])
        assert args.no_logs is True

    def test_parser_accepts_secret_data_flag(self):
        """Test that --secret-data flag sets secret_data parameter.

        GIVEN argument parser
        WHEN --secret-data flag is provided
        THEN secret_data is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--secret-data"])
        assert args.secret_data is True

    def test_parser_accepts_pods_only_flag(self):
        """Test that --pods-only flag sets pods_only parameter.

        GIVEN argument parser
        WHEN --pods-only flag is provided
        THEN pods_only is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--pods-only"])
        assert args.pods_only is True

    def test_parser_accepts_mas_instance_ids(self):
        """Test that --mas-instance-ids accepts comma-separated list.

        GIVEN argument parser
        WHEN --mas-instance-ids is provided with comma-separated values
        THEN mas_instance_ids is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--mas-instance-ids", "inst1,inst2"])
        assert args.mas_instance_ids == "inst1,inst2"

    def test_parser_accepts_mas_app_ids(self):
        """Test that --mas-app-ids accepts comma-separated list.

        GIVEN argument parser
        WHEN --mas-app-ids is provided with comma-separated values
        THEN mas_app_ids is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--mas-app-ids", "core,manage"])
        assert args.mas_app_ids == "core,manage"

    def test_parser_has_default_mas_app_ids(self):
        """Test that mas_app_ids has default value.

        GIVEN argument parser
        WHEN no --mas-app-ids is provided
        THEN mas_app_ids defaults to all apps.
        """
        parser = createArgumentParser()
        args = parser.parse_args([])
        expected = "core,add,assist,iot,monitor,manage,optimizer,predict,visualinspection,pipelines,facilities"
        assert args.mas_app_ids == expected

    def test_parser_accepts_aiservice_instance_ids(self):
        """Test that --aiservice-instance-ids accepts comma-separated list.

        GIVEN argument parser
        WHEN --aiservice-instance-ids is provided
        THEN aiservice_instance_ids is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--aiservice-instance-ids", "ai1,ai2"])
        assert args.aiservice_instance_ids == "ai1,ai2"

    def test_parser_accepts_aiservice_tenant_ids(self):
        """Test that --aiservice-tenant-ids accepts comma-separated list.

        GIVEN argument parser
        WHEN --aiservice-tenant-ids is provided
        THEN aiservice_tenant_ids is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--aiservice-tenant-ids", "tenant1,tenant2"])
        assert args.aiservice_tenant_ids == "tenant1,tenant2"

    def test_parser_accepts_no_ocp_flag(self):
        """Test that --no-ocp flag sets no_ocp parameter.

        GIVEN argument parser
        WHEN --no-ocp flag is provided
        THEN no_ocp is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--no-ocp"])
        assert args.no_ocp is True

    def test_parser_accepts_no_dependencies_flag(self):
        """Test that --no-dependencies flag sets no_dependencies parameter.

        GIVEN argument parser
        WHEN --no-dependencies flag is provided
        THEN no_dependencies is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--no-dependencies"])
        assert args.no_dependencies is True

    def test_parser_accepts_no_sls_flag(self):
        """Test that --no-sls flag sets no_sls parameter.

        GIVEN argument parser
        WHEN --no-sls flag is provided
        THEN no_sls is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--no-sls"])
        assert args.no_sls is True

    def test_parser_accepts_no_mas_quick_summary_flag(self):
        """Test that --no-mas-quick-summary flag sets no_mas_quick_summary parameter.

        GIVEN argument parser
        WHEN --no-mas-quick-summary flag is provided
        THEN no_mas_quick_summary is True.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--no-mas-quick-summary"])
        assert args.no_mas_quick_summary is True

    def test_parser_accepts_extra_namespaces(self):
        """Test that --extra-namespaces accepts comma-separated list.

        GIVEN argument parser
        WHEN --extra-namespaces is provided
        THEN extra_namespaces is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--extra-namespaces", "ns1,ns2,ns3"])
        assert args.extra_namespaces == "ns1,ns2,ns3"

    def test_parser_accepts_artifactory_token(self):
        """Test that --artifactory-token accepts token value.

        GIVEN argument parser
        WHEN --artifactory-token is provided
        THEN artifactory_token is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--artifactory-token", "test-token-123"])
        assert args.artifactory_token == "test-token-123"

    def test_parser_accepts_artifactory_upload_dir(self):
        """Test that --artifactory-upload-dir accepts URL value.

        GIVEN argument parser
        WHEN --artifactory-upload-dir is provided
        THEN artifactory_upload_dir is set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["--artifactory-upload-dir", "https://example.com/upload"])
        assert args.artifactory_upload_dir == "https://example.com/upload"

    def test_parser_accepts_multiple_flags_together(self):
        """Test that multiple flags can be combined.

        GIVEN argument parser
        WHEN multiple flags are provided together
        THEN all parameters are set correctly.
        """
        parser = createArgumentParser()
        args = parser.parse_args(["-d", "/custom/dir", "--keep-files", "--summary-only", "--no-logs", "--mas-instance-ids", "inst1", "--no-ocp"])
        assert args.directory == "/custom/dir"
        assert args.keep_files is True
        assert args.summary_only is True
        assert args.no_logs is True
        assert args.mas_instance_ids == "inst1"
        assert args.no_ocp is True


# Made with Bob
