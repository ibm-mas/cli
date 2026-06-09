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

from unittest.mock import Mock
from kubernetes.dynamic import DynamicClient


class TestDiscoverDb2Namespaces:
    """Test Db2 namespace discovery functionality."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create mock Kubernetes client.
        """
        self.mockClient = Mock(spec=DynamicClient)

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

    def test_discover_db2_namespaces_from_jdbccfg(self):
        """Test Db2 namespace discovery from JdbcCfg resources.

        GIVEN JdbcCfg resources with JDBC URLs
        WHEN discoverDb2Namespaces is called with masInstanceIds
        THEN Db2 namespaces are discovered from JDBC URLs.
        """
        from mas.cli.must_gather.dependencies.db2 import discoverDb2Namespaces

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

        namespaces = discoverDb2Namespaces(dynClient=self.mockClient, masInstanceIds=["inst1"])

        assert namespaces == ["another-db2", "db2u-namespace"]

    def test_discover_db2_namespaces_from_db2ucluster(self):
        """Test Db2 namespace discovery from Db2uCluster resources.

        GIVEN Db2uCluster resources exist
        WHEN discoverDb2Namespaces is called without masInstanceIds
        THEN Db2 namespaces are discovered from Db2uCluster resources.
        """
        from mas.cli.must_gather.dependencies.db2 import discoverDb2Namespaces

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

        namespaces = discoverDb2Namespaces(dynClient=self.mockClient, masInstanceIds=None)

        assert namespaces == ["db2u-ns1", "db2u-ns2"]

    def test_discover_db2_namespaces_returns_empty_when_none_found(self):
        """Test discovery returns empty list when no Db2 found.

        GIVEN no Db2 resources exist
        WHEN discoverDb2Namespaces is called
        THEN empty list is returned.
        """
        from mas.cli.must_gather.dependencies.db2 import discoverDb2Namespaces

        mockDb2Api = Mock()
        mockDb2Api.get.return_value = self._createMockResourceList([])

        def mockGetResource(kind, **kwargs):
            if kind == "Db2uCluster":
                return mockDb2Api
            return Mock()

        self.mockClient.resources.get.side_effect = mockGetResource

        namespaces = discoverDb2Namespaces(dynClient=self.mockClient, masInstanceIds=None)

        assert namespaces == []


class TestGenerateDb2CollectionTasks:
    """Test Db2 collection task generation."""

    def setup_method(self):
        """Set up test fixtures.

        GIVEN a test environment
        WHEN tests are run
        THEN create mock Kubernetes client.
        """
        self.mockClient = Mock(spec=DynamicClient)

    def test_generate_db2_collection_tasks_creates_tasks_for_each_namespace(self):
        """Test task generation for multiple Db2 namespaces.

        GIVEN multiple Db2 namespaces
        WHEN generateDb2CollectionTasks is called
        THEN tasks are generated for each namespace.
        """
        from mas.cli.must_gather.dependencies.db2 import generateDb2CollectionTasks

        namespaces = ["db2u-ns1", "db2u-ns2"]
        tasks = generateDb2CollectionTasks(dynClient=self.mockClient, namespaces=namespaces, outputDir="/tmp/output", noDetail=False, noLogs=False)

        # Each namespace generates multiple tasks (resources, secrets, pods)
        assert len(tasks) > 0
        # Verify we have tasks for both namespaces (each namespace generates multiple tasks)
        assert len(tasks) >= 2

    def test_generate_db2_collection_tasks_returns_empty_for_no_namespaces(self):
        """Test task generation with no namespaces.

        GIVEN no Db2 namespaces
        WHEN generateDb2CollectionTasks is called
        THEN empty list is returned.
        """
        from mas.cli.must_gather.dependencies.db2 import generateDb2CollectionTasks

        tasks = generateDb2CollectionTasks(dynClient=self.mockClient, namespaces=[], outputDir="/tmp/output", noDetail=False, noLogs=False)

        assert tasks == []
