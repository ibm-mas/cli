# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test IBM CloudPak for Data dependency collector."""

from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException


class TestDiscoverCP4DNamespaces:
    """Test CP4D namespace discovery functionality."""

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

    def test_discover_cp4d_namespaces_when_operator_namespace_exists(self):
        """Test CP4D namespace discovery when operator namespace exists.

        GIVEN ibm-cpd-operators namespace exists
        WHEN discoverCP4DNamespaces is called
        THEN both ibm-cpd and ibm-cpd-operators namespaces are returned.
        """
        from mas.cli.must_gather.dependencies.cp4d import discoverCP4DNamespaces

        # Mock namespace lookup
        mockNamespaceApi = Mock()
        mockNamespace = self._createMockNamespace("ibm-cpd-operators")
        mockNamespaceApi.get.return_value = mockNamespace

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = discoverCP4DNamespaces(dynClient=self.mockClient)

        assert namespaces == ["ibm-cpd", "ibm-cpd-operators"]

    def test_discover_cp4d_namespaces_when_operator_namespace_not_found(self):
        """Test CP4D namespace discovery when operator namespace does not exist.

        GIVEN ibm-cpd-operators namespace does not exist
        WHEN discoverCP4DNamespaces is called
        THEN empty list is returned.
        """
        from mas.cli.must_gather.dependencies.cp4d import discoverCP4DNamespaces

        # Mock namespace lookup to raise NotFoundError
        mockNamespaceApi = Mock()
        mockNamespaceApi.get.side_effect = ApiException(status=404, reason="Not Found")

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = discoverCP4DNamespaces(dynClient=self.mockClient)

        assert namespaces == []


class TestGenerateCP4DCollectionTasks:
    """Test CP4D collection task generation."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create mock Kubernetes client.
        """
        self.mockClient = Mock(spec=DynamicClient)

    def test_generate_cp4d_collection_tasks_creates_tasks_for_both_namespaces(self):
        """Test task generation for CP4D namespaces.

        GIVEN CP4D namespaces
        WHEN generateCP4DCollectionTasks is called
        THEN tasks are generated for both namespaces.
        """
        from mas.cli.must_gather.dependencies.cp4d import generateCP4DCollectionTasks

        namespaces = ["ibm-cpd", "ibm-cpd-operators"]
        tasks = generateCP4DCollectionTasks(dynClient=self.mockClient, namespaces=namespaces, outputDir="/tmp/output", noDetail=False, noLogs=False)

        # Each namespace generates multiple tasks (resources, secrets, pods)
        assert len(tasks) > 0
        # Verify we have tasks for both namespaces
        assert len(tasks) >= 2

    def test_generate_cp4d_collection_tasks_returns_empty_for_no_namespaces(self):
        """Test task generation with no namespaces.

        GIVEN no CP4D namespaces
        WHEN generateCP4DCollectionTasks is called
        THEN empty list is returned.
        """
        from mas.cli.must_gather.dependencies.cp4d import generateCP4DCollectionTasks

        tasks = generateCP4DCollectionTasks(dynClient=self.mockClient, namespaces=[], outputDir="/tmp/output", noDetail=False, noLogs=False)

        assert tasks == []
