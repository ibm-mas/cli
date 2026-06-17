# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Node resource collection with describe output."""

import logging
from mas.cli.must_gather.common.resources import collectResources

logger = logging.getLogger(__name__)


def collectNodes(outputDir: str) -> bool:
    """Collect node resources with describe output.

    Collects node information including both summary and detailed describe output
    for each node. The describe output provides comprehensive node information
    similar to 'kubectl describe node' command.

    Args:
        outputDir (str): Base output directory for collected resources

    Returns:
        bool: True if collection succeeded, False if errors occurred
    """
    return collectResources(
        namespace=None,
        apiVersion="v1",
        kind="Node",
        outputDir=outputDir,
        allNamespaces=False,
    )
