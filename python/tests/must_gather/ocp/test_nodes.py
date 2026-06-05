# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP node resource collection."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectNodes:
    """Test node resource collection with describe output."""

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

    def _createMockResource(self, name: str):
        """Create a mock Kubernetes node resource.

        Args:
            name (str): Node name

        Returns:
            Mock: Mock node resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name

        # Nodes are cluster-scoped, no namespace
        del mockResource.metadata.namespace

        resourceDict = {"metadata": {"name": name}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}}

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

    def test_collect_nodes_creates_summary_file(self):
        """Test that nodes summary file is created.

        GIVEN a cluster with nodes
        WHEN collectNodes is called
        THEN nodes.txt summary file is created.
        """
        from mas.cli.must_gather.ocp.nodes import collectNodes

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("node1"), self._createMockResource("node2")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectNodes(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        summaryFile = os.path.join(self.testDir, "_cluster", "nodes.txt")
        assert os.path.exists(summaryFile)

    def test_collect_nodes_creates_describe_files(self):
        """Test that describe files are created for each node.

        GIVEN a cluster with nodes
        WHEN collectNodes is called with noDetail=False
        THEN describe .txt files are created for each node.
        """
        from mas.cli.must_gather.ocp.nodes import collectNodes

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("node1"), self._createMockResource("node2")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectNodes(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        # Check describe files exist
        node1Describe = os.path.join(self.testDir, "_cluster", "nodes", "node1.txt")
        node2Describe = os.path.join(self.testDir, "_cluster", "nodes", "node2.txt")
        assert os.path.exists(node1Describe)
        assert os.path.exists(node2Describe)

    def test_collect_nodes_creates_yaml_files(self):
        """Test that YAML files are created for each node.

        GIVEN a cluster with nodes
        WHEN collectNodes is called with noDetail=False
        THEN YAML files are created for each node.
        """
        from mas.cli.must_gather.ocp.nodes import collectNodes

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("node1")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectNodes(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        yamlFile = os.path.join(self.testDir, "_cluster", "nodes", "node1.yaml")
        assert os.path.exists(yamlFile)

    def test_collect_nodes_respects_no_detail_flag(self):
        """Test that noDetail flag is respected.

        GIVEN noDetail=True
        WHEN collectNodes is called
        THEN only summary file is created, no detailed files.
        """
        from mas.cli.must_gather.ocp.nodes import collectNodes

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("node1")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectNodes(dynClient=self.mockClient, outputDir=self.testDir, noDetail=True)

        assert result is True
        # Summary should exist
        summaryFile = os.path.join(self.testDir, "_cluster", "nodes.txt")
        assert os.path.exists(summaryFile)
        # Detail directory should NOT exist
        detailDir = os.path.join(self.testDir, "_cluster", "nodes")
        assert not os.path.exists(detailDir)

    def test_collect_nodes_handles_errors_gracefully(self):
        """Test that errors are handled gracefully.

        GIVEN an error occurs during collection
        WHEN collectNodes is called
        THEN False is returned but no exception is raised.
        """
        from mas.cli.must_gather.ocp.nodes import collectNodes

        # Mock API to raise exception
        mockApi = Mock()
        mockApi.get.side_effect = Exception("API error")
        self.mockClient.resources.get.return_value = mockApi

        result = collectNodes(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is False


# Made with Bob
