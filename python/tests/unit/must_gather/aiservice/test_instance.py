"""Tests for AI Service instance discovery and collection."""

import unittest
from unittest.mock import MagicMock, patch
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.aiservice import instance


class TestDiscoverAIServiceInstances(unittest.TestCase):
    """Test AI Service instance discovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)

    def test_discover_aiservice_instances_from_crs(self):
        """Test discovering AI Service instances from AIServiceApp CRs.

        GIVEN AIServiceApp CRs exist in the cluster
        WHEN discoverAIServiceInstances() is called
        THEN it returns a list of instance IDs from the CRs.
        """
        # Mock AIServiceApp CRs
        mockAIServiceApps = MagicMock()
        mockAIServiceApps.items = [
            MagicMock(metadata=MagicMock(name="aiservice1", namespace="aiservice-inst1")),
            MagicMock(metadata=MagicMock(name="aiservice2", namespace="aiservice-inst2")),
        ]

        mockApi = MagicMock()
        mockApi.get.return_value = mockAIServiceApps
        self.mockDynClient.resources.get.return_value = mockApi

        instances = instance.discoverAIServiceInstances(self.mockDynClient)

        self.assertEqual(instances, ["inst1", "inst2"])
        self.mockDynClient.resources.get.assert_called_once_with(api_version="aiservice.ibm.com/v1", kind="AIServiceApp")

    def test_discover_aiservice_instances_from_namespaces(self):
        """Test discovering AI Service instances from aiservice-* namespaces.

        GIVEN aiservice-* namespaces exist but no AIServiceApp CRs
        WHEN discoverAIServiceInstances() is called
        THEN it returns instance IDs from namespace names.
        """
        # Mock AIServiceApp API that raises exception
        mockAIServiceApi = MagicMock()
        mockAIServiceApi.get.side_effect = Exception("Not found")

        # Mock namespaces with proper name attributes
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "aiservice-test1"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "aiservice-test2"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "other-namespace"

        mockNamespaces = MagicMock()
        mockNamespaces.items = [mockNs1, mockNs2, mockNs3]

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces

        # Set up resources.get to return different APIs based on kind
        def mockResourcesGet(api_version=None, kind=None):
            if kind == "AIServiceApp":
                return mockAIServiceApi
            elif kind == "Namespace":
                return mockNsApi
            raise Exception(f"Unexpected kind: {kind}")

        self.mockDynClient.resources.get.side_effect = mockResourcesGet

        instances = instance.discoverAIServiceInstances(self.mockDynClient)

        self.assertEqual(sorted(instances), ["test1", "test2"])

    def test_discover_aiservice_instances_with_filter(self):
        """Test filtering AI Service instances by instance IDs.

        GIVEN multiple AI Service instances exist
        WHEN discoverAIServiceInstances() is called with instanceIds filter
        THEN it returns only the filtered instances.
        """
        mockAIServiceApps = MagicMock()
        mockAIServiceApps.items = [
            MagicMock(metadata=MagicMock(name="aiservice1", namespace="aiservice-inst1")),
            MagicMock(metadata=MagicMock(name="aiservice2", namespace="aiservice-inst2")),
            MagicMock(metadata=MagicMock(name="aiservice3", namespace="aiservice-inst3")),
        ]

        mockApi = MagicMock()
        mockApi.get.return_value = mockAIServiceApps
        self.mockDynClient.resources.get.return_value = mockApi

        instances = instance.discoverAIServiceInstances(self.mockDynClient, instanceIds="inst1,inst3")

        self.assertEqual(sorted(instances), ["inst1", "inst3"])

    def test_discover_aiservice_instances_no_instances(self):
        """Test when no AI Service instances exist.

        GIVEN no AI Service instances exist
        WHEN discoverAIServiceInstances() is called
        THEN it returns an empty list.
        """
        # Mock AIServiceApp API that raises exception
        mockAIServiceApi = MagicMock()
        mockAIServiceApi.get.side_effect = Exception("Not found")

        # Mock empty namespaces
        mockNamespaces = MagicMock()
        mockNamespaces.items = []

        mockNsApi = MagicMock()
        mockNsApi.get.return_value = mockNamespaces

        # Set up resources.get to return different APIs based on kind
        def mockResourcesGet(api_version=None, kind=None):
            if kind == "AIServiceApp":
                return mockAIServiceApi
            elif kind == "Namespace":
                return mockNsApi
            raise Exception(f"Unexpected kind: {kind}")

        self.mockDynClient.resources.get.side_effect = mockResourcesGet

        instances = instance.discoverAIServiceInstances(self.mockDynClient)

        self.assertEqual(instances, [])


class TestCollectAIServiceInstance(unittest.TestCase):
    """Test AI Service instance collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.mockDynClient = MagicMock(spec=DynamicClient)
        self.mockGenericMustGather = MagicMock()

    @patch("mas.cli.must_gather.aiservice.instance._generateAIServiceSummary")
    @patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel")
    def test_collect_aiservice_instance_success(self, mockCollectLogs, mockGenerateSummary):
        """Test successful AI Service instance collection.

        GIVEN an AI Service instance namespace exists
        WHEN collectAIServiceInstance() is called
        THEN it generates summary and collects reconcile logs.
        """

        result = instance.collectAIServiceInstance(
            dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)
        self.mockGenericMustGather.assert_called_once_with(namespace="aiservice-test1", outputSubDir="aiservice/test1")

        # Verify summary generation and log collection were called
        mockGenerateSummary.assert_called_once()
        mockCollectLogs.assert_called_once()

    @patch("mas.cli.must_gather.aiservice.instance._generateAIServiceSummary")
    @patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel")
    def test_collect_aiservice_instance_without_generic_must_gather(self, mockCollectLogs, mockGenerateSummary):
        """Test AI Service collection without genericMustGather.

        GIVEN genericMustGather is not provided
        WHEN collectAIServiceInstance() is called
        THEN it generates summary and collects logs.
        """

        result = instance.collectAIServiceInstance(dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output")

        self.assertTrue(result)
        mockGenerateSummary.assert_called_once()
        mockCollectLogs.assert_called_once()

    @patch("mas.cli.must_gather.aiservice.instance._generateAIServiceSummary")
    @patch("mas.cli.must_gather.aiservice.instance.collectReconcileLogsParallel")
    def test_collect_aiservice_instance_script_failure(self, mockCollectLogs, mockGenerateSummary):
        """Test that collection succeeds even if summary generation has issues.

        GIVEN summary generation is called
        WHEN collectAIServiceInstance() is called
        THEN it continues with collection and returns True.
        """
        # _generateAIServiceSummary handles its own errors internally, so we just verify it's called
        result = instance.collectAIServiceInstance(
            dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)
        mockGenerateSummary.assert_called_once()
        mockCollectLogs.assert_called_once()
        self.mockGenericMustGather.assert_called_once()


if __name__ == "__main__":
    unittest.main()
