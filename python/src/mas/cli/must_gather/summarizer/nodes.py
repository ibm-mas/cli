# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Nodes summarizer for must-gather.

Post-processes node markdown files to add links to pod YAML files
that exist in the collection.
"""

import os
import re
import glob
import logging

logger = logging.getLogger(__name__)


def summarize(outputDir: str) -> None:
    """Add pod links to node markdown files.

    Processes all node.md files in resources/_cluster/nodes/ and adds
    markdown links to pod YAML files that exist in the collection.

    Args:
        outputDir (str): Path to must-gather output directory
    """
    nodesDir = os.path.join(outputDir, "resources", "_cluster", "nodes")

    if not os.path.exists(nodesDir):
        logger.debug("No nodes directory found, skipping node summarization")
        return

    # Find all node markdown files
    nodeMdFiles = glob.glob(os.path.join(nodesDir, "*.md"))

    if not nodeMdFiles:
        logger.debug("No node markdown files found")
        return

    logger.info(f"Processing {len(nodeMdFiles)} node markdown file(s)")

    for mdFile in nodeMdFiles:
        try:
            _processNodeMarkdown(mdFile, outputDir)
        except Exception as e:
            logger.warning(f"Failed to process {os.path.basename(mdFile)}: {e}")


def _processNodeMarkdown(mdFile: str, outputDir: str) -> None:
    """Process a single node markdown file to add pod links.

    Args:
        mdFile (str): Path to node markdown file
        outputDir (str): Path to must-gather output directory
    """
    with open(mdFile, "r") as f:
        content = f.read()

    # Find the Non-terminated Pods table
    # Look for the table header line
    tableHeaderPattern = r"\| Namespace \| Name \| CPU Requests \| CPU Limits \| Memory Requests \| Memory Limits \| Age \|"
    match = re.search(tableHeaderPattern, content)

    if not match:
        logger.debug(f"No pod table found in {os.path.basename(mdFile)}")
        return

    # Process each table row
    # Pattern matches: | namespace | podname | ... |
    # Pod names can contain letters, numbers, hyphens, and be quite long
    rowPattern = r"\| ([a-z0-9-]+) \| ([a-z0-9-]+) \| "

    def replacePodName(match):
        namespace = match.group(1)
        podName = match.group(2)

        # Pod YAML files are stored in subdirectories: pods/{pod-base-name}/{pod-name}.yaml
        # Use glob to find the pod YAML file
        podGlobPattern = os.path.join(outputDir, "resources", namespace, "pods", "*", f"{podName}.yaml")
        matchingFiles = glob.glob(podGlobPattern)

        if matchingFiles:
            # Get the relative path from the pod YAML to construct the link
            podYamlPath = matchingFiles[0]
            # Extract the subdirectory name (pod base name)
            podSubdir = os.path.basename(os.path.dirname(podYamlPath))
            # Create relative link from nodes directory to pod YAML
            relativeLink = f"../../{namespace}/pods/{podSubdir}/{podName}.yaml"
            # Replace pod name with markdown link
            return f"| {namespace} | [{podName}]({relativeLink}) | "
        else:
            # Keep original if pod YAML doesn't exist
            return match.group(0)

    # Replace pod names with links where YAML files exist
    updatedContent = re.sub(rowPattern, replacePodName, content)

    # Only write if content changed
    if updatedContent != content:
        with open(mdFile, "w") as f:
            f.write(updatedContent)
        logger.debug(f"Updated pod links in {os.path.basename(mdFile)}")


# Made with Bob
