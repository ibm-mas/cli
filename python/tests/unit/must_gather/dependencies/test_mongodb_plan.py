# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for MongoDB collection plan integration."""

from unittest.mock import MagicMock, Mock
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestAddMongoDBToCollectionPlan:
    """Test MongoDB collection plan integration."""

    def test_addMongoDBToCollectionPlan_adds_groups_for_discovered_namespaces(self):
        """Test that MongoDB namespaces are added to collection plan.

        GIVEN MongoDB namespaces exist
        WHEN addMongoDBToCollectionPlan is called
        THEN collection groups are added for each namespace.
        """
        from mas.cli.must_gather.dependencies.mongodb import addMongoDBToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock discovery to return namespaces
        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi

        # Create mock MongoDB resources
        mockMongo1 = Mock()
        mockMongo1.metadata.namespace = "mongo-ns1"
        mockMongo2 = Mock()
        mockMongo2.metadata.namespace = "mongo-ns2"

        mockApi.get.return_value.items = [mockMongo1, mockMongo2]

        addMongoDBToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        # Should have added 2 groups (one per namespace)
        assert plan.total_groups == 2
        assert plan.total_tasks > 0

    def test_addMongoDBToCollectionPlan_handles_no_namespaces(self):
        """Test that no groups are added when no MongoDB namespaces exist.

        GIVEN no MongoDB namespaces exist
        WHEN addMongoDBToCollectionPlan is called
        THEN no collection groups are added.
        """
        from mas.cli.must_gather.dependencies.mongodb import addMongoDBToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock discovery to return no namespaces
        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []

        addMongoDBToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        # Should have added no groups
        assert plan.total_groups == 0
        assert plan.total_tasks == 0
