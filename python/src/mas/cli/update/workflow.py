# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Workflow definition for the MAS update command.

Builds the ordered list of WorkflowStep objects that the Textual TUI
shell renders when the user runs ``mas-cli update`` without ``--catalog``.
"""

from typing import Any

from mas.cli.tui.models import WorkflowDefinition, WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens import LaunchScreen, ReviewScreen
from mas.cli.tui.shell import AutoRunScreen
from mas.cli.common.workflow import connectClusterStep


def buildUpdateReview(appInstance: Any) -> str:
    """Build the Markdown review text for the update command.

    Mirrors the structure of the original interactive ``printH1``/``printH2``/
    ``printSummary`` calls in ``UpdateApp.update()`` so the TUI review screen
    looks like its non-interactive counterpart.

    Three sections:
    - **IBM Maximo Operator Catalog** — installed vs target catalog IDs.
    - **Supported Dependency Updates** — Db2, MongoDB, Kafka, CP4D with
      namespace detail when detected, "No action required" otherwise.
    - **Required Migrations** — Grafana v4 and ODH/RHOAI migration status.

    Args:
        appInstance (Any): A ``UpdateApp`` instance with populated params and
            ``installedCatalogId`` attribute.

    Returns:
        str: Markdown document string ready for the Textual Markdown widget.
    """

    def _row(label: str, value: str) -> str:
        return f"**{label}:** {value}  "

    def _ns(param: str, prefix: str) -> str:
        ns = appInstance.params.get(param, "")
        return f"{prefix} in `{ns}`" if ns else "No action required"

    lines = [
        "## IBM Maximo Operator Catalog",
        "",
        _row("Installed Catalog", getattr(appInstance, "installedCatalogId", None) or "—"),
        _row("Target Catalog Version", appInstance.params.get("mas_catalog_version", "—")),
        "",
        "## Supported Dependency Updates",
        "",
        _row("IBM Db2", _ns("db2_namespace", "All Db2uCluster and Db2uInstance instances")),
        _row("MongoDB Community", _ns("mongodb_namespace", "All MongoDbCommunity instances")),
        _row("Apache Kafka", _ns("kafka_namespace", "All Kafka instances")),
        _row(
            "IBM Cloud Pak for Data",
            "Platform and services in `ibm-cpd`" if appInstance.params.get("cp4d_update", "") else "No action required",
        ),
        "",
        "## Required Migrations",
        "",
        _row(
            "Grafana v4 Operator",
            "Migrate to Grafana v5 Operator" if appInstance.params.get("grafana_v5_upgrade", "") else "No action required",
        ),
        _row(
            "AI Service Data Science Platform",
            "Migrate from ODH to RHOAI" if appInstance.params.get("odh_to_rhoai_migration", "") else "No action required",
        ),
        "",
    ]
    return "\n".join(lines)


def buildUpdateWorkflow(appInstance: Any) -> WorkflowDefinition:
    """Build the workflow definition for the update command.

    Constructs the ordered list of steps shown in the TUI when the user
    invokes ``mas-cli update`` without ``--catalog``.

    The five steps are:

    1. **connect-cluster** — Collect OCP credentials and connect, then review
       the currently installed catalog (sets ``installedCatalogId``).
    2. **choose-catalog** — Select the target Maximo Operator Catalog version.
       Validates OCP compatibility and ordering against installed catalog.
    3. **dependency-checks** — Auto-running checklist that detects installed
       dependencies and populates params.
    4. **review** — Review all settings before proceeding.  The Confirm button
       advances to the launch step.
    5. **launch** — Submits the Tekton pipeline.  The Done button exits the app.

    All ``condition`` lambdas accept a single ``dict`` argument.

    Args:
        appInstance (Any): A ``UpdateApp`` instance whose methods are used
            as step actions.

    Returns:
        WorkflowDefinition: Ordered list of WorkflowStep objects.
    """
    # Use the same curated list as the interactive chooseCatalog() prompt —
    # NOT the full listCatalogTags() which contains all historical releases.
    catalogOptions = appInstance.getCatalogOptions()

    # reviewCurrentCatalog() must run immediately after connecting — it sets
    # self.installedCatalogId which validateCatalog() reads on the next step.
    connectStep = connectClusterStep(appInstance, post_connect=appInstance.reviewCurrentCatalog)

    reviewStep = WorkflowStep(
        id="review",
        heading="Review Settings",
        heading_level="h1",
        description=["Please carefully review your choices below."],
        screen_class=ReviewScreen,
        screen_kwargs={"review_builder": buildUpdateReview},
        summary=[
            WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId"),
            WorkflowSummaryItem(label="Target Catalog Version", param="mas_catalog_version"),
            WorkflowSummaryItem(label="IBM Db2", param="db2_namespace"),
            WorkflowSummaryItem(label="MongoDB Community", param="mongodb_namespace"),
            WorkflowSummaryItem(label="Apache Kafka", param="kafka_namespace"),
            WorkflowSummaryItem(label="IBM Cloud Pak for Data", param="cp4d_update"),
            WorkflowSummaryItem(label="Grafana v4 Operator", param="grafana_v5_upgrade"),
            WorkflowSummaryItem(label="Open Data Hub (ODH)", param="odh_to_rhoai_migration"),
        ],
    )

    launchStep = WorkflowStep(
        id="launch",
        heading="Launch Update",
        heading_level="h1",
        description=["Submitting the Tekton pipeline for MAS update."],
        screen_class=LaunchScreen,
    )

    return [
        connectStep,
        WorkflowStep(
            id="choose-catalog",
            heading="Choose Target Catalog",
            heading_level="h1",
            description=[
                "Select the IBM Maximo Operator Catalog version to update to.",
            ],
            fields=[
                WorkflowField(
                    id="mas_catalog_version",
                    label="Catalog Version",
                    type="select",
                    options=catalogOptions,
                    required=True,
                ),
            ],
            validator=appInstance.checkCatalog,
        ),
        WorkflowStep(
            id="dependency-checks",
            heading="Dependency Update Checks",
            heading_level="h1",
            description=[
                "Detecting installed dependencies that may require updates.",
            ],
            screen_class=AutoRunScreen,
            summary=[
                WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId"),
                WorkflowSummaryItem(label="Target Catalog Version", param="mas_catalog_version"),
                WorkflowSummaryItem(label="IBM Db2", param="db2_namespace"),
                WorkflowSummaryItem(label="MongoDB Community", param="mongodb_namespace"),
                WorkflowSummaryItem(label="Apache Kafka", param="kafka_namespace"),
                WorkflowSummaryItem(label="IBM Cloud Pak for Data", param="cp4d_update"),
                WorkflowSummaryItem(label="Grafana v4 Operator", param="grafana_v5_upgrade"),
                WorkflowSummaryItem(label="Open Data Hub (ODH)", param="odh_to_rhoai_migration"),
            ],
        ),
        reviewStep,
        launchStep,
    ]
