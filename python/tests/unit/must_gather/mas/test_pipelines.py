# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Pipelines collector."""

import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException
from mas.cli.must_gather.mas.pipelines import discoverMASPipelineNamespaces, collectMASPipelines


class TestDiscoverMASPipelineNamespaces:
    """Tests for MAS Pipeline namespace discovery."""

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

    def test_discover_instance_pipeline_namespaces(self):
        """Test discovering instance-specific pipeline namespaces.

        GIVEN MAS instances with pipeline namespaces
        WHEN discoverMASPipelineNamespaces is called with instance IDs
        THEN instance-specific pipeline namespaces are returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst2-pipelines"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "mas-pipelines"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASPipelineNamespaces(self.mockClient, masInstanceIds=["inst1", "inst2"])

        assert namespaces == {"mas-inst1-pipelines", "mas-inst2-pipelines"}

    def test_discover_cluster_level_pipeline_namespace(self):
        """Test discovering cluster-level pipeline namespace.

        GIVEN cluster-level mas-pipelines namespace exists
        WHEN discoverMASPipelineNamespaces is called with includeClusterLevel=True
        THEN mas-pipelines namespace is included.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-pipelines"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASPipelineNamespaces(self.mockClient, masInstanceIds=["inst1"], includeClusterLevel=True)

        assert namespaces == {"mas-inst1-pipelines", "mas-pipelines"}

    def test_discover_all_pipeline_namespaces(self):
        """Test discovering all pipeline namespaces.

        GIVEN multiple pipeline namespaces exist
        WHEN discoverMASPipelineNamespaces is called without filters
        THEN all pipeline namespaces are returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-pipelines"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst2-pipelines"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "mas-pipelines"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASPipelineNamespaces(self.mockClient, includeClusterLevel=True)

        assert namespaces == {"mas-inst1-pipelines", "mas-inst2-pipelines", "mas-pipelines"}

    def test_discover_no_pipeline_namespaces(self):
        """Test discovering pipeline namespaces when none exist.

        GIVEN no pipeline namespaces exist
        WHEN discoverMASPipelineNamespaces is called
        THEN empty set is returned.
        """
        # Mock namespace API with no pipeline namespaces
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASPipelineNamespaces(self.mockClient)

        assert namespaces == set()

    def test_discover_handles_api_exception(self):
        """Test pipeline namespace discovery handles API exceptions.

        GIVEN API call fails
        WHEN discoverMASPipelineNamespaces is called
        THEN empty set is returned and error is logged.
        """
        # Mock namespace API to raise exception
        mockNamespaceApi = MagicMock()
        mockNamespaceApi.get.side_effect = ApiException(status=403, reason="Forbidden")

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASPipelineNamespaces(self.mockClient)

        assert namespaces == set()


class TestCollectMASPipelines:
    """Tests for MAS Pipelines resource collection."""

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

    def test_collect_mas_pipelines_namespace(self):
        """Test MAS Pipelines collection from a namespace.

        GIVEN a MAS pipelines namespace exists
        WHEN collectMASPipelines is called
        THEN pipeline resources are collected using genericMustGather.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        result = collectMASPipelines(
            dynClient=self.mockClient,
            namespace="mas-inst1-pipelines",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=False,
            genericMustGather=mockGenericMustGather,
        )

        assert result is True
        # Verify generic collection was called
        mockGenericMustGather.assert_called_once()

    def test_collect_mas_pipelines_respects_no_logs_flag(self):
        """Test MAS Pipelines collection respects --no-logs flag.

        GIVEN --no-logs flag is set
        WHEN collectMASPipelines is called
        THEN noLogs parameter is passed to genericMustGather.
        """
        # Mock genericMustGather function
        mockGenericMustGather = Mock(return_value=True)

        collectMASPipelines(
            dynClient=self.mockClient,
            namespace="mas-inst1-pipelines",
            outputDir=self.testDir,
            noDetail=False,
            noLogs=True,
            genericMustGather=mockGenericMustGather,
        )

        # Verify noLogs was passed to genericMustGather
        mockGenericMustGather.assert_called_once()
        call_kwargs = mockGenericMustGather.call_args[1]
        assert call_kwargs["noLogs"] is True

    def test_collect_mas_pipelines_without_generic_must_gather(self):
        """Test MAS Pipelines collection without genericMustGather function.

        GIVEN no genericMustGather function is provided
        WHEN collectMASPipelines is called
        THEN collection returns True with warning.
        """
        result = collectMASPipelines(dynClient=self.mockClient, namespace="mas-inst1-pipelines", outputDir=self.testDir, noDetail=False, noLogs=False)

        assert result is True
