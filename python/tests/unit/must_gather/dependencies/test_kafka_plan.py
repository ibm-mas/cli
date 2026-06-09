# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Kafka collection plan integration."""

from unittest.mock import MagicMock, Mock
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestAddKafkaToCollectionPlan:
    """Test Kafka collection plan integration."""

    def test_addKafkaToCollectionPlan_adds_groups_for_discovered_namespaces(self):
        """Test that Kafka namespaces are added to collection plan.

        GIVEN Kafka namespaces exist
        WHEN addKafkaToCollectionPlan is called
        THEN collection groups are added for each namespace.
        """
        from mas.cli.must_gather.dependencies.kafka import addKafkaToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock discovery to return namespaces
        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi

        # Create mock Kafka resources
        mockKafka1 = Mock()
        mockKafka1.metadata.namespace = "kafka-ns1"
        mockKafka2 = Mock()
        mockKafka2.metadata.namespace = "kafka-ns2"

        mockApi.get.return_value.items = [mockKafka1, mockKafka2]

        addKafkaToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        # Should have added 2 groups (one per namespace)
        assert (
            plan.total_groups == 2
        ), f"Collection plan should add one group per Kafka namespace (2 namespaces discovered), but got {plan.total_groups} group(s)"
        assert plan.total_tasks > 0, "Collection plan should generate tasks for Kafka namespaces, but no tasks were generated"

    def test_addKafkaToCollectionPlan_handles_no_namespaces(self):
        """Test that no groups are added when no Kafka namespaces exist.

        GIVEN no Kafka namespaces exist
        WHEN addKafkaToCollectionPlan is called
        THEN no collection groups are added.
        """
        from mas.cli.must_gather.dependencies.kafka import addKafkaToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock discovery to return no namespaces
        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []

        addKafkaToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        # Should have added no groups
        assert plan.total_groups == 0, f"Collection plan should not add groups when no Kafka namespaces exist, but got {plan.total_groups} group(s)"
        assert plan.total_tasks == 0, f"Collection plan should not generate tasks when no Kafka namespaces exist, but got {plan.total_tasks} task(s)"
