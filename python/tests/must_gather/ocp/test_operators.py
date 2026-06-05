# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP operator resource collection."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectOperatorResources:
    """Test Kubernetes operator resource collection."""

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

    def _createMockResource(self, name: str, namespace: str = "test-ns"):
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name
            namespace (str, optional): Resource namespace. Defaults to "test-ns".

        Returns:
            Mock: Mock resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name
        mockResource.metadata.namespace = namespace

        resourceDict = {"metadata": {"name": name, "namespace": namespace}}

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

    def test_collect_operator_resources_collects_subscriptions(self):
        """Test that subscriptions are collected from all namespaces.

        GIVEN a cluster with subscriptions across namespaces
        WHEN collectOperatorResources is called
        THEN subscriptions are collected with allNamespaces=True.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList(
            [self._createMockResource("ibm-mas-operator", "mas-inst1-core"), self._createMockResource("cert-manager", "cert-manager")]
        )
        self.mockClient.resources.get.return_value = mockApi

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        # Should create _cluster directory for all-namespaces resources
        summaryFile = os.path.join(self.testDir, "_cluster", "subscriptions.txt")
        assert os.path.exists(summaryFile)

    def test_collect_operator_resources_collects_installplans(self):
        """Test that installplans are collected from all namespaces.

        GIVEN a cluster with installplans
        WHEN collectOperatorResources is called
        THEN installplans are collected.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("install-abc123", "mas-inst1-core")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        summaryFile = os.path.join(self.testDir, "_cluster", "installplans.txt")
        assert os.path.exists(summaryFile)

    def test_collect_operator_resources_collects_operatorconditions(self):
        """Test that operatorconditions are collected from all namespaces.

        GIVEN a cluster with operatorconditions
        WHEN collectOperatorResources is called
        THEN operatorconditions are collected.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("ibm-mas-operator.v1.0.0", "mas-inst1-core")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        summaryFile = os.path.join(self.testDir, "_cluster", "operatorconditions.txt")
        assert os.path.exists(summaryFile)

    def test_collect_operator_resources_creates_detailed_yaml(self):
        """Test that detailed YAML files are created when noDetail=False.

        GIVEN operator resources exist
        WHEN collectOperatorResources is called with noDetail=False
        THEN detailed YAML files are created in all-namespaces.yaml.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("sub1", "ns1")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        # Check all-namespaces.yaml exists
        yamlFile = os.path.join(self.testDir, "_cluster", "subscriptions", "all-namespaces.yaml")
        assert os.path.exists(yamlFile)

    def test_collect_operator_resources_respects_no_detail_flag(self):
        """Test that noDetail flag is respected.

        GIVEN noDetail=True
        WHEN collectOperatorResources is called
        THEN only summary files are created.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("sub1", "ns1")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=True)

        assert result is True
        summaryFile = os.path.join(self.testDir, "_cluster", "subscriptions.txt")
        assert os.path.exists(summaryFile)
        # Detail directory should NOT exist
        detailDir = os.path.join(self.testDir, "_cluster", "subscriptions")
        assert not os.path.exists(detailDir)

    def test_collect_operator_resources_handles_errors_gracefully(self):
        """Test that errors are handled gracefully.

        GIVEN an error occurs during collection
        WHEN collectOperatorResources is called
        THEN partial success is returned.
        """
        from mas.cli.must_gather.ocp.operators import collectOperatorResources

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "Subscription":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("sub1", "ns1")])
            else:
                mockApi.get.side_effect = Exception("API error")
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectOperatorResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True  # Partial success


# Made with Bob
