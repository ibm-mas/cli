# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for SLS license service collector."""

import os

import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException
from mas.cli.must_gather.sls.license_service import discoverSLSNamespaces, collectSLSNamespace, generateSLSSummary


class TestDiscoverSLSNamespaces:
    """Tests for SLS namespace discovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.testDir, ignore_errors=True)

    def test_discover_from_slscfg_with_mas_instance_ids(self):
        """Test SLS namespace discovery from slscfg CRs.

        GIVEN a cluster with slscfg CRs in MAS core namespaces
        WHEN discoverSLSNamespaces is called with MAS instance IDs
        THEN SLS namespaces are extracted from slscfg spec.config.url.
        """
        # Mock slscfg API
        mockSlsCfgApi = MagicMock()
        mockSlsCfg = MagicMock()
        mockSlsCfg.get.return_value = {"config": {"url": "https://sls-route.sls-namespace.svc:443"}}
        mockSlsCfgApi.get.return_value = MagicMock(items=[mockSlsCfg])

        # Mock route API
        mockRouteApi = MagicMock()
        mockRoute = MagicMock()
        mockRoute.metadata.name = "sls-route"
        mockRoute.metadata.namespace = "sls-namespace"
        mockRouteApi.get.return_value = MagicMock(items=[mockRoute])

        # Configure mock client
        def get_resource(api_version=None, kind=None):
            if kind == "SlsCfg":
                return mockSlsCfgApi
            elif kind == "Route":
                return mockRouteApi
            raise ApiException(status=404)

        self.mockClient.resources.get.side_effect = get_resource

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=["inst1"])

        assert namespaces == {"sls-namespace"}

    def test_discover_from_slscfg_multiple_instances(self):
        """Test SLS namespace discovery from multiple MAS instances.

        GIVEN a cluster with multiple MAS instances using different SLS
        WHEN discoverSLSNamespaces is called with multiple instance IDs
        THEN all unique SLS namespaces are discovered.
        """
        # Mock slscfg API
        mockSlsCfgApi = MagicMock()

        # Create different slscfg responses for different namespaces
        def get_slscfg(namespace=None):
            if namespace == "mas-inst1-core" or namespace == "mas-inst2-core":
                mockSlsCfg = MagicMock()
                mockSlsCfg.get.return_value = {"config": {"url": "https://sls-route1.sls-ns1.svc:443"}}
                return MagicMock(items=[mockSlsCfg])
            elif namespace == "mas-inst3-core":
                mockSlsCfg = MagicMock()
                mockSlsCfg.get.return_value = {"config": {"url": "https://sls-route2.sls-ns2.svc:443"}}
                return MagicMock(items=[mockSlsCfg])
            return MagicMock(items=[])

        mockSlsCfgApi.get.side_effect = get_slscfg

        # Mock route API
        mockRouteApi = MagicMock()
        mockRoute1 = MagicMock()
        mockRoute1.metadata.name = "sls-route1"
        mockRoute1.metadata.namespace = "sls-ns1"
        mockRoute2 = MagicMock()
        mockRoute2.metadata.name = "sls-route2"
        mockRoute2.metadata.namespace = "sls-ns2"
        mockRouteApi.get.return_value = MagicMock(items=[mockRoute1, mockRoute2])

        # Configure mock client
        def get_resource(api_version=None, kind=None):
            if kind == "SlsCfg":
                return mockSlsCfgApi
            elif kind == "Route":
                return mockRouteApi
            raise ApiException(status=404)

        self.mockClient.resources.get.side_effect = get_resource

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=["inst1", "inst2", "inst3"])

        assert namespaces == {"sls-ns1", "sls-ns2"}

    def test_discover_from_license_service_crs(self):
        """Test SLS namespace discovery from LicenseService CRs.

        GIVEN a cluster with LicenseService CRs
        WHEN discoverSLSNamespaces is called without MAS instance IDs
        THEN namespaces are discovered from LicenseService CRs.
        """
        # Mock LicenseService API
        mockLicenseServiceApi = MagicMock()
        mockLS1 = MagicMock()
        mockLS1.metadata.namespace = "sls-namespace1"
        mockLS2 = MagicMock()
        mockLS2.metadata.namespace = "sls-namespace2"
        mockLicenseServiceApi.get.return_value = MagicMock(items=[mockLS1, mockLS2])

        self.mockClient.resources.get.return_value = mockLicenseServiceApi

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=None)

        assert namespaces == {"sls-namespace1", "sls-namespace2"}

    def test_discover_no_sls_found(self):
        """Test SLS namespace discovery when no SLS exists.

        GIVEN a cluster without SLS
        WHEN discoverSLSNamespaces is called
        THEN an empty set is returned.
        """
        # Mock LicenseService API with no items
        mockLicenseServiceApi = MagicMock()
        mockLicenseServiceApi.get.return_value = MagicMock(items=[])
        self.mockClient.resources.get.return_value = mockLicenseServiceApi

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=None)

        assert namespaces == set()

    def test_discover_handles_missing_slscfg(self):
        """Test SLS namespace discovery handles missing slscfg gracefully.

        GIVEN a cluster where slscfg CRs don't exist
        WHEN discoverSLSNamespaces is called with MAS instance IDs
        THEN an empty set is returned without errors.
        """
        # Mock slscfg API to raise 404
        mockSlsCfgApi = MagicMock()
        mockSlsCfgApi.get.side_effect = ApiException(status=404)
        self.mockClient.resources.get.return_value = mockSlsCfgApi

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=["inst1"])

        assert namespaces == set()

    def test_discover_handles_malformed_slscfg(self):
        """Test SLS namespace discovery handles malformed slscfg.

        GIVEN a cluster with slscfg missing URL
        WHEN discoverSLSNamespaces is called
        THEN the malformed config is skipped without errors.
        """
        # Mock slscfg API with malformed data
        mockSlsCfgApi = MagicMock()
        mockSlsCfg = MagicMock()
        mockSlsCfg.get.return_value = {"config": {}}  # Missing URL
        mockSlsCfgApi.get.return_value = MagicMock(items=[mockSlsCfg])

        # Mock route API
        mockRouteApi = MagicMock()
        mockRouteApi.get.return_value = MagicMock(items=[])

        # Configure mock client
        def get_resource(api_version=None, kind=None):
            if kind == "SlsCfg":
                return mockSlsCfgApi
            elif kind == "Route":
                return mockRouteApi
            raise ApiException(status=404)

        self.mockClient.resources.get.side_effect = get_resource

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=["inst1"])

        assert namespaces == set()


class TestCollectSLSNamespace:
    """Tests for SLS namespace collection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.testDir, ignore_errors=True)

    @patch("mas.cli.must_gather.common.collectIBMCustomResources")
    @patch("mas.cli.must_gather.common.collectResources")
    @patch("mas.cli.must_gather.common.collectPods")
    @patch("mas.cli.must_gather.common.collectSecrets")
    @patch("mas.cli.must_gather.sls.license_service.generateSLSSummary")
    def test_collect_sls_namespace_basic(self, mockGenerateSummary, mockCollectSecrets, mockCollectPods, mockCollectResources, mockCollectIBM):
        """Test basic SLS namespace collection.

        GIVEN an SLS namespace with LicenseService CR
        WHEN collectSLSNamespace is called
        THEN resources are collected and summary is generated.
        """
        namespace = "sls-namespace"

        # Mock all collection functions to return True
        mockCollectIBM.return_value = True
        mockCollectResources.return_value = True
        mockCollectPods.return_value = True
        mockCollectSecrets.return_value = True

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=False)

        assert result is True
        mockGenerateSummary.assert_called_once()
        mockCollectIBM.assert_called_once()
        assert mockCollectResources.call_count == 8  # 8 standard resource types

    @patch("mas.cli.must_gather.sls.license_service.generateSLSSummary")
    def test_collect_sls_namespace_with_no_detail(self, mockGenerateSummary):
        """Test SLS namespace collection with noDetail flag.

        GIVEN an SLS namespace
        WHEN collectSLSNamespace is called with noDetail=True
        THEN only summary is generated without detailed YAML.
        """
        namespace = "sls-namespace"

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=True)

        assert result is True
        mockGenerateSummary.assert_called_once()

    @patch("mas.cli.must_gather.sls.license_service.generateSLSSummary")
    def test_collect_sls_namespace_handles_errors(self, mockGenerateSummary):
        """Test SLS namespace collection handles errors gracefully.

        GIVEN an error during collection
        WHEN collectSLSNamespace is called
        THEN errors are handled and False is returned.
        """
        mockGenerateSummary.side_effect = Exception("Test error")

        result = collectSLSNamespace(self.mockClient, "nonexistent-namespace", self.testDir, noDetail=False)

        assert result is False

    @patch("mas.cli.must_gather.common.collectIBMCustomResources")
    @patch("mas.cli.must_gather.common.collectResources")
    @patch("mas.cli.must_gather.common.collectPods")
    @patch("mas.cli.must_gather.common.collectSecrets")
    @patch("mas.cli.must_gather.sls.license_service.generateSLSSummary")
    def test_collect_sls_namespace_writes_resources_under_single_resources_directory(
        self, mockGenerateSummary, mockCollectSecrets, mockCollectPods, mockCollectResources, mockCollectIBM
    ):
        """Test that SLS namespace collection uses a single resources directory.

        GIVEN an SLS namespace with detailed collection enabled
        WHEN collectSLSNamespace is called
        THEN collected resources are written under outputDir/resources without duplicating resources in the path.
        """
        namespace = "sls-namespace"

        mockCollectIBM.return_value = True
        mockCollectResources.return_value = True
        mockCollectPods.return_value = (True, 1)
        mockCollectSecrets.return_value = (True, 1)

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=False)

        assert result is True
        mockGenerateSummary.assert_called_once_with(self.mockClient, namespace, self.testDir)
        mockCollectIBM.assert_called_once_with(self.mockClient, namespace, os.path.join(self.testDir, "resources"))
        mockCollectPods.assert_called_once_with(dynClient=self.mockClient, namespace=namespace, outputDir=os.path.join(self.testDir, "resources"), podLogs=True)
        mockCollectSecrets.assert_called_once_with(self.mockClient, namespace, os.path.join(self.testDir, "resources"), secretData=False)

        for call in mockCollectResources.call_args_list:
            assert call.args[4] == os.path.join(self.testDir, "resources")


