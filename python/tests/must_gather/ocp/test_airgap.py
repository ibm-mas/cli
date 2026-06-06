# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test OCP airgap environment detection and collection."""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from kubernetes.dynamic import DynamicClient


class TestCollectAirgapResources:
    """Test airgap environment detection and resource collection."""

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
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name

        Returns:
            Mock: Mock resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name
        del mockResource.metadata.namespace

        resourceDict = {"metadata": {"name": name}}
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

    def test_detect_airgap_returns_true_when_imagecontentsourcepolicy_exists(self):
        """Test airgap detection with imagecontentsourcepolicy.

        GIVEN a cluster with imagecontentsourcepolicy
        WHEN detectAirgapEnvironment is called
        THEN True is returned.
        """
        from mas.cli.must_gather.ocp.airgap import detectAirgapEnvironment

        # Mock API to return resources for imagecontentsourcepolicy
        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "ImageContentSourcePolicy":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("icsp1")])
            else:
                mockApi.get.return_value = self._createMockResourceList([])
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = detectAirgapEnvironment(self.mockClient)
        assert result is True

    def test_detect_airgap_returns_true_when_imagedigestmirrorset_exists(self):
        """Test airgap detection with imagedigestmirrorset.

        GIVEN a cluster with imagedigestmirrorset
        WHEN detectAirgapEnvironment is called
        THEN True is returned.
        """
        from mas.cli.must_gather.ocp.airgap import detectAirgapEnvironment

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "ImageDigestMirrorSet":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("idms1")])
            else:
                mockApi.get.return_value = self._createMockResourceList([])
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = detectAirgapEnvironment(self.mockClient)
        assert result is True

    def test_detect_airgap_returns_false_when_no_airgap_resources(self):
        """Test airgap detection returns false when no airgap resources.

        GIVEN a cluster without airgap resources
        WHEN detectAirgapEnvironment is called
        THEN False is returned.
        """
        from mas.cli.must_gather.ocp.airgap import detectAirgapEnvironment

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        result = detectAirgapEnvironment(self.mockClient)
        assert result is False

    def test_collect_airgap_resources_skips_when_not_airgap(self):
        """Test that collection is skipped when not airgap environment.

        GIVEN a non-airgap cluster
        WHEN collectAirgapResources is called
        THEN collection is skipped and True is returned.
        """
        from mas.cli.must_gather.ocp.airgap import collectAirgapResources

        mockApi = Mock()
        mockApi.get.return_value = self._createMockResourceList([])
        self.mockClient.resources.get.return_value = mockApi

        result = collectAirgapResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True

    def test_collect_airgap_resources_collects_mirror_resources(self):
        """Test that mirror resources are collected in airgap environment.

        GIVEN an airgap cluster
        WHEN collectAirgapResources is called
        THEN imagecontentsourcepolicy, imagedigestmirrorset, imagetagmirrorset are collected.
        """
        from mas.cli.must_gather.ocp.airgap import collectAirgapResources

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind in ["ImageContentSourcePolicy", "ImageDigestMirrorSet", "ImageTagMirrorSet"]:
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource(f"{kind}-1")])
            else:
                mockApi.get.return_value = self._createMockResourceList([])
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectAirgapResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        # Verify files were created
        assert os.path.exists(os.path.join(self.testDir, "_cluster", "imagecontentsourcepolicy.md"))

    def test_collect_airgap_resources_collects_machineconfig(self):
        """Test that machineconfig resources are collected.

        GIVEN an airgap cluster
        WHEN collectAirgapResources is called
        THEN machineconfig and machineconfigpool are collected.
        """
        from mas.cli.must_gather.ocp.airgap import collectAirgapResources

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "ImageContentSourcePolicy":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("icsp1")])
            elif kind in ["MachineConfig", "MachineConfigPool"]:
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource(f"{kind}-1")])
            else:
                mockApi.get.return_value = self._createMockResourceList([])
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectAirgapResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        assert os.path.exists(os.path.join(self.testDir, "_cluster", "machineconfig.md"))

    @patch("mas.cli.must_gather.ocp.airgap.collectNodeFiles")
    def test_collect_airgap_resources_collects_node_files(self, mockCollectNodeFiles):
        """Test that node files are collected in airgap environment.

        GIVEN an airgap cluster
        WHEN collectAirgapResources is called
        THEN collectNodeFiles is called to collect registries.conf.
        """
        from mas.cli.must_gather.ocp.airgap import collectAirgapResources

        mockCollectNodeFiles.return_value = True

        def mockGetResource(**kwargs):
            mockApi = Mock()
            kind = kwargs.get("kind", "")
            if kind == "ImageContentSourcePolicy":
                mockApi.get.return_value = self._createMockResourceList([self._createMockResource("icsp1")])
            else:
                mockApi.get.return_value = self._createMockResourceList([])
            return mockApi

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectAirgapResources(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True
        mockCollectNodeFiles.assert_called_once_with(dynClient=self.mockClient, outputDir=self.testDir, filePath="/host/etc/containers/registries.conf")


# Made with Bob
