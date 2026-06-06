# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Apps collector."""

import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException
from mas.cli.must_gather.mas.apps import discoverMASAppNamespaces, collectMASApp


class TestDiscoverMASAppNamespaces:
    """Tests for MAS App namespace discovery."""

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

    def test_discover_all_apps_for_instance(self):
        """Test discovering all app namespaces for a MAS instance.

        GIVEN a MAS instance with multiple app namespaces
        WHEN discoverMASAppNamespaces is called without app filter
        THEN all app namespaces for that instance are returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst1-manage"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "mas-inst1-iot"
        mockNs4 = MagicMock()
        mockNs4.metadata.name = "mas-inst2-manage"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3, mockNs4])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASAppNamespaces(self.mockClient, masInstanceId="inst1")

        assert namespaces == {"mas-inst1-manage", "mas-inst1-iot"}

    def test_discover_filtered_apps_for_instance(self):
        """Test discovering specific app namespaces for a MAS instance.

        GIVEN a MAS instance with multiple app namespaces and app filter
        WHEN discoverMASAppNamespaces is called with specific app IDs
        THEN only filtered app namespaces are returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst1-manage"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "mas-inst1-iot"
        mockNs4 = MagicMock()
        mockNs4.metadata.name = "mas-inst1-monitor"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3, mockNs4])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASAppNamespaces(self.mockClient, masInstanceId="inst1", masAppIds=["manage", "iot"])

        assert namespaces == {"mas-inst1-manage", "mas-inst1-iot"}

    def test_discover_no_app_namespaces(self):
        """Test discovering app namespaces when none exist.

        GIVEN a MAS instance with no app namespaces
        WHEN discoverMASAppNamespaces is called
        THEN empty set is returned.
        """
        # Mock namespace API with only core namespace
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASAppNamespaces(self.mockClient, masInstanceId="inst1")

        assert namespaces == set()

    def test_discover_handles_api_exception(self):
        """Test app namespace discovery handles API exceptions.

        GIVEN API call fails
        WHEN discoverMASAppNamespaces is called
        THEN empty set is returned and error is logged.
        """
        # Mock namespace API to raise exception
        mockNamespaceApi = MagicMock()
        mockNamespaceApi.get.side_effect = ApiException(status=403, reason="Forbidden")

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASAppNamespaces(self.mockClient, masInstanceId="inst1")

        assert namespaces == set()


class TestCollectMASApp:
    """Tests for MAS App resource collection."""

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

    def test_collect_mas_app_calls_generic_must_gather(self):
        """Test MAS App collection calls genericMustGather.

        GIVEN a MAS app namespace and genericMustGather function
        WHEN collectMASApp is called
        THEN genericMustGather is called with correct parameters.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        result = collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=False,
            genericMustGather=mockGenericMustGather,
        )

        assert result is True
        # Verify generic collection was called with correct parameters
        mockGenericMustGather.assert_called_once_with(
            namespace="mas-inst1-manage",
            outputDir=self.testDir,
            noDetail=False,
            podsOnly=False,
            noLogs=False,
            additionalResources=[],
        )

    def test_collect_mas_app_respects_no_detail_flag(self):
        """Test MAS App collection respects --no-detail flag.

        GIVEN --no-detail flag is set
        WHEN collectMASApp is called
        THEN noDetail parameter is passed to genericMustGather.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=True,
            noLogs=False,
            genericMustGather=mockGenericMustGather,
        )

        # Verify noDetail was passed to genericMustGather
        mockGenericMustGather.assert_called_once()
        call_kwargs = mockGenericMustGather.call_args[1]
        assert call_kwargs["noDetail"] is True

    def test_collect_mas_app_respects_no_logs_flag(self):
        """Test MAS App collection respects --no-logs flag.

        GIVEN --no-logs flag is set
        WHEN collectMASApp is called
        THEN noLogs parameter is passed to genericMustGather.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=True,
            genericMustGather=mockGenericMustGather,
        )

        # Verify noLogs was passed to genericMustGather
        mockGenericMustGather.assert_called_once()
        call_kwargs = mockGenericMustGather.call_args[1]
        assert call_kwargs["noLogs"] is True

    def test_collect_mas_app_without_generic_must_gather(self):
        """Test MAS App collection when genericMustGather is not provided.

        GIVEN genericMustGather is None
        WHEN collectMASApp is called
        THEN function returns True and logs warning.
        """
        result = collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=False,
            genericMustGather=None,
        )

        assert result is True

    def test_collect_mas_app_handles_generic_must_gather_failure(self):
        """Test MAS App collection handles genericMustGather failure.

        GIVEN genericMustGather returns False
        WHEN collectMASApp is called
        THEN function returns False.
        """
        # Mock genericMustGather function to return False
        mockGenericMustGather = Mock(return_value=False)

        result = collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=False,
            genericMustGather=mockGenericMustGather,
        )

        assert result is False

    def test_collect_mas_app_handles_exception(self):
        """Test MAS App collection handles exceptions.

        GIVEN genericMustGather raises exception
        WHEN collectMASApp is called
        THEN function returns False and logs error.
        """
        # Mock genericMustGather function to raise exception
        mockGenericMustGather = Mock(side_effect=Exception("Test error"))

        result = collectMASApp(
            dynClient=self.mockClient,
            namespace="mas-inst1-manage",
            appId="manage",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=False,
            genericMustGather=mockGenericMustGather,
        )

        assert result is False
