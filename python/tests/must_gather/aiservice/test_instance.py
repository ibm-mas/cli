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

    @patch("mas.cli.must_gather.aiservice.instance.subprocess.run")
    def test_collect_aiservice_instance_success(self, mockSubprocessRun):
        """Test successful AI Service instance collection.

        GIVEN an AI Service instance namespace exists
        WHEN collectAIServiceInstance() is called
        THEN it calls mg-summary-aiservice and mg-collect-aiservice scripts.
        """
        mockSubprocessRun.return_value = MagicMock(returncode=0)

        result = instance.collectAIServiceInstance(
            dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)
        self.mockGenericMustGather.assert_called_once_with(namespace="aiservice-test1", outputSubDir="aiservice/test1")

        # Verify subprocess calls
        self.assertEqual(mockSubprocessRun.call_count, 2)
        calls = mockSubprocessRun.call_args_list

        # Check mg-summary-aiservice call
        self.assertIn("mg-summary-aiservice", calls[0][0][0])
        self.assertIn("aiservice-test1", calls[0][0][0])

        # Check mg-collect-aiservice call
        self.assertIn("mg-collect-aiservice", calls[1][0][0])
        self.assertIn("aiservice-test1", calls[1][0][0])

    @patch("mas.cli.must_gather.aiservice.instance.subprocess.run")
    def test_collect_aiservice_instance_without_generic_must_gather(self, mockSubprocessRun):
        """Test AI Service collection without genericMustGather.

        GIVEN genericMustGather is not provided
        WHEN collectAIServiceInstance() is called
        THEN it only calls the summary and collection scripts.
        """
        mockSubprocessRun.return_value = MagicMock(returncode=0)

        result = instance.collectAIServiceInstance(dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output")

        self.assertTrue(result)
        self.assertEqual(mockSubprocessRun.call_count, 2)

    @patch("mas.cli.must_gather.aiservice.instance.subprocess.run")
    def test_collect_aiservice_instance_script_failure(self, mockSubprocessRun):
        """Test handling of script execution failure.

        GIVEN mg-summary-aiservice script fails
        WHEN collectAIServiceInstance() is called
        THEN it logs the error and continues with collection.
        """
        mockSubprocessRun.side_effect = [Exception("Script not found"), MagicMock(returncode=0)]

        result = instance.collectAIServiceInstance(
            dynClient=self.mockDynClient, instanceId="test1", outputDir="/tmp/output", genericMustGather=self.mockGenericMustGather
        )

        self.assertTrue(result)
        self.mockGenericMustGather.assert_called_once()


if __name__ == "__main__":
    unittest.main()

# Made with Bob
