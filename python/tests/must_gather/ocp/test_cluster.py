# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP cluster resource collection."""

import os
import tempfile
import shutil
from typing import Optional
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectClusterResources:
    """Test cluster-level resource collection."""

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

        # Use spec to properly handle namespace attribute
        if namespace:
            mockResource.metadata.namespace = namespace
        else:
            # For cluster-scoped resources, namespace attribute should not exist
            del mockResource.metadata.namespace

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

    def test_collect_cluster_resources_collects_storageclasses(self):
        """Test that storageclasses are collected.

        GIVEN a cluster with storageclasses
        WHEN collectClusterResources is called
        THEN storageclasses are collected to _cluster directory.
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        # Mock API responses
        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("gp2"), self._createMockResource("gp3")])

        def mockGetResource(**kwargs):
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert success is True
        # Verify storageclasses.md was created
        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "storageclasses.md")
        assert os.path.exists(summaryFile)

    def test_collect_cluster_resources_collects_clusterversions(self):
        """Test that clusterversions are collected.

        GIVEN a cluster with clusterversions
        WHEN collectClusterResources is called
        THEN clusterversions are collected.
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("version")])

        def mockGetResource(**kwargs):
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert success is True
        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "clusterversions.md")
        assert os.path.exists(summaryFile)

    def test_collect_cluster_resources_collects_objectbucket(self):
        """Test that objectbucket resources are collected.

        GIVEN a cluster with objectbucket resources
        WHEN collectClusterResources is called
        THEN objectbucket, objectbucketclaim, objectstoragecfg are collected.
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("bucket1")])

        def mockGetResource(**kwargs):
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert success is True
        # Should attempt to collect objectbucket
        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "objectbucket.md")
        assert os.path.exists(summaryFile)

    def test_collect_cluster_resources_collects_summary_only_resources(self):
        """Test that summary-only resources are collected without detail.

        GIVEN a cluster with namespaces, packagemanifests, clusterroles, clusterrolebindings
        WHEN collectClusterResources is called with noDetail=False
        THEN these resources are collected with noDetail=True (summary only).
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("default"), self._createMockResource("kube-system")])

        def mockGetResource(**kwargs):
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert success is True
        # Verify namespaces.md exists
        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "namespaces.md")
        assert os.path.exists(summaryFile)
        # Verify detailed directory was NOT created (noDetail=True for these resources)
        detailDir = os.path.join(self.testDir, "resources", "_cluster", "namespaces")
        assert not os.path.exists(detailDir)

    def test_collect_cluster_resources_respects_no_detail_flag(self):
        """Test that noDetail flag is respected.

        GIVEN noDetail=True
        WHEN collectClusterResources is called
        THEN only summary files are created, no detailed YAML.
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("gp2")])

        def mockGetResource(**kwargs):
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=True)

        assert success is True
        # Summary file should exist
        summaryFile = os.path.join(self.testDir, "resources", "_cluster", "storageclasses.md")
        assert os.path.exists(summaryFile)
        # Detail directory should NOT exist
        detailDir = os.path.join(self.testDir, "resources", "_cluster", "storageclasses")
        assert not os.path.exists(detailDir)

    def test_collect_cluster_resources_handles_missing_resources_gracefully(self):
        """Test that missing resources are handled gracefully.

        GIVEN a resource type that doesn't exist
        WHEN collectClusterResources is called
        THEN collection continues without failing.
        """
        from mas.cli.must_gather.ocp.cluster import collectClusterResources

        # Mock API to raise exception for some resources
        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "StorageClass":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("gp2")])
            else:
                mockApi.get.side_effect = Exception("Resource not found")
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        success, printerColumns, ibmCRDs = collectClusterResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        # Should still return True (partial success)
        assert success is True
