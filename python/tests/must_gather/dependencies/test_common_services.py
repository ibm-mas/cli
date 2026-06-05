# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test IBM Common Services dependency collector."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectCommonServices:
    """Test IBM Common Services collection functionality."""

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

    def test_collect_common_services_when_namespace_exists(self):
        """Test collection when ibm-common-services namespace exists.

        GIVEN ibm-common-services namespace exists
        WHEN collectCommonServices is called
        THEN resources are collected from the namespace.
        """
        from mas.cli.must_gather.dependencies.common_services import collectCommonServices

        # Mock namespace lookup
        mockNamespaceApi = Mock()
        mockNamespace = self._createMockNamespace("ibm-common-services")
        mockNamespaceApi.get.return_value = mockNamespace

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        # Mock genericMustGather
        mockGenericMustGather = Mock(return_value=True)

        result = collectCommonServices(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False, genericMustGather=mockGenericMustGather)

        assert result is True
        mockGenericMustGather.assert_called_once_with(namespace="ibm-common-services", outputDir=self.testDir, noDetail=False)

    def test_collect_common_services_when_namespace_not_found(self):
        """Test collection when ibm-common-services namespace does not exist.

        GIVEN ibm-common-services namespace does not exist
        WHEN collectCommonServices is called
        THEN collection is skipped and returns False.
        """
        from mas.cli.must_gather.dependencies.common_services import collectCommonServices

        # Mock namespace lookup to raise NotFoundError
        mockNamespaceApi = Mock()
        from kubernetes.client.exceptions import ApiException

        mockNamespaceApi.get.side_effect = ApiException(status=404, reason="Not Found")

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectCommonServices(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is False


# Made with Bob
