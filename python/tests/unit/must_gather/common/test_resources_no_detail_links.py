# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test that markdown links are not created when noDetail=True."""

import os
import tempfile
import shutil
from typing import Optional
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestResourcesNoDetailLinks:
    """Test that resource links respect noDetail flag."""

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

    def _createMockResource(self, name: str, namespace: Optional[str] = None):
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name
            namespace (str, optional): Resource namespace. Defaults to None.

        Returns:
            Mock: Mock resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name
        mockResource.metadata.namespace = namespace

        resourceDict = {"metadata": {"name": name}}
        if namespace:
            resourceDict["metadata"]["namespace"] = namespace

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

    def test_markdown_does_not_contain_links_when_no_detail_true(self):
        """Test that markdown summary does not contain links when noDetail=True.

        GIVEN noDetail flag is True
        WHEN collectResources creates markdown summary
        THEN resource names are plain text, not markdown links.
        """
        from mas.cli.must_gather.common.resources import collectResources

        mockResource1 = self._createMockResource("clusterrolebinding1")
        mockResource2 = self._createMockResource("clusterrolebinding2")

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([mockResource1, mockResource2])
        self.mockClient.resources.get.return_value = mockApi

        collectResources(
            dynClient=self.mockClient,
            namespace=None,
            apiVersion="rbac.authorization.k8s.io/v1",
            kind="ClusterRoleBinding",
            outputDir=self.testDir,
            noDetail=True,
        )

        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "clusterrolebindings.md")
        assert os.path.exists(summaryFile)

        with open(summaryFile, "r") as f:
            content = f.read()

        # Should NOT contain markdown links like [clusterrolebinding1](clusterrolebindings/clusterrolebinding1.yaml)
        assert "[clusterrolebinding1](clusterrolebindings/clusterrolebinding1.yaml)" not in content
        assert "[clusterrolebinding2](clusterrolebindings/clusterrolebinding2.yaml)" not in content

        # Should contain plain text names
        assert "clusterrolebinding1" in content
        assert "clusterrolebinding2" in content

    def test_markdown_contains_links_when_no_detail_false(self):
        """Test that markdown summary contains links when noDetail=False.

        GIVEN noDetail flag is False
        WHEN collectResources creates markdown summary
        THEN resource names are markdown links to YAML files.
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

        summaryFile = os.path.join(self.testDir, "resources", "test-ns", "pods.md")
        assert os.path.exists(summaryFile)

        with open(summaryFile, "r") as f:
            content = f.read()

        # Should contain markdown links
        assert "[pod1](pods/pod1.yaml)" in content
        assert "[pod2](pods/pod2.yaml)" in content


# Made with Bob
