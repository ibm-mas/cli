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
shell renders when the user runs ``mas-cli update`` without arguments.
"""

from typing import Any

from mas.cli.tui.models import WorkflowDefinition, WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens import ConfirmUpgradesScreen, LaunchScreen, ReviewScreen
from mas.cli.tui.shell import AutoRunScreen
from mas.cli.common.workflow import connectClusterStep


def _nonInteractiveCommand(appInstance: Any) -> str:
    """Render the equivalent non-interactive ``mas update`` command.

    Delegates to ``UpdateApp.buildCommand()`` (the ``updateArgBuilderMixin``
    from PR #2713, round-trip tested in
    ``tests/unit/update/test_update_arg_builder.py``) so the TUI shows exactly
    what the classic interactive wizard would print.

    Args:
        appInstance (Any): A ``UpdateApp`` instance with populated params.

    Returns:
        str: The rendered command, secrets masked as environment variables.
    """
    return appInstance.buildCommand()


def _scriptFilename(appInstance: Any) -> str:
    """Default filename for the review screen's Save Script button.

    Mirrors the filename offered by the classic interactive flow
    (``app.py`` offerCommandScript call).

    Args:
        appInstance (Any): A ``UpdateApp`` instance.

    Returns:
        str: e.g. ``mas-update-v9-261102-amd64.sh``.
    """
    return f"mas-update-{appInstance.getParam('mas_catalog_version')}.sh"


def buildUpdateReview(appInstance: Any) -> str:
    """Build the Markdown review text for the update command.

    Mirrors the structure of the interactive ``printH1``/``printH2``/
    ``printSummary`` calls in ``UpdateApp.update()`` so the TUI review screen
    looks like its CLI counterpart.

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

    if appInstance.params.get("odh_to_rhoai_migration", "") == "":
        aiServiceDataScienceMigration = "No action required"
    elif getattr(appInstance, "rhoaiV2Detected", False):
        aiServiceDataScienceMigration = "Upgrade from RHOAI v2 to RHOAI v3"
    else:
        aiServiceDataScienceMigration = "Migrate from ODH to RHOAI"

    lines = [
        "## IBM Maximo Operator Catalog",
        "",
        _row("Installed Catalog", getattr(appInstance, "installedCatalogId", None) or "—"),
        _row("Target Catalog Version", appInstance.params.get("mas_catalog_version", "—")),
        _row("Pipeline Service Account", appInstance.params.get("service_account_name", "—")),
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
        _row("AI Service Data Science Platform", aiServiceDataScienceMigration),
        "",
    ]
    return "\n".join(lines)


def buildUpdateWorkflow(appInstance: Any) -> WorkflowDefinition:
    """Build the workflow definition for the update command.

    Constructs the ordered list of steps shown in the TUI when the user
    invokes ``mas-cli update`` without arguments.

    The six steps are:

    1. **connect-cluster** — Collect OCP credentials and connect, then run
       the post-connection cluster review (``_postConnectChecks``) which
       detects the installed catalog and verifies MAS/AI Service instances
       exist.
    2. **choose-catalog** — Select the target Maximo Operator Catalog version,
       with the currently installed catalog shown as context.  Validates OCP
       compatibility, catalog ordering, and the routing-mode pre-flight check
       (``validateCatalogSelection``).
    3. **dependency-checks** — Auto-running checklist that detects installed
       dependencies and populates params.
    4. **confirm-upgrades** — Conditional step shown only when a MongoDB or
       Db2 major-version upgrade confirmation (or the Db2 v11 to v12 license
       file) is still required.
    5. **review** — Review all settings before proceeding, including the
       equivalent non-interactive ``mas update`` command (with copy /
       save-as-script).  The Confirm button advances to the launch step.
    6. **launch** — Submits the Tekton pipeline, then re-displays the
       non-interactive command for reference.  The Done button exits the app.

    Args:
        appInstance (Any): A ``UpdateApp`` instance whose methods are used
            as step actions and validators.

    Returns:
        WorkflowDefinition: Ordered list of WorkflowStep objects.
    """
    # Use the same curated list as the interactive chooseCatalog() prompt —
    # NOT the full listCatalogTags() which contains all historical releases.
    catalogOptions = appInstance.getCatalogOptions()

    # _postConnectChecks() must run immediately after connecting — it sets
    # self.installedCatalogId which validateCatalogSelection() reads on the
    # next step.
    connectStep = connectClusterStep(appInstance, post_connect=appInstance._postConnectChecks)

    catalogStep = WorkflowStep(
        id="choose-catalog",
        heading="Choose Target Catalog",
        heading_level="h1",
        description=[
            "Select the IBM Maximo Operator Catalog version to update to.",
            "Enter the name of an existing service account in mas-pipelines to run the update pipeline as.",
            "The default `pipeline` service account is bound to cluster-admin, any other service account must already have the permissions the update needs.",
        ],
        # Read-only context panel: the catalog detected by the connect step's
        # post-connect checks.  The panel composes lazily (after connect), so
        # installedCatalogId is already populated when the values resolve.
        context=[
            WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId"),
        ],
        fields=[
            WorkflowField(
                id="mas_catalog_version",
                label="Catalog Version",
                type="select",
                options=catalogOptions,
                required=True,
            ),
            WorkflowField(id="service_account_name", label="Pipeline Service Account", type="string", default="pipeline"),
        ],
        validator=appInstance.validateCatalogSelection,
    )
    dependenciesStep = WorkflowStep(
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
    )

    # Only shown when the dependency checks detected a major-version upgrade
    # (or Db2 v11 to v12 license file) that still requires an explicit
    # confirmation.  The condition closes over the app instance so it reads
    # the detector state rather than the params dict; it is re-evaluated by
    # the shell after the dependency-checks step completes.
    confirmUpgradesStep = WorkflowStep(
        id="confirm-upgrades",
        heading="Confirm Upgrade Requirements",
        heading_level="h1",
        description=[
            "The dependency checks detected updates that require your explicit confirmation before the update can proceed.",
        ],
        screen_class=ConfirmUpgradesScreen,
        condition=lambda p: appInstance.upgradeConfirmationsPending(),
    )

    reviewStep = WorkflowStep(
        id="review",
        heading="Review Settings",
        heading_level="h1",
        description=["Please carefully review your choices below."],
        screen_class=ReviewScreen,
        screen_kwargs={
            "review_builder": buildUpdateReview,
            "command_builder": _nonInteractiveCommand,
            "script_filename_builder": _scriptFilename,
        },
        summary=[
            WorkflowSummaryItem(label="Installed Catalog", attr="installedCatalogId"),
            WorkflowSummaryItem(label="Target Catalog Version", param="mas_catalog_version"),
            WorkflowSummaryItem(label="Pipeline Service Account", param="service_account_name"),
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
        screen_kwargs={"command_builder": _nonInteractiveCommand},
    )

    return [
        connectStep,
        catalogStep,
        dependenciesStep,
        confirmUpgradesStep,
        reviewStep,
        launchStep,
    ]
