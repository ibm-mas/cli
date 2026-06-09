"""Tests for AI Service pipelines collection."""

import unittest
from unittest.mock import MagicMock
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.aiservice import pipelines


class TestDiscoverAIServicePipelineNamespaces(unittest.TestCase):
    """Test AI Service pipeline namespace discovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)

    def test_discover_instance_pipeline_namespaces(self):
        """Test discovering instance-specific pipeline namespaces.

        GIVEN AI Service instances exist
        WHEN discoverAIServicePipelineNamespaces() is called
        THEN it returns aiservice-{instance}-pipelines namespaces.
        """
        # Mock namespace API
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "aiservice-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "aiservice-inst2-pipelines"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "aiservice-inst1"
        mockNs4 = MagicMock()
        mockNs4.metadata.name = "other-namespace"

        mockNamespaces = MagicMock()
        mockNamespaces.items = [mockNs1, mockNs2, mockNs3, mockNs4]

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces
        self.mockDynClient.resources.get.return_value = mockNsApi

        namespaces = pipelines.discoverAIServicePipelineNamespaces(self.mockDynClient, instanceIds=["inst1", "inst2"])

        self.assertEqual(sorted(namespaces), ["aiservice-inst1-pipelines", "aiservice-inst2-pipelines"])

    def test_discover_pipeline_namespaces_with_filter(self):
        """Test filtering pipeline namespaces by instance IDs.

        GIVEN multiple AI Service pipeline namespaces exist
        WHEN discoverAIServicePipelineNamespaces() is called with instanceIds filter
        THEN it returns only filtered pipeline namespaces.
        """
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "aiservice-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "aiservice-inst2-pipelines"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "aiservice-inst3-pipelines"

        mockNamespaces = MagicMock()
        mockNamespaces.items = [mockNs1, mockNs2, mockNs3]

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces
        self.mockDynClient.resources.get.return_value = mockNsApi

        namespaces = pipelines.discoverAIServicePipelineNamespaces(self.mockDynClient, instanceIds=["inst1", "inst3"])

        self.assertEqual(sorted(namespaces), ["aiservice-inst1-pipelines", "aiservice-inst3-pipelines"])

    def test_discover_pipeline_namespaces_no_filter(self):
        """Test discovering all pipeline namespaces without filter.

        GIVEN AI Service pipeline namespaces exist
        WHEN discoverAIServicePipelineNamespaces() is called without instanceIds
        THEN it returns all aiservice-*-pipelines namespaces.
        """
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "aiservice-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "aiservice-inst2-pipelines"

        mockNamespaces = MagicMock()
        mockNamespaces.items = [mockNs1, mockNs2]

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces
        self.mockDynClient.resources.get.return_value = mockNsApi

        namespaces = pipelines.discoverAIServicePipelineNamespaces(self.mockDynClient)

        self.assertEqual(sorted(namespaces), ["aiservice-inst1-pipelines", "aiservice-inst2-pipelines"])

    def test_discover_pipeline_namespaces_none_exist(self):
        """Test when no pipeline namespaces exist.

        GIVEN no AI Service pipeline namespaces exist
        WHEN discoverAIServicePipelineNamespaces() is called
        THEN it returns an empty list.
        """
        mockNamespaces = MagicMock()
        mockNamespaces.items = []

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces
        self.mockDynClient.resources.get.return_value = mockNsApi

        namespaces = pipelines.discoverAIServicePipelineNamespaces(self.mockDynClient, instanceIds=["inst1"])

        self.assertEqual(namespaces, [])


if __name__ == "__main__":
    unittest.main()
