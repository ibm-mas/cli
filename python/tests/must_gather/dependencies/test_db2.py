# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test IBM Db2 Universal Operator dependency collector."""

import os
import tempfile
import shutil
from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestCollectDb2:
    """Test IBM Db2 collection functionality."""

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

    def _createMockResource(self, name: str, namespace: str, spec: dict = None):  # type: ignore
        """Create a mock Kubernetes resource.

        Args:
            name (str): Resource name
            namespace (str): Resource namespace
            spec (dict, optional): Resource spec. Defaults to None.

        Returns:
            Mock: Mock resource object
        """
        mockResource = Mock()
        mockResource.metadata = Mock()
        mockResource.metadata.name = name
        mockResource.metadata.namespace = namespace

        resourceDict = {"metadata": {"name": name, "namespace": namespace}}
        if spec:
            resourceDict["spec"] = spec

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
        return mockList

    def test_collect_db2_discovers_from_jdbccfg(self):
        """Test Db2 namespace discovery from JdbcCfg resources.

        GIVEN JdbcCfg resources with JDBC URLs
        WHEN collectDb2 is called with masInstanceIds
        THEN Db2 namespaces are discovered from JDBC URLs and collected.
        """
        from mas.cli.must_gather.dependencies.db2 import collectDb2

        # Mock JdbcCfg resources with JDBC URLs
        jdbcUrl1 = "jdbc:db2://c-db2u-db2u.db2u-namespace.svc:50001/BLUDB"
        jdbcUrl2 = "jdbc:db2://c-db2u-db2u.another-db2.svc:50001/TESTDB"

        jdbcCfg1 = self._createMockResource("jdbc1", "mas-inst1-core", spec={"config": {"url": jdbcUrl1}})
        jdbcCfg2 = self._createMockResource("jdbc2", "mas-inst1-core", spec={"config": {"url": jdbcUrl2}})

        mockJdbcApi = Mock()
        mockJdbcApi.get.return_value = self._createMockResourceList([jdbcCfg1, jdbcCfg2])

        def mockGetResource(kind, **kwargs):
            if kind == "JdbcCfg":
                return mockJdbcApi
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        # Mock genericMustGather
        mockGenericMustGather = Mock(return_value=True)

        result = collectDb2(
            dynClient=self.mockClient, outputDir=self.testDir, noDetail=False, masInstanceIds=["inst1"], genericMustGather=mockGenericMustGather
        )

        assert result is True
        # Should collect from both discovered namespaces
        assert mockGenericMustGather.call_count == 2

    def test_collect_db2_discovers_from_db2ucluster(self):
        """Test Db2 namespace discovery from Db2uCluster resources.

        GIVEN Db2uCluster resources exist
        WHEN collectDb2 is called without masInstanceIds
        THEN Db2 namespaces are discovered from Db2uCluster resources.
        """
        from mas.cli.must_gather.dependencies.db2 import collectDb2

        # Mock Db2uCluster resources
        db2Cluster1 = self._createMockResource("cluster1", "db2u-ns1")
        db2Cluster2 = self._createMockResource("cluster2", "db2u-ns2")

        mockDb2Api = Mock()
        mockDb2Api.get.return_value = self._createMockResourceList([db2Cluster1, db2Cluster2])

        def mockGetResource(kind, **kwargs):
            if kind == "Db2uCluster":
                return mockDb2Api
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        # Mock genericMustGather
        mockGenericMustGather = Mock(return_value=True)

        result = collectDb2(dynClient=self.mockClient, outputDir=self.testDir, noDetail=False, masInstanceIds=None, genericMustGather=mockGenericMustGather)

        assert result is True
        assert mockGenericMustGather.call_count == 2
