# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test resource collection utilities."""

import os
import tempfile
import shutil
from typing import Optional
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectResources:
    """Test resource collection functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create temporary directory and mock Kubernetes client.
        """
        self.testDir = tempfile.mkdtemp()
        self.mockClient = Mock(spec=DynamicClient)

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test completion
        WHEN teardown is called
        THEN remove temporary directory.
        """
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)

    def _createMockResource(self, name: str, namespace: Optional[str] = None, status: Optional[dict] = None):
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name
            namespace (str, optional): Resource namespace. Defaults to None.
            status (dict, optional): Resource status. Defaults to None.

        Returns:
            Mock: Mock resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name
        if namespace:
            mockResource.metadata.namespace = namespace
        else:
            mockResource.metadata.namespace = None

        resourceDict = {"metadata": {"name": name}}
        if namespace:
            resourceDict["metadata"]["namespace"] = namespace
        if status:
            resourceDict["status"] = status

        mockResource.to_dict.return_value = resourceDict
        return mockResource

    def _createMockResourceList(self, resources: list):
        """Create a mock ResourceList.

        Args:
            resources (list): List of mock resources

        Returns:
            Mock: Mock ResourceList object
        """
        mockList = Mock()
        mockList.items = resources
        mockList.to_dict.return_value = {"items": [r.to_dict() for r in resources]}
        return mockList

    def test_collect_resources_creates_namespace_directory(self):
        """Test that namespace directory is created.

        GIVEN a namespace and resource type
        WHEN collectResources is called
        THEN namespace directory is created.
        """
        from mas.cli.must_gather.common.resources import collectResources

        # Mock API response
        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-namespace",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=True,
        )

        namespaceDir = os.path.join(self.testDir, "test-namespace")
        assert os.path.exists(namespaceDir)

    def test_collect_resources_creates_cluster_directory_when_no_namespace(self):
        """Test that _cluster directory is created for cluster-scoped resources.

        GIVEN no namespace specified
        WHEN collectResources is called
        THEN _cluster directory is created.
        """
        from mas.cli.must_gather.common.resources import collectResources

        # Mock API response
        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace=None,
            apiVersion="v1",
            kind="Node",
            outputDir=self.testDir,
            noDetail=True,
        )

        clusterDir = os.path.join(self.testDir, "_cluster")
        assert os.path.exists(clusterDir)

    def test_collect_resources_creates_summary_file(self):
        """Test that summary file is created.

        GIVEN resources exist
        WHEN collectResources is called
        THEN summary .txt file is created with wide output.
        """
        from mas.cli.must_gather.common.resources import collectResources

        # Create mock resources
        mockResource1 = self._createMockResource("pod1", "test-ns", {"phase": "Running"})
        mockResource2 = self._createMockResource("pod2", "test-ns", {"phase": "Pending"})

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource1, mockResource2])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=True,
        )

        summaryFile = os.path.join(self.testDir, "test-ns", "pods.txt")
        assert os.path.exists(summaryFile)

    def test_collect_resources_with_no_detail_flag(self):
        """Test that no detail directory is created when noDetail is True.

        GIVEN noDetail flag is True
        WHEN collectResources is called
        THEN no resource detail directory is created.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=True,
        )

        resourceDir = os.path.join(self.testDir, "test-ns", "pods")
        assert not os.path.exists(resourceDir)

    def test_collect_resources_creates_detail_directory_when_detail_enabled(self):
        """Test that detail directory is created when noDetail is False.

        GIVEN noDetail flag is False
        WHEN collectResources is called with resources
        THEN resource detail directory is created.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource = self._createMockResource("pod1", "test-ns")

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=False,
        )

        resourceDir = os.path.join(self.testDir, "test-ns", "pods")
        assert os.path.exists(resourceDir)

    def test_collect_resources_creates_yaml_files_for_each_resource(self):
        """Test that YAML files are created for each resource.

        GIVEN multiple resources exist
        WHEN collectResources is called with detail enabled
        THEN YAML file is created for each resource.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource1 = self._createMockResource("pod1", "test-ns")
        mockResource2 = self._createMockResource("pod2", "test-ns")

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource1, mockResource2])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=False,
        )

        resourceDir = os.path.join(self.testDir, "test-ns", "pods")
        assert os.path.exists(os.path.join(resourceDir, "pod1.yaml"))
        assert os.path.exists(os.path.join(resourceDir, "pod2.yaml"))

    def test_collect_resources_with_describe_flag_creates_txt_files(self):
        """Test that describe .txt files are created when describe flag is True.

        GIVEN describe flag is True
        WHEN collectResources is called
        THEN .txt describe files are created for each resource.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource = self._createMockResource("pod1", "test-ns", {"phase": "Running"})

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=False,
            describe=True,
        )

        resourceDir = os.path.join(self.testDir, "test-ns", "pods")
        assert os.path.exists(os.path.join(resourceDir, "pod1.txt"))

    def test_collect_resources_with_all_namespaces_flag(self):
        """Test collection across all namespaces.

        GIVEN allNamespaces flag is True
        WHEN collectResources is called
        THEN resources from all namespaces are collected into single file.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource1 = self._createMockResource("pod1", "ns1")
        mockResource2 = self._createMockResource("pod2", "ns2")

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource1, mockResource2])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace=None,
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=False,
            allNamespaces=True,
        )

        resourceDir = os.path.join(self.testDir, "_cluster", "pods")
        assert os.path.exists(os.path.join(resourceDir, "all-namespaces.yaml"))

    def test_collect_resources_handles_resource_not_found(self):
        """Test graceful handling when resource type doesn't exist.

        GIVEN resource type doesn't exist
        WHEN collectResources is called
        THEN function handles error gracefully and returns False.
        """
        from mas.cli.must_gather.common.resources import collectResources

        self.mockClient.resources.get.side_effect = Exception("Resource not found")

        result = collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="NonExistent",
            outputDir=self.testDir,
            noDetail=True,
        )

        assert result is False

    def test_collect_resources_handles_api_error(self):
        """Test graceful handling of API errors.

        GIVEN API call fails
        WHEN collectResources is called
        THEN function handles error gracefully and returns False.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockApi = Mock()
        mockApi.get.side_effect = Exception("API Error")
        self.mockClient.resources.get.return_value = mockApi

        result = collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=True,
        )

        assert result is False

    def test_collect_resources_sanitizes_resource_names_with_colons(self):
        """Test that resource names with colons are sanitized.

        GIVEN resource name contains colons
        WHEN collectResources creates files
        THEN colons are replaced with underscores.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource = self._createMockResource("pod:with:colons", "test-ns")

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=False,
        )

        resourceDir = os.path.join(self.testDir, "test-ns", "pods")
        assert os.path.exists(os.path.join(resourceDir, "pod_with_colons.yaml"))

    def test_collect_resources_returns_true_on_success(self):
        """Test that function returns True on successful collection.

        GIVEN valid parameters
        WHEN collectResources completes successfully
        THEN function returns True.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        result = collectResources(
            dynClient=self.mockClient,
            namespace="test-ns",
            apiVersion="v1",
            kind="Pod",
            outputDir=self.testDir,
            noDetail=True,
        )

        assert result is True


# Made with Bob
