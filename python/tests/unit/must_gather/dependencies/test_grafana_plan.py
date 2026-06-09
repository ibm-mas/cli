# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Grafana collection plan integration."""

from unittest.mock import MagicMock, Mock
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestAddGrafanaToCollectionPlan:
    """Test Grafana collection plan integration."""

    def test_addGrafanaToCollectionPlan_adds_groups_for_discovered_namespaces(self):
        """Test that Grafana namespaces are added to collection plan.

        GIVEN Grafana namespaces exist
        WHEN addGrafanaToCollectionPlan is called
        THEN collection groups are added for each namespace.
        """
        from mas.cli.must_gather.dependencies.grafana import addGrafanaToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock discovery to return namespaces
        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi

        mockGrafana1 = Mock()
        mockGrafana1.metadata.namespace = "grafana-ns1"
        mockGrafana2 = Mock()
        mockGrafana2.metadata.namespace = "grafana-ns2"

        mockApi.get.return_value.items = [mockGrafana1, mockGrafana2]

        addGrafanaToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noDetail=False,
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        assert plan.total_groups == 2
        assert plan.total_tasks > 0

    def test_addGrafanaToCollectionPlan_handles_no_namespaces(self):
        """Test that no groups are added when no Grafana namespaces exist.

        GIVEN no Grafana namespaces exist
        WHEN addGrafanaToCollectionPlan is called
        THEN no collection groups are added.
        """
        from mas.cli.must_gather.dependencies.grafana import addGrafanaToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        mockApi = MagicMock()
        mockClient.resources.get.return_value = mockApi
        mockApi.get.return_value.items = []

        addGrafanaToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noDetail=False,
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        assert plan.total_groups == 0
        assert plan.total_tasks == 0
