# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Suite License Service dependency collector."""

import logging
from typing import Set, Optional, List
from kubernetes.dynamic import DynamicClient

from mas.cli.must_gather.common import collectReconcileLogsParallel
from .utils import discoverNamespacesFromCR

logger = logging.getLogger(__name__)


def discoverSLSNamespaces(dynClient: DynamicClient, masInstanceIds: Optional[List[str]] = None) -> Set[str]:
    """Discover SLS namespaces from LicenseService CRs.

    Note: The masInstanceIds parameter is kept for backward compatibility but is not used.
    Discovery is always done via LicenseService CRs, which is simpler and more reliable
    than parsing SlsCfg URLs and searching for routes.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceIds (list, optional): Unused - kept for backward compatibility. Defaults to None.

    Returns:
        set: Set of unique SLS namespace names
    """
    return discoverNamespacesFromCR(dynClient=dynClient, kind="LicenseService")


def collectSLSNamespace(dynClient: DynamicClient, namespace: str, outputDir: str, noDetail: bool = False) -> bool:
    """Collect SLS resources from a namespace.

    This function is kept for backward compatibility with app.py's collectSLS() method.
    It uses genericMustGather pattern with hardcoded podLogs=True for SLS namespaces.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str): SLS namespace to collect from
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Import here to avoid circular dependency
        from ..common import collectResources, collectPods, collectSecrets, collectIBMCustomResources

        logger.info(f"Collecting SLS resources from namespace: {namespace}")

        if noDetail:
            return True

        success = True

        # Collect reconcile logs from SLS operators
        operators = [
            (namespace, "control-plane", "controller-manager"),
            (namespace, "operator", "ibm-truststore-mgr"),
        ]

        logger.info(f"Collecting reconcile logs from {len(operators)} operators")

        def progressCallback(completed: int, total: int) -> None:
            logger.info(f"Collecting reconcile logs: {completed}/{total} operators completed")

        collectReconcileLogsParallel(dynClient, operators, outputDir, progressCallback=progressCallback)

        # Collect IBM custom resources
        try:
            if not collectIBMCustomResources(dynClient, namespace, outputDir):
                success = False
        except Exception as e:
            logger.warning(f"Error collecting IBM custom resources from {namespace}: {e}")
            success = False

        # Collect standard resources
        standardResources = [
            ("v1", "ConfigMap"),
            ("v1", "Service"),
            ("v1", "Secret"),
            ("apps/v1", "Deployment"),
            ("apps/v1", "StatefulSet"),
            ("apps/v1", "DaemonSet"),
            ("batch/v1", "Job"),
            ("batch/v1", "CronJob"),
        ]

        for apiVersion, kind in standardResources:
            try:
                collectResources(dynClient, namespace, apiVersion, kind, outputDir)
            except Exception as e:
                logger.warning(f"Error collecting {kind} from {namespace}: {e}")
                success = False

        # Collect pods with logs (SLS always collects logs)
        try:
            collectPods(
                dynClient=dynClient,
                namespace=namespace,
                outputDir=outputDir,
                podLogs=True,
            )
        except Exception as e:
            logger.warning(f"Error collecting pods from {namespace}: {e}")
            success = False

        # Collect secrets (without data)
        try:
            collectSecrets(dynClient, namespace, outputDir, secretData=False)
        except Exception as e:
            logger.warning(f"Error collecting secrets from {namespace}: {e}")
            success = False

        return success

    except Exception as e:
        logger.error(f"Error collecting SLS namespace {namespace}: {e}")
        return False


def collectSLS(dynClient: DynamicClient, outputDir: str, noDetail: bool = False, noLogs: bool = False, genericMustGather=None) -> bool:
    """Collect IBM Suite License Service resources.

    Discovers SLS namespaces from LicenseService CRs and collects SLS resources.
    Note: SLS always collects pod logs regardless of the noLogs parameter.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        outputDir (str): Base output directory for collected resources
        noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
        noLogs (bool, optional): Ignored for SLS - logs are always collected. Defaults to False.
        genericMustGather (callable, optional): Function to perform generic must-gather collection. Defaults to None.

    Returns:
        bool: True if collection succeeded, False if no SLS found or errors occurred
    """
    try:
        # Discover SLS namespaces from LicenseService CRs
        slsNamespaces = discoverNamespacesFromCR(dynClient=dynClient, kind="LicenseService")

        if not slsNamespaces:
            logger.info("No SLS namespaces found, skipping collection")
            print("⏭️  IBM Suite License Service skipped - no LicenseService resources found")
            return False

        # Collect from discovered namespaces
        # Note: We use collectSLSNamespace directly instead of genericMustGather
        # because SLS always needs pod logs collected
        success = True
        for namespace in sorted(slsNamespaces):
            if not collectSLSNamespace(dynClient=dynClient, namespace=namespace, outputDir=outputDir, noDetail=noDetail):
                success = False

        if success:
            print(f"✅ IBM Suite License Service collected from {len(slsNamespaces)} namespace(s)")
        else:
            print("❌ IBM Suite License Service collection encountered errors (check logs)")

        return success

    except Exception as e:
        logger.warning(f"Error collecting IBM Suite License Service: {e}")
        print(f"❌ IBM Suite License Service - {e}")
        return False


# Made with Bob
