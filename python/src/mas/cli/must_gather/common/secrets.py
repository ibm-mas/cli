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
from typing import Optional
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def collectSecrets(
    dynClient: DynamicClient,
    namespace: Optional[str],
    outputDir: str,
    secretData: bool = False,
    allNamespaces: bool = False,
) -> bool:
    """Collect Kubernetes secrets from a namespace.

    Collects secrets and generates both summary and detailed output. When secretData
    is False, uses describe format (metadata only). When True, includes full YAML
    with base64-encoded secret data.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        namespace (str, optional): Target namespace for collection. Use None for cluster-scoped. Defaults to None.
        outputDir (str): Base output directory for collected secrets
        secretData (bool, optional): If True, include secret data in YAML output. If False, use describe format. Defaults to False.
        allNamespaces (bool, optional): If True, collect secrets across all namespaces. Defaults to False.

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    try:
        # Determine namespace directory
        if namespace:
            namespaceDir = os.path.join(outputDir, namespace)
        else:
            namespaceDir = os.path.join(outputDir, "_cluster")

        os.makedirs(namespaceDir, exist_ok=True)

        # Create secrets directory
        secretsDir = os.path.join(namespaceDir, "secrets")
        os.makedirs(secretsDir, exist_ok=True)

        # Get API resource
        api = dynClient.resources.get(kind="Secret")

        # Collect secrets
        if allNamespaces:
            secrets = api.get()
        elif namespace:
            secrets = api.get(namespace=namespace)
        else:
            secrets = api.get()

        # Generate summary file
        summaryFile = os.path.join(namespaceDir, "secrets.txt")
        _writeSummary(secrets, summaryFile)

        # Generate detailed reports
        if allNamespaces:
            # For all-namespaces, write single file
            allNamespacesFile = os.path.join(secretsDir, "all-namespaces.yaml")
            if secretData:
                _writeYaml(secrets.to_dict(), allNamespacesFile)
            else:
                _writeDescribeMultiple(secrets, allNamespacesFile)
        else:
            # Write individual secret files
            for secret in secrets.items:
                secretName = secret.metadata.name

                secretFile = os.path.join(secretsDir, f"{secretName}.yaml")
                if secretData:
                    # Write full YAML with secret data
                    _writeYaml(secret.to_dict(), secretFile)
                else:
                    # Write describe format (no secret data)
                    _writeDescribe(secret, secretFile)

        return True

    except Exception as e:
        logger.warning(f"Error collecting secrets: {e}")
        return False


def _writeSummary(secrets, outputFile: str) -> None:
    """Write secret summary in wide format.

    Args:
        secrets: ResourceList or ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        if hasattr(secrets, "items") and len(secrets.items) > 0:
            # Write header
            f.write(f"{'NAME':<50} {'NAMESPACE':<30} {'TYPE':<30}\n")

            # Write each secret
            for secret in secrets.items:
                name = secret.metadata.name
                namespace = getattr(secret.metadata, "namespace", "")
                secretType = secret.to_dict().get("type", "")
                f.write(f"{name:<50} {namespace:<30} {secretType:<30}\n")
        else:
            f.write("No resources found.\n")


def _writeYaml(secretDict: dict, outputFile: str) -> None:
    """Write secret as YAML file with data.

    Args:
        secretDict (dict): Secret dictionary to write
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        yaml.dump(secretDict, f, default_flow_style=False, sort_keys=False)


def _writeDescribe(secret, outputFile: str) -> None:
    """Write secret describe output without data for a single secret.

    Generates output similar to 'kubectl describe secret' command, which shows
    metadata but not the actual secret data values.

    Args:
        secret: ResourceInstance from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        _writeSecretDescribe(secret, f)


def _writeDescribeMultiple(secrets, outputFile: str) -> None:
    """Write secret describe output for multiple secrets.

    Args:
        secrets: ResourceList from Kubernetes API
        outputFile (str): Path to output file
    """
    with open(outputFile, "w") as f:
        for secret in secrets.items:
            _writeSecretDescribe(secret, f)
            f.write("\n---\n\n")


def _writeSecretDescribe(secret, fileHandle) -> None:
    """Write describe output for a single secret.

    Args:
        secret: ResourceInstance from Kubernetes API
        fileHandle: File handle to write to
    """
    secretDict = secret.to_dict()

    # Write metadata section
    fileHandle.write("Name:         {}\n".format(secretDict.get("metadata", {}).get("name", "")))
    fileHandle.write("Namespace:    {}\n".format(secretDict.get("metadata", {}).get("namespace", "")))
    fileHandle.write("Labels:       {}\n".format(secretDict.get("metadata", {}).get("labels", {})))
    fileHandle.write("Annotations:  {}\n".format(secretDict.get("metadata", {}).get("annotations", {})))
    fileHandle.write("\n")

    # Write type
    fileHandle.write("Type:  {}\n".format(secretDict.get("type", "Opaque")))
    fileHandle.write("\n")

    # Write data keys (but not values)
    if "data" in secretDict:
        fileHandle.write("Data\n")
        fileHandle.write("====\n")
        for key in secretDict["data"].keys():
            fileHandle.write(f"{key}:  <redacted>\n")


# Made with Bob
