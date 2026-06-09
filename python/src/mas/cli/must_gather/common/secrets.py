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
import json
import yaml
import logging

from kubernetes.client import CoreV1Api

logger = logging.getLogger(__name__)


def collectSecrets(
    coreV1: CoreV1Api,
    namespace: str,
    outputDir: str,
    secretData: bool = False,
) -> tuple[bool, int]:
    """Collect Kubernetes secrets from a namespace.

    Collects secrets and generates both summary and detailed YAML output. When secretData
    is False, secret data is excluded from YAML. When True, includes full YAML
    with base64-encoded secret data.

    Args:
        coreV1 (CoreV1Api): Kubernetes CoreV1Api client instance
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

        # Collect secrets from namespace using CoreV1Api with raw JSON response
        rawResponse = coreV1.list_namespaced_secret(namespace=namespace, _preload_content=False)
        rawJson = rawResponse.data
        secretListDict = json.loads(rawJson)

        # Extract items from the response
        secretItems = secretListDict.get("items", [])
        secretCount = len(secretItems)

        # Generate summary file
        summaryFile = os.path.join(namespaceDir, "secrets.md")
        _writeSummary(secretListDict, summaryFile)

        # Write individual secret files
        for secretDict in secretItems:
            secretName = secretDict.get("metadata", {}).get("name", "unknown")
            secretFile = os.path.join(secretsDir, f"{secretName}.yaml")
            # Add apiVersion and kind (omitted from list items by Kubernetes API)
            if "apiVersion" not in secretDict:
                secretDict["apiVersion"] = "v1"
            if "kind" not in secretDict:
                secretDict["kind"] = "Secret"
            # Write YAML (with or without secret data based on secretData flag)
            _writeYaml(secretDict, secretFile, includeData=secretData)

        return (True, secretCount)

    except Exception as e:
        logger.warning(f"Error collecting secrets from namespace {namespace}: {type(e).__name__}: {e}", exc_info=True)
        return (False, 0)


def _writeSummary(secretListDict: dict, outputFile: str) -> None:
    """Write secret summary as a markdown table.

    Args:
        secretListDict (dict): Secret list dictionary from Kubernetes API (raw JSON)
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        f.write("# Secrets (v1)\n\n")

        items = secretListDict.get("items", [])
        if len(items) > 0:
            f.write("| NAME | NAMESPACE | TYPE |\n")
            f.write("| --- | --- | --- |\n")

            for secret in items:
                metadata = secret.get("metadata", {})
                name = metadata.get("name", "")
                namespace = metadata.get("namespace", "")
                secretType = secret.get("type", "")
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
