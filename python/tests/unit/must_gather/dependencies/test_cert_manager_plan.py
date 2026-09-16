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
from mas.cli.must_gather.common.resources import collectResources


class TestAddCertManagerToCollectionPlan:
    """Test Certificate Manager collection plan integration."""

    def test_addCertManagerToCollectionPlan_adds_groups_for_discovered_namespaces(self):
        """Test that Certificate Manager namespaces and all-namespaces group are added to collection plan.

        GIVEN Certificate Manager namespaces exist
        WHEN addCertManagerToCollectionPlan is called
        THEN one collection group per namespace plus one all-namespaces group are added.
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

        # 2 namespace groups + 1 all-namespaces group
        assert (
            plan.total_groups == 3
        ), f"Collection plan should add one group per namespace (2) plus one all-namespaces group, but got {plan.total_groups} group(s)"
        assert plan.total_tasks > 0, "Collection plan should generate tasks for Certificate Manager namespaces, but no tasks were generated"

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

        assert (
            plan.total_groups == 0
        ), f"Collection plan should not add groups when no Certificate Manager namespaces exist, but got {plan.total_groups} group(s)"
        assert (
            plan.total_tasks == 0
        ), f"Collection plan should not generate tasks when no Certificate Manager namespaces exist, but got {plan.total_tasks} task(s)"

    def test_addCertManagerToCollectionPlan_adds_all_namespace_group(self):
        """Test that an all-namespaces group is added when cert-manager is installed.

        GIVEN a Certificate Manager namespace exists
        WHEN addCertManagerToCollectionPlan is called
        THEN a group named 'Certificate Manager (all namespaces)' is present in the plan.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        mockClient.resources.get.return_value.get.return_value.items = [Mock()]

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=[],
        )

        groupNames = [g.name for g in plan.groups]
        assert (
            "Certificate Manager (all namespaces)" in groupNames
        ), f"Expected a 'Certificate Manager (all namespaces)' group in the plan, but got: {groupNames}"

    def test_addCertManagerToCollectionPlan_no_all_namespace_group_when_no_cert_manager(self):
        """Test that no all-namespaces group is added when cert-manager is not installed.

        GIVEN no Certificate Manager namespaces exist
        WHEN addCertManagerToCollectionPlan is called
        THEN no 'Certificate Manager (all namespaces)' group is added.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan
        from kubernetes.client.exceptions import ApiException

        mockClient = MagicMock()
        plan = CollectionPlan()
        mockClient.resources.get.return_value.get.side_effect = ApiException(status=404)

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=[],
        )

        groupNames = [g.name for g in plan.groups]
        assert (
            "Certificate Manager (all namespaces)" not in groupNames
        ), f"Expected no 'Certificate Manager (all namespaces)' group when cert-manager is not installed, but got: {groupNames}"

    def test_addCertManagerToCollectionPlan_all_namespace_tasks_use_allNamespaces_flag(self):
        """Test that all-namespace group tasks call collectResources with namespace=None and allNamespaces=True.

        The namespace=None causes output to land in resources/_cluster/ which is semantically
        correct since the data spans all namespaces, not a single one.

        GIVEN a Certificate Manager namespace exists
        WHEN addCertManagerToCollectionPlan is called
        THEN every task in the all-namespaces group uses collectResources with
             namespace=None (so output goes to resources/_cluster/) and allNamespaces=True.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan, CERT_MANAGER_ALL_NAMESPACE_RESOURCES

        mockClient = MagicMock()
        plan = CollectionPlan()
        mockClient.resources.get.return_value.get.return_value.items = [Mock()]

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=[],
        )

        allNsGroup = next(g for g in plan.groups if g.name == "Certificate Manager (all namespaces)")

        # Each task tuple is: (task_name, func, namespace, apiVersion, kind, outputDir, allNamespaces)
        assert len(allNsGroup.tasks) == len(
            CERT_MANAGER_ALL_NAMESPACE_RESOURCES
        ), f"Expected {len(CERT_MANAGER_ALL_NAMESPACE_RESOURCES)} all-namespace tasks, got {len(allNsGroup.tasks)}"
        for task in allNsGroup.tasks:
            _taskName, func, namespace, _apiVersion, _kind, _outputDir, allNamespaces = task
            assert func is collectResources, f"Expected collectResources as task function, got {func}"
            assert namespace is None, f"Expected namespace=None so output is written to resources/_cluster/, got namespace={namespace!r}"
            assert allNamespaces is True, f"Expected allNamespaces=True for all-namespace task, got {allNamespaces!r}"

    def test_addCertManagerToCollectionPlan_namespace_groups_collect_clusterissuer_and_certmanager(self):
        """Test that per-namespace groups include ClusterIssuer and CertManager resource tasks.

        GIVEN a Certificate Manager namespace exists
        WHEN addCertManagerToCollectionPlan is called
        THEN the namespace collection group tasks include ClusterIssuer and CertManager kinds.
        """
        from mas.cli.must_gather.dependencies.cert_manager import addCertManagerToCollectionPlan

        mockClient = MagicMock()
        plan = CollectionPlan()
        mockClient.resources.get.return_value.get.return_value.items = [Mock()]

        addCertManagerToCollectionPlan(
            plan=plan,
            dynClient=mockClient,
            outputDir="/tmp/output",
            noLogs=False,
            ibmCRDs=[],
        )

        nsGroups = [g for g in plan.groups if g.name != "Certificate Manager (all namespaces)"]
        assert len(nsGroups) >= 1, "Expected at least one namespace group"

        # Collect all kinds targeted by collectResources tasks in the namespace groups
        nsGroupKinds = set()
        for group in nsGroups:
            for task in group.tasks:
                if task[1] is collectResources:
                    # task: (task_name, func, namespace, apiVersion, kind, outputDir, allNamespaces)
                    nsGroupKinds.add(task[4])

        assert "ClusterIssuer" in nsGroupKinds, f"Expected ClusterIssuer in namespace group tasks, got: {nsGroupKinds}"
        assert "CertManager" in nsGroupKinds, f"Expected CertManager in namespace group tasks, got: {nsGroupKinds}"
