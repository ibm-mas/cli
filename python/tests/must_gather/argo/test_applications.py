# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Argo applications collector."""

import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException
from mas.cli.must_gather.argo.applications import checkArgoNamespace, collectArgo


class TestCheckArgoNamespace:
    """Tests for Argo namespace detection."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN mock client is available.
        """
        self.mockClient = Mock(spec=DynamicClient)

    def test_argo_namespace_exists(self):
        """Test Argo namespace detection when namespace exists.

        GIVEN openshift-gitops namespace exists
        WHEN checkArgoNamespace is called
        THEN True is returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs = MagicMock()
        mockNs.metadata.name = "openshift-gitops"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        result = checkArgoNamespace(self.mockClient)

        assert result is True

    def test_argo_namespace_not_exists(self):
        """Test Argo namespace detection when namespace doesn't exist.

        GIVEN openshift-gitops namespace doesn't exist
        WHEN checkArgoNamespace is called
        THEN False is returned.
        """
        # Mock namespace API with no Argo namespace
        mockNamespaceApi = MagicMock()
        mockNs = MagicMock()
        mockNs.metadata.name = "default"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        result = checkArgoNamespace(self.mockClient)

        assert result is False

    def test_argo_namespace_check_handles_exception(self):
        """Test Argo namespace detection handles exceptions.

        GIVEN API call fails
        WHEN checkArgoNamespace is called
        THEN False is returned.
        """
        # Mock namespace API to raise exception
        mockNamespaceApi = MagicMock()
        mockNamespaceApi.get.side_effect = ApiException(status=403, reason="Forbidden")

        self.mockClient.resources.get.return_value = mockNamespaceApi

        result = checkArgoNamespace(self.mockClient)

        assert result is False


class TestCollectArgo:
    """Tests for Argo resource collection."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN mock client and temp directory are available.
        """
        self.mockClient = Mock(spec=DynamicClient)
        self.testDir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures.

        GIVEN test fixtures exist
        WHEN tests complete
        THEN temp directory is cleaned up.
        """
        shutil.rmtree(self.testDir, ignore_errors=True)

    def test_collect_argo_when_namespace_exists(self):
        """Test Argo collection when namespace exists.

        GIVEN openshift-gitops namespace exists
        WHEN collectArgo is called
        THEN resources are collected using genericMustGather.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        result = collectArgo(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False, genericMustGather=mockGenericMustGather)

        assert result is True
        # Verify generic collection was called
        mockGenericMustGather.assert_called_once()

    def test_collect_argo_without_generic_must_gather(self):
        """Test Argo collection without genericMustGather function.

        GIVEN no genericMustGather function is provided
        WHEN collectArgo is called
        THEN collection returns True with warning.
        """
        result = collectArgo(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False)

        assert result is True


# Made with Bob
