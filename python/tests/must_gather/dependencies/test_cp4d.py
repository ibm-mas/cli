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

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException


class TestCollectCP4D:
    """Test IBM CloudPak for Data collection functionality."""

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

    def test_collect_cp4d_when_namespace_exists(self):
        """Test collection when ibm-cpd-operators namespace exists.

        GIVEN ibm-cpd-operators namespace exists
        WHEN collectCP4D is called
        THEN resources are collected from ibm-cpd and ibm-cpd-operators namespaces.
        """
        from mas.cli.must_gather.dependencies.cp4d import collectCP4D

        # Mock namespace lookup
        mockNamespaceApi = Mock()
        mockNamespace = self._createMockNamespace("ibm-cpd-operators")
        mockNamespaceApi.get.return_value = mockNamespace

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        # Mock genericMustGather
        mockGenericMustGather = Mock(return_value=True)

        result = collectCP4D(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False, genericMustGather=mockGenericMustGather)

        assert result is True
        assert mockGenericMustGather.call_count == 2
        mockGenericMustGather.assert_any_call(namespace="ibm-cpd", outputDir=self.testDir, noDetail=False)
        mockGenericMustGather.assert_any_call(namespace="ibm-cpd-operators", outputDir=self.testDir, noDetail=False)

    def test_collect_cp4d_when_namespace_not_found(self):
        """Test collection when ibm-cpd-operators namespace does not exist.

        GIVEN ibm-cpd-operators namespace does not exist
        WHEN collectCP4D is called
        THEN collection is skipped and returns False.
        """
        from mas.cli.must_gather.dependencies.cp4d import collectCP4D

        # Mock namespace lookup to raise NotFoundError
        mockNamespaceApi = Mock()
        mockNamespaceApi.get.side_effect = ApiException(status=404, reason="Not Found")

        def mockGetResource(kind, **kwargs):
            if kind == "Namespace":
                return mockNamespaceApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        result = collectCP4D(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is False
