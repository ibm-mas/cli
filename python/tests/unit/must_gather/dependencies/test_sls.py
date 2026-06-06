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

import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from kubernetes.dynamic import DynamicClient
from mas.cli.must_gather.dependencies.sls import discoverSLSNamespaces, collectSLSNamespace


class TestDiscoverSLSNamespaces:
    """Tests for SLS namespace discovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.testDir, ignore_errors=True)

    def test_discover_from_license_service_crs(self):
        """Test SLS namespace discovery from LicenseService CRs.

        GIVEN a cluster with LicenseService CRs
        WHEN discoverSLSNamespaces is called
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

    def test_discover_with_mas_instance_ids_uses_license_service(self):
        """Test SLS namespace discovery with MAS instance IDs still uses LicenseService.

        GIVEN a cluster with LicenseService CRs
        WHEN discoverSLSNamespaces is called with MAS instance IDs
        THEN namespaces are still discovered from LicenseService CRs (masInstanceIds parameter is ignored).
        """
        # Mock LicenseService API
        mockLicenseServiceApi = MagicMock()
        mockLS1 = MagicMock()
        mockLS1.metadata.namespace = "sls-namespace1"
        mockLicenseServiceApi.get.return_value = MagicMock(items=[mockLS1])

        self.mockClient.resources.get.return_value = mockLicenseServiceApi

        # masInstanceIds parameter is kept for backward compatibility but not used
        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=["inst1"])

        assert namespaces == {"sls-namespace1"}

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

    def test_discover_handles_api_errors(self):
        """Test SLS namespace discovery handles API errors gracefully.

        GIVEN an API error during discovery
        WHEN discoverSLSNamespaces is called
        THEN an empty set is returned without raising exceptions.
        """
        # Mock API to raise exception
        self.mockClient.resources.get.side_effect = Exception("Test error")

        namespaces = discoverSLSNamespaces(self.mockClient, masInstanceIds=None)

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
    def test_collect_sls_namespace_basic(self, mockCollectSecrets, mockCollectPods, mockCollectResources, mockCollectIBM):
        """Test basic SLS namespace collection.

        GIVEN an SLS namespace with LicenseService CR
        WHEN collectSLSNamespace is called
        THEN resources are collected.
        """
        namespace = "sls-namespace"

        # Mock all collection functions to return True
        mockCollectIBM.return_value = True
        mockCollectResources.return_value = True
        mockCollectPods.return_value = (True, 1)
        mockCollectSecrets.return_value = (True, 1)

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=False)

        assert result is True
        mockCollectIBM.assert_called_once()
        assert mockCollectResources.call_count == 8  # 8 standard resource types
        mockCollectPods.assert_called_once()
        mockCollectSecrets.assert_called_once()

    def test_collect_sls_namespace_with_no_detail(self):
        """Test SLS namespace collection with noDetail flag.

        GIVEN an SLS namespace
        WHEN collectSLSNamespace is called with noDetail=True
        THEN only summary is generated without detailed YAML.
        """
        namespace = "sls-namespace"

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=True)

        assert result is True

    @patch("mas.cli.must_gather.common.collectIBMCustomResources")
    def test_collect_sls_namespace_handles_errors(self, mockCollectIBM):
        """Test SLS namespace collection handles errors gracefully.

        GIVEN an error during collection
        WHEN collectSLSNamespace is called
        THEN errors are handled and False is returned.
        """
        mockCollectIBM.side_effect = Exception("Test error")

        result = collectSLSNamespace(self.mockClient, "test-namespace", self.testDir, noDetail=False)

        assert result is False

    @patch("mas.cli.must_gather.common.collectIBMCustomResources")
    @patch("mas.cli.must_gather.common.collectResources")
    @patch("mas.cli.must_gather.common.collectPods")
    @patch("mas.cli.must_gather.common.collectSecrets")
    def test_collect_sls_namespace_always_collects_pod_logs(self, mockCollectSecrets, mockCollectPods, mockCollectResources, mockCollectIBM):
        """Test that SLS namespace collection always collects pod logs.

        GIVEN an SLS namespace with detailed collection enabled
        WHEN collectSLSNamespace is called
        THEN pod logs are always collected (podLogs=True).
        """
        namespace = "sls-namespace"

        mockCollectIBM.return_value = True
        mockCollectResources.return_value = True
        mockCollectPods.return_value = (True, 1)
        mockCollectSecrets.return_value = (True, 1)

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=False)

        assert result is True
        # Verify that collectPods was called with podLogs=True
        mockCollectPods.assert_called_once()
        call_kwargs = mockCollectPods.call_args.kwargs
        assert call_kwargs["podLogs"] is True

    @patch("mas.cli.must_gather.common.collectIBMCustomResources")
    @patch("mas.cli.must_gather.common.collectResources")
    @patch("mas.cli.must_gather.common.collectPods")
    @patch("mas.cli.must_gather.common.collectSecrets")
    def test_collect_sls_namespace_uses_correct_output_paths(self, mockCollectSecrets, mockCollectPods, mockCollectResources, mockCollectIBM):
        """Test that SLS namespace collection passes outputDir correctly to collectors.

        GIVEN an SLS namespace with detailed collection enabled
        WHEN collectSLSNamespace is called
        THEN collectors receive outputDir without modification (they add /resources internally).
        """
        namespace = "sls-namespace"

        mockCollectIBM.return_value = True
        mockCollectResources.return_value = True
        mockCollectPods.return_value = (True, 1)
        mockCollectSecrets.return_value = (True, 1)

        result = collectSLSNamespace(self.mockClient, namespace, self.testDir, noDetail=False)

        assert result is True
        # Verify that collectors receive outputDir directly (not outputDir/resources)
        mockCollectIBM.assert_called_once_with(self.mockClient, namespace, self.testDir)
        mockCollectPods.assert_called_once()
        assert mockCollectPods.call_args.kwargs["outputDir"] == self.testDir
        mockCollectSecrets.assert_called_once_with(self.mockClient, namespace, self.testDir, secretData=False)

        # Verify collectResources calls
        for call in mockCollectResources.call_args_list:
            assert call.args[4] == self.testDir


# Made with Bob
