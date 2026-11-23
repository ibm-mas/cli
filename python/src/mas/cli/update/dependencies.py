# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Dependency-check registry for the update command.

Defines the pure-data types that drive the pre-update dependency checks:

- :class:`DetectResult` — the value returned by every detector method on
  :class:`~mas.cli.update.app.UpdateApp`.  ``ok`` is ``True`` for a success
  or informational outcome and ``False`` for a blocking failure; ``message``
  is the human-readable status shown in the Halo spinner (CLI) and the TUI
  progress list.
- :class:`CheckItem` — one entry in the ordered ``_DEPENDENCY_CHECKS``
  registry: a display label plus the name of the ``UpdateApp`` detector
  method to call.
- ``_DEPENDENCY_CHECKS`` — the ordered registry itself, exposed as a class
  attribute on ``UpdateApp`` and driven by
  ``UpdateApp.runDependencyChecks()`` on both the CLI (Halo spinner) and
  TUI (progress callback) execution paths.
- :func:`dependencyCheckLabels` — the display labels (including the trailing
  pre-install RBAC evaluation stage) used by the TUI AutoRunScreen.

This module is deliberately free of cluster-API imports so the TUI screens
can render the check list without a connection.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DetectResult:
    """Result returned by every dependency detector method.

    Attributes:
        ok (bool): True for a success or informational outcome (no blocking
            issue), False when the result requires the update to be aborted.
        message (str): Short, specific human-readable status string shown
            verbatim in the Halo spinner line and the TUI progress log.
    """

    ok: bool
    message: str


@dataclass
class CheckItem:
    """Descriptor for a single pre-update dependency check.

    Attributes:
        label (str): Human-readable check name shown in progress output.
        method (str): Name of the ``UpdateApp`` detector method to call.
            The method takes no arguments and returns a ``DetectResult``.
        param (str): Unused — kept for backwards-compatible registry entries.
        fatal_if_present (bool): Retained for registry compatibility.  Every
            ``DetectResult(ok=False, ...)`` blocks the update on both
            execution paths regardless of this flag: the CLI wraps the
            failure in ``fatalError``, the TUI raises ``RuntimeError`` so
            the failure is shown inline.
        present_message (str): Unused legacy field.  Defaults to empty string.
        absent_message (str): Unused legacy field.  Defaults to "No action required".
    """

    label: str
    method: str
    param: str = ""
    fatal_if_present: bool = False
    present_message: str = ""
    absent_message: str = "No action required"


_DEPENDENCY_CHECKS: List[CheckItem] = [
    CheckItem("IBM Watson Discovery", "isWatsonDiscoveryInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
    CheckItem("IBM Watson Openscale", "isWatsonOpenscaleInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
    CheckItem("IBM Certificate-Manager", "isIBMCertManagerInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
    CheckItem("Grafana Operator v4", "detectGrafana4", "grafana_v5_upgrade", present_message="Migrate to v5"),
    CheckItem("Open Data Hub (ODH)", "detectODH", "odh_to_rhoai_migration", present_message="Migrate to RHOAI"),
    CheckItem("Red Hat OpenShift AI (RHOAI) v2", "detectRHOAIv2", "odh_to_rhoai_migration", present_message="Upgrade to RHOAI v3"),
    CheckItem("AI Service MinIO to Ceph", "detectMinioToCeph", "aiservice_s3_migration_instance_ids", present_message="Migration scheduled"),
    CheckItem("MongoDB Community", "detectMongoDb", "mongodb_namespace", present_message="Found"),
    CheckItem("IBM Db2", "detectDb2u", "db2_namespace", present_message="Found"),
    CheckItem("Apache Kafka", "detectKafka", "kafka_namespace", present_message="Found"),
    CheckItem("IBM Cloud Pak for Data", "detectCP4D", "cp4d_update", present_message="Platform and services in ibm-cpd"),
]
"""Ordered registry of pre-update dependency checks.

Any check returning ``DetectResult(ok=False, ...)`` blocks the update on both
execution paths (the CLI wraps the failure in ``fatalError``, the TUI raises
``RuntimeError`` so the failure is shown inline).
"""


def dependencyCheckLabels() -> List[str]:
    """Return the display labels for all dependency-check stages.

    Combines the ``_DEPENDENCY_CHECKS`` registry labels with the final
    pre-install RBAC evaluation stage that ``runDependencyChecks()`` always
    performs last.

    Returns:
        List[str]: Ordered list of human-readable check labels.
    """
    return [item.label for item in _DEPENDENCY_CHECKS] + ["Pre-install RBAC evaluation"]
