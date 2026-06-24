# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test Red Hat OpenShift AI dependency collector."""

from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException


class TestDiscoverRHOAINamespaces:
    """Test RHOAI namespace discovery functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create mock Kubernetes client.
        """
        self.mockClient = Mock(spec=DynamicClient)

    def _createMockNamespace(self, name: str):
        """Create a mock Kubernetes namespace.

        Args:
            name (str): Namespace name

        Returns:
            Mock: Mock namespace object
        """
        mockNamespace = Mock()
        mockNamespace.metadata = Mock()
        mockNamespace.metadata.name = name
        mockNamespace.to_dict.return_value = {"metadata": {"name": name}}
        return mockNamespace

    def test_discover_rhoai_namespaces_when_all_exist(self):
        """Test RHOAI namespace discovery when all namespaces exist.

        GIVEN all RHOAI namespaces exist
        WHEN discoverRHOAINamespaces is called
        THEN all three namespaces are returned.
        """
        from mas.cli.must_gather.dependencies.rhoai import _discoverRHOAINamespaces

        # Mock namespace lookup
        mockNamespaceApi = Mock()

        def mockGet(name):
            return self._createMockNamespace(name)

        mockNamespaceApi.get.side_effect = mockGet

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = _discoverRHOAINamespaces(dynClient=self.mockClient)

        assert namespaces == {
            "redhat-ods-operator",
            "redhat-ods-applications",
        }, f"RHOAI namespace discovery should return all namespaces when they exist, but got: {namespaces}"

    def test_discover_rhoai_namespaces_when_only_operator_exists(self):
        """Test RHOAI namespace discovery when only operator namespace exists.

        GIVEN only redhat-ods-operator namespace exists
        WHEN discoverRHOAINamespaces is called
        THEN only redhat-ods-operator is returned.
        """
        from mas.cli.must_gather.dependencies.rhoai import _discoverRHOAINamespaces

        # Mock namespace lookup
        mockNamespaceApi = Mock()

        def mockGet(name):
            if name == "redhat-ods-operator":
                return self._createMockNamespace(name)
            raise ApiException(status=404, reason="Not Found")

        mockNamespaceApi.get.side_effect = mockGet

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = _discoverRHOAINamespaces(dynClient=self.mockClient)

        assert namespaces == {
            "redhat-ods-operator"
        }, f"RHOAI namespace discovery should return only redhat-ods-operator when other namespaces do not exist, but got: {namespaces}"

    def test_discover_rhoai_namespaces_when_none_exist(self):
        """Test RHOAI namespace discovery when no namespaces exist.

        GIVEN no RHOAI namespaces exist
        WHEN discoverRHOAINamespaces is called
        THEN empty set is returned.
        """
        from mas.cli.must_gather.dependencies.rhoai import _discoverRHOAINamespaces

        # Mock namespace lookup to raise NotFoundError
        mockNamespaceApi = Mock()
        mockNamespaceApi.get.side_effect = ApiException(status=404, reason="Not Found")

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = _discoverRHOAINamespaces(dynClient=self.mockClient)

        assert namespaces == set(), f"RHOAI namespace discovery should return empty set when no namespaces exist, but got: {namespaces}"

    def test_discover_rhoai_namespaces_when_operator_and_applications_exist(self):
        """Test RHOAI namespace discovery when operator and applications namespaces exist.

        GIVEN redhat-ods-operator and redhat-ods-applications namespaces exist
        WHEN discoverRHOAINamespaces is called
        THEN both namespaces are returned.
        """
        from mas.cli.must_gather.dependencies.rhoai import _discoverRHOAINamespaces

        # Mock namespace lookup
        mockNamespaceApi = Mock()

        def mockGet(name):
            if name in ["redhat-ods-operator", "redhat-ods-applications"]:
                return self._createMockNamespace(name)
            raise ApiException(status=404, reason="Not Found")

        mockNamespaceApi.get.side_effect = mockGet

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = _discoverRHOAINamespaces(dynClient=self.mockClient)

        assert namespaces == {
            "redhat-ods-operator",
            "redhat-ods-applications",
        }, f"RHOAI namespace discovery should return operator and applications namespaces when they exist, but got: {namespaces}"


class TestGenerateRHOAICollectionTasks:
    """Test RHOAI collection task generation."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create mock Kubernetes client.
        """
        self.mockClient = Mock(spec=DynamicClient)
        # Mock the client attribute needed by CoreV1Api
        self.mockClient.client = Mock()

    def test_generate_rhoai_collection_tasks_creates_tasks_for_namespace(self):
        """Test task generation for RHOAI namespace.

        GIVEN a RHOAI namespace
        WHEN generateRHOAICollectionTasks is called
        THEN tasks are generated for the namespace.
        """
        from mas.cli.must_gather.dependencies.rhoai import _generateRHOAICollectionTasks

        tasks = _generateRHOAICollectionTasks(dynClient=self.mockClient, namespace="redhat-ods-operator", outputDir="/tmp/output", noLogs=False)

        # Each namespace generates multiple tasks (resources, secrets, pods)
        assert len(tasks) > 0, "Task generation should create collection tasks for RHOAI namespace, but no tasks were generated"

    def test_generate_rhoai_collection_tasks_respects_no_logs_flag(self):
        """Test task generation respects noLogs flag.

        GIVEN a RHOAI namespace and noLogs=True
        WHEN generateRHOAICollectionTasks is called
        THEN tasks are generated without pod logs.
        """
        from mas.cli.must_gather.dependencies.rhoai import _generateRHOAICollectionTasks

        tasks = _generateRHOAICollectionTasks(dynClient=self.mockClient, namespace="redhat-ods-operator", outputDir="/tmp/output", noLogs=True)

        # Should still generate tasks, just without pod logs
        assert len(tasks) > 0, "Task generation should create collection tasks even with noLogs=True, but no tasks were generated"


# Made with Bob