class TestGenerateSLSSummary:
    """Tests for SLS summary generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.testDir, ignore_errors=True)

    def test_generate_summary_single_instance(self):
        """Test SLS summary generation for single instance.

        GIVEN an SLS namespace with one LicenseService
        WHEN generateSLSSummary is called
        THEN a summary file is created with instance details.
        """
        namespace = "sls-namespace"

        # Mock LicenseService API
        mockLicenseServiceApi = MagicMock()
        mockLS = MagicMock()
        mockLS.metadata.name = "sls-instance"
        mockLS.metadata.namespace = namespace
        mockLS.metadata.creationTimestamp = "2024-01-01T00:00:00Z"
        mockLS.status = {"conditions": [{"type": "Ready", "status": "True"}]}
        mockLS.get.side_effect = lambda key, default=None: mockLS.status if key == "status" else default
        mockLicenseServiceApi.get.return_value = MagicMock(items=[mockLS])

        self.mockClient.resources.get.return_value = mockLicenseServiceApi

        generateSLSSummary(self.mockClient, namespace, self.testDir)

        import os

        summaryFile = os.path.join(self.testDir, f"{namespace}.txt")
        assert os.path.exists(summaryFile)

        with open(summaryFile, "r") as f:
            content = f.read()
            assert "sls-instance" in content
            assert namespace in content

    def test_generate_summary_no_license_service(self):
        """Test SLS summary generation when no LicenseService exists.

        GIVEN an SLS namespace without LicenseService
        WHEN generateSLSSummary is called
        THEN a summary file is created indicating no instances found.
        """
        namespace = "sls-namespace"

        # Mock LicenseService API with no items
        mockLicenseServiceApi = MagicMock()
        mockLicenseServiceApi.get.return_value = MagicMock(items=[])
        self.mockClient.resources.get.return_value = mockLicenseServiceApi

        generateSLSSummary(self.mockClient, namespace, self.testDir)

        import os

        summaryFile = os.path.join(self.testDir, f"{namespace}.txt")
        assert os.path.exists(summaryFile)

        with open(summaryFile, "r") as f:
            content = f.read()
            assert "No LicenseService" in content or "not found" in content.lower()

    def test_generate_summary_handles_errors(self):
        """Test SLS summary generation handles errors gracefully.

        GIVEN an error during summary generation
        WHEN generateSLSSummary is called
        THEN errors are logged and handled gracefully.
        """
        # Mock API to raise exception
        self.mockClient.resources.get.side_effect = Exception("Test error")

        # Should not raise exception
        generateSLSSummary(self.mockClient, "nonexistent-namespace", self.testDir)

        # Summary file should still be created with error message
        import os

        summaryFile = os.path.join(self.testDir, "nonexistent-namespace.txt")
        assert os.path.exists(summaryFile)


# Made with Bob
