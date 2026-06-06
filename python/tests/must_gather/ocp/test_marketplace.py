# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP marketplace resource collection."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectMarketplaceResources:
    """Test OpenShift Marketplace resource collection."""

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

    def _createMockResource(self, name: str, namespace: str = "openshift-marketplace"):
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name
            namespace (str, optional): Resource namespace. Defaults to "openshift-marketplace".

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

    def test_collect_marketplace_resources_collects_catalogsources(self):
        """Test that catalogsources are collected from openshift-marketplace.

        GIVEN a cluster with catalogsources in openshift-marketplace
        WHEN collectMarketplaceResources is called
        THEN catalogsources are collected.
        """
        from mas.cli.must_gather.ocp.marketplace import collectMarketplaceResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("redhat-operators"), self._createMockResource("certified-operators")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectMarketplaceResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        summaryFile = os.path.join(self.testDir, "openshift-marketplace", "catalogsources.md")
        assert os.path.exists(summaryFile)

    def test_collect_marketplace_resources_collects_jobs(self):
        """Test that jobs are collected from openshift-marketplace.

        GIVEN a cluster with jobs in openshift-marketplace
        WHEN collectMarketplaceResources is called
        THEN jobs are collected.
        """
        from mas.cli.must_gather.ocp.marketplace import collectMarketplaceResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("catalog-import-job")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectMarketplaceResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        summaryFile = os.path.join(self.testDir, "openshift-marketplace", "jobs.md")
        assert os.path.exists(summaryFile)

    def test_collect_marketplace_resources_respects_no_detail_flag(self):
        """Test that noDetail flag is respected.

        GIVEN noDetail=True
        WHEN collectMarketplaceResources is called
        THEN only summary files are created.
        """
        from mas.cli.must_gather.ocp.marketplace import collectMarketplaceResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([self._createMockResource("redhat-operators")])
        self.mockClient.resources.get.return_value = mockApi

        result = collectMarketplaceResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=True)

        assert result is True
        summaryFile = os.path.join(self.testDir, "openshift-marketplace", "catalogsources.md")
        assert os.path.exists(summaryFile)
        # Detail directory should NOT exist
        detailDir = os.path.join(self.testDir, "openshift-marketplace", "catalogsources")
        assert not os.path.exists(detailDir)

    def test_collect_marketplace_resources_handles_errors_gracefully(self):
        """Test that errors are handled gracefully.

        GIVEN an error occurs during collection
        WHEN collectMarketplaceResources is called
        THEN partial success is returned.
        """
        from mas.cli.must_gather.ocp.marketplace import collectMarketplaceResources

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "CatalogSource":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("redhat-operators")])
            else:
                mockApi.get.side_effect = Exception("API error")
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectMarketplaceResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True  # Partial success


# Made with Bob
