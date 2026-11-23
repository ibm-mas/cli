# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Sanitization utilities for must-gather secret output."""

import copy

LAST_APPLIED_ANNOTATION = "kubectl.kubernetes.io/last-applied-configuration"


def stripLastAppliedConfiguration(resourceDict: dict) -> dict:
    """Return a copy of a resource without the last-applied-configuration annotation.

    The annotation kubectl.kubernetes.io/last-applied-configuration holds a full copy of the
    manifest from the last apply, which for Secrets includes data/stringData in clear text.
    The input is not modified.

    Args:
        resourceDict (dict): A single resource (e.g. a Secret)

    Returns:
        dict: Sanitized deep copy of the resource
    """
    cleaned = copy.deepcopy(resourceDict)
    metadata = cleaned.get("metadata")
    if isinstance(metadata, dict):
        annotations = metadata.get("annotations")
        if isinstance(annotations, dict):
            annotations.pop(LAST_APPLIED_ANNOTATION, None)
            if not annotations:
                metadata.pop("annotations", None)
    return cleaned
