"""Tests for AI Service tenant discovery and collection."""

import unittest
from unittest.mock import MagicMock
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.aiservice import tenant


class TestDiscoverAIServiceTenants(unittest.TestCase):
    """Test AI Service tenant discovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)

    def test_discover_tenants_from_crs(self):
        """Test discovering AI Service tenants from AIServiceTenant CRs.

        GIVEN AIServiceTenant CRs exist in the cluster
        WHEN discoverAIServiceTenants() is called
        THEN it returns a list of tenant IDs from the CRs.
        """
        # Mock AIServiceTenant CRs - only return tenants from inst1 namespace
        mockTenant1 = MagicMock()
        mockTenant1.metadata.name = "tenant1"
        mockTenant1.metadata.namespace = "aiservice-inst1"
        mockTenant2 = MagicMock()
        mockTenant2.metadata.name = "tenant2"
        mockTenant2.metadata.namespace = "aiservice-inst1"

        mockTenants = MagicMock()
        mockTenants.items = [mockTenant1, mockTenant2]

        mockApi = MagicMock()
        mockApi.get.return_value = mockTenants
        self.mockDynClient.resources.get.return_value = mockApi

        tenants = tenant.discoverAIServiceTenants(self.mockDynClient, instanceId="inst1")

        self.assertEqual(sorted(tenants), ["tenant1", "tenant2"])
        # Verify get was called with the correct namespace
        mockApi.get.assert_called_once_with(namespace="aiservice-inst1")

    def test_discover_tenants_with_filter(self):
        """Test filtering AI Service tenants by tenant IDs.

        GIVEN multiple AI Service tenants exist
        WHEN discoverAIServiceTenants() is called with tenantIds filter
        THEN it returns only the filtered tenants.
        """
        mockTenant1 = MagicMock()
        mockTenant1.metadata.name = "tenant1"
        mockTenant1.metadata.namespace = "aiservice-inst1"
        mockTenant2 = MagicMock()
        mockTenant2.metadata.name = "tenant2"
        mockTenant2.metadata.namespace = "aiservice-inst1"
        mockTenant3 = MagicMock()
        mockTenant3.metadata.name = "tenant3"
        mockTenant3.metadata.namespace = "aiservice-inst1"

        mockTenants = MagicMock()
        mockTenants.items = [mockTenant1, mockTenant2, mockTenant3]

        mockApi = MagicMock()
        mockApi.get.return_value = mockTenants
        self.mockDynClient.resources.get.return_value = mockApi

        tenants = tenant.discoverAIServiceTenants(self.mockDynClient, instanceId="inst1", tenantIds="tenant1,tenant3")

        self.assertEqual(sorted(tenants), ["tenant1", "tenant3"])

    def test_discover_tenants_no_tenants(self):
        """Test when no AI Service tenants exist.

        GIVEN no AI Service tenants exist for the instance
        WHEN discoverAIServiceTenants() is called
        THEN it returns an empty list.
        """
        mockTenants = MagicMock()
        mockTenants.items = []

        mockApi = MagicMock()
        mockApi.get.return_value = mockTenants
        self.mockDynClient.resources.get.return_value = mockApi

        tenants = tenant.discoverAIServiceTenants(self.mockDynClient, instanceId="inst1")

        self.assertEqual(tenants, [])

    def test_discover_tenants_handles_exception(self):
        """Test handling of discovery exception.

        GIVEN AIServiceTenant API raises an exception
        WHEN discoverAIServiceTenants() is called
        THEN it returns an empty list.
        """
        mockApi = MagicMock()
        mockApi.get.side_effect = Exception("API error")
        self.mockDynClient.resources.get.return_value = mockApi

        tenants = tenant.discoverAIServiceTenants(self.mockDynClient, instanceId="inst1")

        self.assertEqual(tenants, [])


class TestCollectAIServiceTenant(unittest.TestCase):
    """Test AI Service tenant collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)

    def test_collect_tenant_success(self):
        """Test successful AI Service tenant collection.

        GIVEN an AI Service tenant exists
        WHEN collectAIServiceTenant() is called
        THEN it collects InferenceService resources for the tenant.
        """
        # Mock InferenceService resources
        mockInferenceService = MagicMock()
        mockInferenceService.metadata.name = "inference1"

        mockInferenceServices = MagicMock()
        mockInferenceServices.items = [mockInferenceService]

        mockApi = MagicMock()
        mockApi.get.return_value = mockInferenceServices
        self.mockDynClient.resources.get.return_value = mockApi

        result = tenant.collectAIServiceTenant(
            dynClient=self.mockDynClient, instanceId="inst1", tenantId="tenant1", namespace="aiservice-inst1", outputDir="/tmp/output"
        )

        self.assertTrue(result)
        # Verify InferenceService API was called
        self.mockDynClient.resources.get.assert_called()

    def test_collect_tenant_no_inference_services(self):
        """Test tenant collection when no InferenceServices exist.

        GIVEN no InferenceService resources exist for the tenant
        WHEN collectAIServiceTenant() is called
        THEN it completes successfully.
        """
        mockInferenceServices = MagicMock()
        mockInferenceServices.items = []

        mockApi = MagicMock()
        mockApi.get.return_value = mockInferenceServices
        self.mockDynClient.resources.get.return_value = mockApi

        result = tenant.collectAIServiceTenant(
            dynClient=self.mockDynClient, instanceId="inst1", tenantId="tenant1", namespace="aiservice-inst1", outputDir="/tmp/output"
        )

        self.assertTrue(result)

    def test_collect_tenant_handles_exception(self):
        """Test handling of collection exception.

        GIVEN InferenceService API raises an exception
        WHEN collectAIServiceTenant() is called
        THEN it logs the error and returns True.
        """
        mockApi = MagicMock()
        mockApi.get.side_effect = Exception("API error")
        self.mockDynClient.resources.get.return_value = mockApi

        result = tenant.collectAIServiceTenant(
            dynClient=self.mockDynClient, instanceId="inst1", tenantId="tenant1", namespace="aiservice-inst1", outputDir="/tmp/output"
        )

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
