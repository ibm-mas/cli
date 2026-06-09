# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for collection planning functionality."""

from unittest.mock import Mock
from mas.cli.must_gather.collection_plan import CollectionPlan
from mas.cli.must_gather.common.task_generation import generateNamespaceCollectionTasks


def test_collection_plan_can_be_built_with_namespace_tasks():
    """Test that a collection plan can be built with namespace tasks.

    GIVEN discovered namespaces
    WHEN building a collection plan using generateNamespaceCollectionTasks
    THEN tasks are added for each namespace.
    """
    dynClient = Mock()
    outputDir = "/tmp/output"
    plan = CollectionPlan()

    # Simulate discovered namespaces
    namespaces = {"strimzi", "kafka-system"}

    for namespace in namespaces:
        tasks = generateNamespaceCollectionTasks(
            dynClient=dynClient,
            namespace=namespace,
            outputDir=outputDir,
            noDetail=False,
            noLogs=False,
            includeSecrets=True,
            secretData=False,
            customResources=None,
            ibmCRDs=None,
        )
        plan.addGroup(f"Namespace ({namespace})", tasks)

    assert plan.total_groups == 2
    assert plan.total_tasks >= 4  # At least IBM resources, standard resources, secrets, pods per namespace


def test_collection_plan_preserves_task_order():
    """Test that collection plan preserves task order within groups.

    GIVEN tasks added to a collection plan
    WHEN retrieving tasks from a group
    THEN tasks are in the same order they were added.
    """
    dynClient = Mock()

    # Mock the Pod API to return an empty list
    mockPodApi = Mock()
    mockPodList = Mock()
    mockPodList.items = []
    mockPodApi.get.return_value = mockPodList

    # Configure dynClient to return the mock API
    dynClient.resources.get.return_value = mockPodApi

    outputDir = "/tmp/output"
    plan = CollectionPlan()

    # Provide some IBM CRDs so ibm_resources task is generated
    ibmCRDs = [("apps.mas.ibm.com/v1", "Suite")]

    tasks = generateNamespaceCollectionTasks(
        dynClient=dynClient,
        namespace="strimzi",
        outputDir=outputDir,
        noDetail=False,
        noLogs=False,
        includeSecrets=True,
        secretData=False,
        customResources=None,
        ibmCRDs=ibmCRDs,
    )

    plan.addGroup("Namespace (strimzi)", tasks)

    # Verify task order: IBM CRDs first, then standard resources, then secrets
    # Note: pods task is not generated when there are no pods (0 pod collection tasks)
    # With the new implementation, each resource type gets its own task instead of grouped tasks
    group = plan.groups[0]
    taskNames = [task[0] for task in group.tasks]

    # Should have: 1 IBM CRD task (ibm_suite) + 17 standard resource tasks + 1 secrets task = 19 tasks
    assert len(taskNames) == 19

    # Verify IBM CRDs come first
    assert taskNames[0] == "ibm_suite"

    # Verify standard resources follow (checking a few key ones)
    assert "std_configmap" in taskNames
    assert "std_deployment" in taskNames
    assert "std_service" in taskNames

    # Verify secrets comes last
    assert taskNames[-1] == "secrets"
