# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Common task generation utilities for must-gather collectors.

This module provides reusable functions for generating collection tasks
that can be executed in parallel for any namespace.
"""

from typing import List, Tuple, Optional
from kubernetes.dynamic import DynamicClient
from .resources import collectResources
from .secrets import collectSecrets
from .pods import generatePodCollectionTasks


def generateNamespaceCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noLogs: bool = False,
    secretData: bool = False,
    customResources: Optional[List[Tuple[str, str]]] = None,
    ibmCRDs: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple]:
    """Generate standard collection tasks for a namespace.

    Creates a list of collection tasks that can be executed in parallel
    for collecting resources from a namespace. This includes custom resources,
    standard Kubernetes resources, secrets (optional), and pods.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected resources
        noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
        secretData (bool, optional): If True, include secret data in YAML. Defaults to False.
        customResources (list, optional): Custom CRD tuples (apiVersion, kind) specific to this namespace type. Defaults to None.
        ibmCRDs (list, optional): Additional IBM CRD tuples (apiVersion, kind) to collect. Defaults to None.

    Returns:
        list: List of task tuples in format (task_name, func, *args)
    """
    tasks = []

    # Custom resources (namespace-specific CRDs + additional IBM CRDs)
    # Create individual tasks for each IBM CRD to avoid nested threadpools
    allCustomResources = []
    if customResources:
        allCustomResources.extend(customResources)
    if ibmCRDs:
        allCustomResources.extend(ibmCRDs)

    if allCustomResources:
        for apiVersion, kind in allCustomResources:
            tasks.append(
                (
                    f"ibm_{kind.lower()}",
                    collectResources,
                    namespace,
                    apiVersion,
                    kind,
                    outputDir,
                    False,  # allNamespaces
                )
            )

    # Standard Kubernetes resources
    # Create individual tasks for each resource type to avoid nested threadpools
    standardResources = [
        ("v1", "ConfigMap"),
        ("v1", "Service"),
        ("apps/v1", "Deployment"),
        ("apps/v1", "StatefulSet"),
        ("apps/v1", "DaemonSet"),
        ("apps/v1", "ReplicaSet"),
        ("batch/v1", "Job"),
        ("batch/v1", "CronJob"),
        ("v1", "PersistentVolumeClaim"),
        ("v1", "ServiceAccount"),
        ("rbac.authorization.k8s.io/v1", "Role"),
        ("rbac.authorization.k8s.io/v1", "RoleBinding"),
        ("networking.k8s.io/v1", "NetworkPolicy"),
        ("networking.k8s.io/v1", "Ingress"),
        ("operators.coreos.com/v1alpha1", "Subscription"),
        ("operators.coreos.com/v1alpha1", "InstallPlan"),
        ("operators.coreos.com/v2", "OperatorCondition"),
    ]

    for apiVersion, kind in standardResources:
        tasks.append(
            (
                f"std_{kind.lower()}",
                collectResources,
                namespace,
                apiVersion,
                kind,
                outputDir,
                False,  # allNamespaces
            )
        )

    # Secrets
    from kubernetes.client import CoreV1Api

    coreV1 = CoreV1Api(dynClient.client)
    tasks.append(
        (
            "secrets",
            collectSecrets,
            coreV1,
            namespace,
            outputDir,
            secretData,
        )
    )

    # Pods (with or without logs based on noLogs flag)
    # Generate individual tasks for each pod
    podTasks = generatePodCollectionTasks(
        dynClient=dynClient,
        namespace=namespace,
        outputDir=outputDir,
        podLogs=not noLogs,
    )
    tasks.extend(podTasks)

    return tasks
