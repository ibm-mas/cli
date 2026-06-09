# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Secret collection utilities for must-gather."""

import os
import yaml
import logging

from .thread_safe_client import createThreadLocalDynamicClient

logger = logging.getLogger(__name__)


def collectSecrets(
    namespace: str,
    outputDir: str,
    secretData: bool = False,
) -> tuple[bool, int]:
    """Collect Kubernetes secrets from a namespace.

    Collects secrets and generates both summary and detailed YAML output. When secretData
    is False, secret data is excluded from YAML. When True, includes full YAML
    with base64-encoded secret data.

    Args:
        namespace (str): Target namespace for collection
        outputDir (str): Base output directory for collected secrets
        secretData (bool, optional): If True, include secret data in YAML output. If False, exclude secret data. Defaults to False.

    Returns:
        tuple[bool, int]: (success status, count of secrets collected)
    """
    try:
        # Create resources/namespace/secrets directory structure
        resourcesDir = os.path.join(outputDir, "resources")
        namespaceDir = os.path.join(resourcesDir, namespace)
        secretsDir = os.path.join(namespaceDir, "secrets")
        os.makedirs(secretsDir, exist_ok=True)

        # Create thread-local DynamicClient for thread-safety
        dynClient = createThreadLocalDynamicClient()
        api = dynClient.resources.get(kind="Secret")

        # Collect secrets from namespace
        secrets = api.get(namespace=namespace)

        # Count secrets
        secretCount = len(secrets.items) if hasattr(secrets, "items") else 0

        # Generate summary file
        summaryFile = os.path.join(namespaceDir, "secrets.md")
        _writeSummary(secrets, summaryFile)

        # Write individual secret files
        for secret in secrets.items:
            secretName = secret.metadata.name
            secretFile = os.path.join(secretsDir, f"{secretName}.yaml")
            # Write YAML (with or without secret data based on secretData flag)
            _writeYaml(secret.to_dict(), secretFile, includeData=secretData)

        return (True, secretCount)

    except Exception as e:
        logger.warning(f"Error collecting secrets from namespace {namespace}: {type(e).__name__}: {e}", exc_info=True)
        return (False, 0)


def _writeSummary(secrets, outputFile: str) -> None:
    """Write secret summary as a markdown table.

    Args:
        secrets: ResourceList or ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        f.write("# Secrets (v1)\n\n")

        if hasattr(secrets, "items") and len(secrets.items) > 0:
            f.write("| NAME | NAMESPACE | TYPE |\n")
            f.write("| --- | --- | --- |\n")

            for secret in secrets.items:
                name = secret.metadata.name
                namespace = getattr(secret.metadata, "namespace", "")
                secretType = secret.to_dict().get("type", "")
                f.write(f"| [{name}](secrets/{name}.yaml) | {namespace} | {secretType} |\n")
        else:
            f.write("No resources found.\n")


def _writeYaml(secretDict: dict, outputFile: str, includeData: bool = True) -> None:
    """Write secret as YAML file.

    Args:
        secretDict (dict): Secret dictionary to write
        outputFile (str): Path to output file
        includeData (bool, optional): If False, remove secret data before writing. Defaults to True.
    """
    # Remove secret data if not requested
    if not includeData and "data" in secretDict:
        secretDict = secretDict.copy()
        secretDict.pop("data", None)

    with open(outputFile, "w") as f:
        yaml.dump(secretDict, f, default_flow_style=False, sort_keys=False)
