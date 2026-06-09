# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Certificate Manager collection plan integration."""

from unittest.mock import MagicMock, Mock
from mas.cli.must_gather.collection_plan import CollectionPlan


class TestAddCertManagerToCollectionPlan:
    """Test Certificate Manager collection plan integration."""

    def test_addCertManagerToCollectionPlan_adds_groups_for_discovered_namespaces(self):
        """Test that Certificate Manager namespaces are added to collection plan.

        GIVEN Certificate Manager namespaces exist
        WHEN addCertManagerToCollectionPlan is called
        THEN collection groups are added for each namespace.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock namespace discovery
        mockNamespace1 = Mock()
        mockNamespace1.metadata.name = "cert-manager"
        mockNamespace2 = Mock()
        mockNamespace2.metadata.name = "cert-manager-operator"

        mockClient.resources.get.return_value.get.return_value.items = [mockNamespace1, mockNamespace2]

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        assert plan.total_groups == 2
        assert plan.total_tasks > 0

    def test_addCertManagerToCollectionPlan_handles_no_namespaces(self):
        """Test that no groups are added when no Certificate Manager namespaces exist.

        GIVEN no Certificate Manager namespaces exist
        WHEN addCertManagerToCollectionPlan is called
        THEN no collection groups are added.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan
        from kubernetes.client.exceptions import ApiException

        mockClient = MagicMock()
        plan = CollectionPlan()
        ibmCRDs = []

        # Mock namespace not found - checkNamespaceExists will raise 404
        mockError = ApiException(status=404)
        mockClient.resources.get.return_value.get.side_effect = mockError

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=ibmCRDs,
        )

        assert plan.total_groups == 0
        assert plan.total_tasks == 0
