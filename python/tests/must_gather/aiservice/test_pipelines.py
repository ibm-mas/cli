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


class TestCollectAIServicePipelines(unittest.TestCase):
    """Test AI Service pipelines collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)
        self.mockGenericMustGather = MagicMock()

    def test_collect_aiservice_pipelines_success(self):
        """Test successful AI Service pipelines collection.

        GIVEN an AI Service pipeline namespace exists
        WHEN collectAIServicePipelines() is called
        THEN it calls genericMustGather for the namespace.
        """
        result = pipelines.collectAIServicePipelines(
            dynClient=self.mockDynClient, namespace="aiservice-inst1-pipelines", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)
        self.mockGenericMustGather.assert_called_once_with(namespace="aiservice-inst1-pipelines", outputSubDir="aiservice/inst1/pipelines")

    def test_collect_aiservice_pipelines_without_generic_must_gather(self):
        """Test AI Service pipelines collection without genericMustGather.

        GIVEN genericMustGather is not provided
        WHEN collectAIServicePipelines() is called
        THEN it returns True without calling genericMustGather.
        """
        result = pipelines.collectAIServicePipelines(dynClient=self.mockDynClient, namespace="aiservice-inst1-pipelines", outputDir="/tmp/output")

        self.assertTrue(result)

    def test_collect_aiservice_pipelines_handles_exception(self):
        """Test handling of collection exception.

        GIVEN genericMustGather raises an exception
        WHEN collectAIServicePipelines() is called
        THEN it logs the error and returns True.
        """
        self.mockGenericMustGather.side_effect = Exception("Collection failed")

        result = pipelines.collectAIServicePipelines(
            dynClient=self.mockDynClient, namespace="aiservice-inst1-pipelines", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

# Made with Bob
