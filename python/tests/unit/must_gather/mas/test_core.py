# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MAS Core collector."""

import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from kubernetes.dynamic import DynamicClient
from kubernetes.client.exceptions import ApiException
from mas.cli.must_gather.mas.core import discoverMASCoreNamespaces, collectMASCore, generateMASCoreSummary


class TestDiscoverMASCoreNamespaces:
    """Tests for MAS Core namespace discovery."""

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

    def test_discover_with_specific_instance_ids(self):
        """Test MAS Core namespace discovery with specific instance IDs.

        GIVEN specific MAS instance IDs are provided
        WHEN discoverMASCoreNamespaces is called
        THEN only namespaces for those instances are returned.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst2-core"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "mas-inst3-core"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASCoreNamespaces(self.mockClient, masInstanceIds=["inst1", "inst2"])

        assert namespaces == {"mas-inst1-core", "mas-inst2-core"}

    def test_discover_all_instances(self):
        """Test MAS Core namespace discovery without specific instance IDs.

        GIVEN no specific MAS instance IDs are provided
        WHEN discoverMASCoreNamespaces is called
        THEN all mas-*-core namespaces are discovered.
        """
        # Mock namespace API
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "mas-inst1-core"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "mas-inst2-core"
        mockNs3 = MagicMock()
        mockNs3.metadata.name = "openshift-operators"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2, mockNs3])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASCoreNamespaces(self.mockClient)

        assert namespaces == {"mas-inst1-core", "mas-inst2-core"}

    def test_discover_no_mas_namespaces(self):
        """Test MAS Core namespace discovery when no MAS namespaces exist.

        GIVEN no MAS Core namespaces exist
        WHEN discoverMASCoreNamespaces is called
        THEN empty set is returned.
        """
        # Mock namespace API with no MAS namespaces
        mockNamespaceApi = MagicMock()
        mockNs1 = MagicMock()
        mockNs1.metadata.name = "openshift-operators"
        mockNs2 = MagicMock()
        mockNs2.metadata.name = "default"
        mockNamespaceApi.get.return_value = MagicMock(items=[mockNs1, mockNs2])

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASCoreNamespaces(self.mockClient)

        assert namespaces == set()

    def test_discover_handles_api_exception(self):
        """Test MAS Core namespace discovery handles API exceptions.

        GIVEN API call fails
        WHEN discoverMASCoreNamespaces is called
        THEN empty set is returned and error is logged.
        """
        # Mock namespace API to raise exception
        mockNamespaceApi = MagicMock()
        mockNamespaceApi.get.side_effect = ApiException(status=403, reason="Forbidden")

        self.mockClient.resources.get.return_value = mockNamespaceApi

        namespaces = discoverMASCoreNamespaces(self.mockClient)

        assert namespaces == set()


class TestCollectMASCore:
    """Tests for MAS Core resource collection."""

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

    def test_collect_mas_core_namespace(self):
        """Test MAS Core resource collection from a namespace.

        GIVEN a MAS Core namespace exists
        WHEN collectMASCore is called
        THEN Suite CR and standard resources are collected.
        """
        # Mock Suite API
        mockSuiteApi = MagicMock()
        mockSuite = MagicMock()
        mockSuite.metadata.name = "inst1"
        mockSuite.metadata.namespace = "mas-inst1-core"
        mockSuite.spec.version = "9.0.0"
        mockSuite.status.conditions = [{"type": "Ready", "status": "True"}]
        mockSuiteApi.get.return_value = MagicMock(items=[mockSuite])

        # Configure mock client
        def get_resource(api_version=None, kind=None):
            if kind == "Suite":
                return mockSuiteApi
            raise ApiException(status=404)

        self.mockClient.resources.get.side_effect = get_resource

        result = collectMASCore(dynClient=self.mockClient, namespace="mas-inst1-core", outputDir=self.testDir, noDetail=False)

        assert result is True

    def test_collect_mas_core_no_suite_cr(self):
        """Test MAS Core collection when Suite CR doesn't exist.

        GIVEN a namespace without Suite CR
        WHEN collectMASCore is called
        THEN collection continues without error.
        """
        # Mock Suite API with no items
        mockSuiteApi = MagicMock()
        mockSuiteApi.get.return_value = MagicMock(items=[])

        self.mockClient.resources.get.return_value = mockSuiteApi

        result = collectMASCore(dynClient=self.mockClient, namespace="mas-inst1-core", outputDir=self.testDir, noDetail=False)

        assert result is True


class TestGenerateMASCoreSummary:
    """Tests for MAS Core summary generation."""

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

    def test_generate_summary_with_suites(self):
        """Test MAS Core summary generation with Suite CRs.

        GIVEN Suite CRs exist in namespaces
        WHEN generateMASCoreSummary is called
        THEN summary file is created with Suite information.
        """
        # Mock Suite API
        mockSuiteApi = MagicMock()
        mockSuite1 = MagicMock()
        mockSuite1.metadata.name = "inst1"
        mockSuite1.metadata.namespace = "mas-inst1-core"
        mockSuite1.spec.version = "9.0.0"
        mockSuite1.status.conditions = [{"type": "Ready", "status": "True"}]

        mockSuite2 = MagicMock()
        mockSuite2.metadata.name = "inst2"
        mockSuite2.metadata.namespace = "mas-inst2-core"
        mockSuite2.spec.version = "8.11.0"
        mockSuite2.status.conditions = [{"type": "Ready", "status": "False"}]

        mockSuiteApi.get.return_value = MagicMock(items=[mockSuite1, mockSuite2])

        self.mockClient.resources.get.return_value = mockSuiteApi

        summaryFile = f"{self.testDir}/mas-core-summary.txt"
        generateMASCoreSummary(dynClient=self.mockClient, namespaces={"mas-inst1-core", "mas-inst2-core"}, outputFile=summaryFile)

        # Verify summary file was created
        import os

        assert os.path.exists(summaryFile)

        # Verify content
        with open(summaryFile, "r") as f:
            content = f.read()
            assert "inst1" in content
            assert "inst2" in content
            assert "9.0.0" in content
            assert "8.11.0" in content

    def test_generate_summary_no_suites(self):
        """Test MAS Core summary generation with no Suite CRs.

        GIVEN no Suite CRs exist
        WHEN generateMASCoreSummary is called
        THEN summary file is created with no instances message.
        """
        # Mock Suite API with no items
        mockSuiteApi = MagicMock()
        mockSuiteApi.get.return_value = MagicMock(items=[])

        self.mockClient.resources.get.return_value = mockSuiteApi

        summaryFile = f"{self.testDir}/mas-core-summary.txt"
        generateMASCoreSummary(dynClient=self.mockClient, namespaces=set(), outputFile=summaryFile)

        # Verify summary file was created
        import os

        assert os.path.exists(summaryFile)

        # Verify content
        with open(summaryFile, "r") as f:
            content = f.read()
            assert "No MAS instances found" in content or "0" in content
