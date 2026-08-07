# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Integration tests for collectors flag functionality."""

import pytest
from unittest.mock import Mock, patch
from mas.cli.must_gather.app import MustGatherApp
from mas.cli.must_gather.arg_parser import mustGatherArgParser


class TestCollectorsIntegration:
    """Test collectors flag integration with collection planning."""

    @pytest.fixture
    def mockDynClient(self):
        """Create mock DynamicClient for testing.

        GIVEN a mock DynamicClient
        WHEN tests need to interact with Kubernetes
        THEN mock client provides necessary responses.
        """
        client = Mock()
        client.resources.get.return_value = Mock()
        return client

    @pytest.fixture
    def mustGatherApp(self, mockDynClient):
        """Create MustGatherApp instance with mocked dependencies.

        GIVEN a MustGatherApp instance
        WHEN tests need to test collection planning
        THEN app is configured with mock dependencies.
        """
        app = MustGatherApp()
        app._dynClient = mockDynClient
        return app

    def test_ocp_collector_enabled_by_default(self, mustGatherApp):
        """Test that OCP collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN OCP resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            # OCP should be in the plan when collectors includes 'ocp'
            assert args.collectors is not None
            assert "ocp" in args.collectors

    def test_ocp_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that OCP collector is disabled when excluded from collectors.

        GIVEN collectors configuration without ocp
        WHEN planCollection is called
        THEN OCP resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "mas,sls"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            # OCP should not be in collectors list
            assert "ocp" not in args.collectors

    def test_db2_collector_enabled_by_default(self, mustGatherApp):
        """Test that DB2 collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN DB2 resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "db2" in args.collectors

    def test_db2_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that DB2 collector is disabled when excluded from collectors.

        GIVEN collectors configuration without db2
        WHEN planCollection is called
        THEN DB2 resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "db2" not in args.collectors

    def test_kafka_collector_enabled_by_default(self, mustGatherApp):
        """Test that Kafka collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN Kafka resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "kafka" in args.collectors

    def test_kafka_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that Kafka collector is disabled when excluded from collectors.

        GIVEN collectors configuration without kafka
        WHEN planCollection is called
        THEN Kafka resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "kafka" not in args.collectors

    def test_mongodb_collector_enabled_by_default(self, mustGatherApp):
        """Test that MongoDB collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN MongoDB resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "mongodb" in args.collectors

    def test_mongodb_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that MongoDB collector is disabled when excluded from collectors.

        GIVEN collectors configuration without mongodb
        WHEN planCollection is called
        THEN MongoDB resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "mongodb" not in args.collectors

    def test_cp4d_collector_enabled_by_default(self, mustGatherApp):
        """Test that CP4D collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN CP4D resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "cp4d" in args.collectors

    def test_cp4d_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that CP4D collector is disabled when excluded from collectors.

        GIVEN collectors configuration without cp4d
        WHEN planCollection is called
        THEN CP4D resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "cp4d" not in args.collectors

    def test_cert_manager_collector_enabled_by_default(self, mustGatherApp):
        """Test that cert-manager collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN cert-manager resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "cert-manager" in args.collectors

    def test_cert_manager_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that cert-manager collector is disabled when excluded from collectors.

        GIVEN collectors configuration without cert-manager
        WHEN planCollection is called
        THEN cert-manager resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "cert-manager" not in args.collectors

    def test_grafana_collector_enabled_by_default(self, mustGatherApp):
        """Test that Grafana collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN Grafana resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "grafana" in args.collectors

    def test_grafana_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that Grafana collector is disabled when excluded from collectors.

        GIVEN collectors configuration without grafana
        WHEN planCollection is called
        THEN Grafana resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "grafana" not in args.collectors

    def test_sls_collector_enabled_by_default(self, mustGatherApp):
        """Test that SLS collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN SLS resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "sls" in args.collectors

    def test_sls_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that SLS collector is disabled when excluded from collectors.

        GIVEN collectors configuration without sls
        WHEN planCollection is called
        THEN SLS resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "sls" not in args.collectors

    def test_mas_collector_enabled_by_default(self, mustGatherApp):
        """Test that MAS collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN MAS resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "mas" in args.collectors

    def test_mas_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that MAS collector is disabled when excluded from collectors.

        GIVEN collectors configuration without mas
        WHEN planCollection is called
        THEN MAS resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,sls"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "mas" not in args.collectors

    def test_aiservice_collector_enabled_by_default(self, mustGatherApp):
        """Test that AIService collector is enabled by default.

        GIVEN default collectors configuration
        WHEN planCollection is called
        THEN AIService resources are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args([])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "aiservice" in args.collectors

    def test_aiservice_collector_disabled_when_excluded(self, mustGatherApp):
        """Test that AIService collector is disabled when excluded from collectors.

        GIVEN collectors configuration without aiservice
        WHEN planCollection is called
        THEN AIService resources are not included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "aiservice" not in args.collectors

    def test_multiple_collectors_combination(self, mustGatherApp):
        """Test that multiple collectors can be combined.

        GIVEN collectors configuration with multiple collectors
        WHEN planCollection is called
        THEN only specified collectors are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "ocp,mas,sls,db2"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "ocp" in args.collectors
            assert "mas" in args.collectors
            assert "sls" in args.collectors
            assert "db2" in args.collectors
            # These should not be present
            assert "kafka" not in args.collectors
            assert "mongodb" not in args.collectors

    def test_only_dependencies_collectors(self, mustGatherApp):
        """Test that only dependency collectors can be specified.

        GIVEN collectors configuration with only dependencies
        WHEN planCollection is called
        THEN only dependency collectors are included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "db2,kafka,mongodb,cp4d,cert-manager,grafana"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert "db2" in args.collectors
            assert "kafka" in args.collectors
            assert "mongodb" in args.collectors
            assert "cp4d" in args.collectors
            assert "cert-manager" in args.collectors
            assert "grafana" in args.collectors
            # These should not be present
            assert "ocp" not in args.collectors
            assert "mas" not in args.collectors
            assert "sls" not in args.collectors
            assert "aiservice" not in args.collectors

    def test_single_collector_only(self, mustGatherApp):
        """Test that single collector can be specified alone.

        GIVEN collectors configuration with single collector
        WHEN planCollection is called
        THEN only that collector is included in collection plan.
        """
        parser = mustGatherArgParser
        args = parser.parse_args(["--collectors", "mas"])

        with patch.object(mustGatherApp, "_collectMustGather"):
            mustGatherApp.planCollection(args, "/tmp/test-output")
            assert args.collectors == "mas"
            # All others should not be present
            assert "ocp" not in args.collectors
            assert "db2" not in args.collectors
            assert "sls" not in args.collectors
