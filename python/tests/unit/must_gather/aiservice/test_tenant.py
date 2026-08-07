# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

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
        # Verify get was called
        mockApi.get.assert_called()

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


if __name__ == "__main__":
    unittest.main()
