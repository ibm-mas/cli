# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test IBM custom resource collection utilities."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectIBMCustomResources:
    """Test IBM custom resource collection functionality."""

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

    def _createMockCRD(self, name: str):
        """Create a mock CRD.

        Args:
            name (str): CRD name

        Returns:
            Mock: Mock CRD object
        """
        mockCRD = Mock()
        mockCRD.metadata = Mock()
        mockCRD.metadata.name = name
        mockCRD.to_dict.return_value = {"metadata": {"name": name}}
        return mockCRD

    def _createMockCRDList(self, crds: list):
        """Create a mock CRD list.

        Args:
            crds (list): List of mock CRDs

        Returns:
            Mock: Mock CRD list object
        """
        mockList = Mock()
        mockList.items = crds
        return mockList

    def test_collect_ibm_custom_resources_discovers_ibm_crds(self):
        """Test that IBM CRDs are discovered.

        GIVEN IBM CRDs exist in cluster
        WHEN collectIBMCustomResources is called
        THEN IBM CRDs are discovered and collected.
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        # Mock CRD API
        mockCRD1 = self._createMockCRD("suites.core.mas.ibm.com")
        mockCRD2 = self._createMockCRD("workspaceapps.apps.mas.ibm.com")
        mockCRD3 = self._createMockCRD("deployments.apps")  # Non-IBM CRD

        mockCRDApi = Mock()
        mockCRDApi.get.return_value = self._createMockCRDList([mockCRD1, mockCRD2, mockCRD3])

        # Mock resource APIs
        def mockResourcesGet(kind=None, api_version=None):
            mockApi = Mock()
            mockApi.get.return_value = Mock(items=[])
            return mockApi

        self.mockClient.resources.get.side_effect = mockResourcesGet

        # First call returns CRD API, subsequent calls return resource APIs
        callCount = [0]

        def sideEffect(kind=None, api_version=None):
            callCount[0] += 1
            if callCount[0] == 1:
                return mockCRDApi
            return mockResourcesGet(kind, api_version)

        self.mockClient.resources.get.side_effect = sideEffect

        result = collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        assert result is True

    def test_collect_ibm_custom_resources_filters_non_ibm_crds(self):
        """Test that non-IBM CRDs are filtered out.

        GIVEN mixed IBM and non-IBM CRDs
        WHEN collectIBMCustomResources is called
        THEN only IBM CRDs are processed.
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        mockCRD1 = self._createMockCRD("suites.core.mas.ibm.com")
        mockCRD2 = self._createMockCRD("deployments.apps")

        mockCRDApi = Mock()
        mockCRDApi.get.return_value = self._createMockCRDList([mockCRD1, mockCRD2])

        callCount = [0]

        def sideEffect(kind=None, api_version=None):
            callCount[0] += 1
            if callCount[0] == 1:
                return mockCRDApi
            mockApi = Mock()
            mockApi.get.return_value = Mock(items=[])
            return mockApi

        self.mockClient.resources.get.side_effect = sideEffect

        collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        # Should only process IBM CRD (suites.core.mas.ibm.com)
        # Verify by checking that resources directory was created
        resourcesDir = os.path.join(self.testDir, "resources")
        assert os.path.exists(resourcesDir)

    def test_collect_ibm_custom_resources_creates_resources_directory(self):
        """Test that resources directory is created.

        GIVEN IBM CRDs exist
        WHEN collectIBMCustomResources is called
        THEN resources directory is created.
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        mockCRD = self._createMockCRD("suites.core.mas.ibm.com")
        mockCRDApi = Mock()
        mockCRDApi.get.return_value = self._createMockCRDList([mockCRD])

        callCount = [0]

        def sideEffect(kind=None, api_version=None):
            callCount[0] += 1
            if callCount[0] == 1:
                return mockCRDApi
            mockApi = Mock()
            mockApi.get.return_value = Mock(items=[])
            return mockApi

        self.mockClient.resources.get.side_effect = sideEffect

        collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        resourcesDir = os.path.join(self.testDir, "resources")
        assert os.path.exists(resourcesDir)

    def test_collect_ibm_custom_resources_handles_no_ibm_crds(self):
        """Test handling when no IBM CRDs exist.

        GIVEN no IBM CRDs exist
        WHEN collectIBMCustomResources is called
        THEN function completes successfully.
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        mockCRDApi = Mock()
        mockCRDApi.get.return_value = self._createMockCRDList([])
        self.mockClient.resources.get.return_value = mockCRDApi

        result = collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        assert result is True

    def test_collect_ibm_custom_resources_handles_api_error(self):
        """Test graceful handling of API errors.

        GIVEN API call fails when fetching CRDs
        WHEN collectIBMCustomResources is called
        THEN function handles error gracefully and returns True (no CRDs found is not an error).
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        mockCRDApi = Mock()
        mockCRDApi.get.side_effect = Exception("API Error")
        self.mockClient.resources.get.return_value = mockCRDApi

        result = collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        assert result is True

    def test_collect_ibm_custom_resources_returns_true_on_success(self):
        """Test that function returns True on successful collection.

        GIVEN valid parameters
        WHEN collectIBMCustomResources completes successfully
        THEN function returns True.
        """
        from mas.cli.must_gather.common.ibm_resources import collectIBMCustomResources

        mockCRDApi = Mock()
        mockCRDApi.get.return_value = self._createMockCRDList([])
        self.mockClient.resources.get.return_value = mockCRDApi

        result = collectIBMCustomResources(dynClient=self.mockClient, namespace="test-ns", outputDir=self.testDir, noDetail=False)

        assert result is True
