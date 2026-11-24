# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Workflow definition for the MAS install command.

Builds the ordered list of WorkflowStep objects that the Textual TUI
shell renders when the user runs ``mas-cli install`` without arguments.
"""

from typing import Any

from mas.cli.common.workflow import connectClusterStep
from mas.cli.tui.models import WorkflowDefinition, WorkflowField, WorkflowStep, WorkflowSummaryItem
from mas.cli.tui.screens import LaunchScreen, LicenseAcceptanceScreen, ReviewScreen


def _nonInteractiveCommand(appInstance: Any) -> str:
    """Render the equivalent non-interactive ``mas install`` command.

    Delegates to ``InstallApp.buildCommand()`` (the ``installArgBuilderMixin``)
    so the TUI shows exactly what the classic interactive wizard would print.

    Args:
        appInstance (Any): An ``InstallApp`` instance with populated params.

    Returns:
        str: The rendered command, secrets masked as environment variables.
    """
    return appInstance.buildCommand()


def _scriptFilename(appInstance: Any) -> str:
    """Default filename for the review screen's Save Script button.

    Mirrors the filename offered by the classic interactive flow
    (``mas-install-<instance-id>.sh``).

    Args:
        appInstance (Any): An ``InstallApp`` instance.

    Returns:
        str: e.g. ``mas-install-inst1.sh``.
    """
    instanceId = appInstance.getParam("mas_instance_id") or "instance"
    return f"mas-install-{instanceId}.sh"


def buildInstallReview(appInstance: Any) -> str:
    """Build the Markdown review text for the install command.

    Mirrors the structure of the installation summary so the TUI review
    screen looks clean, clear, and comprehensive.

    Args:
        appInstance (Any): An ``InstallApp`` instance with populated params.

    Returns:
        str: Markdown document string ready for the Textual Markdown widget.
    """

    def _row(label: str, value: Any) -> str:
        rendered = "—" if value in (None, "") else str(value)
        return f"**{label}:** {rendered}  "

    lines = [
        "## IBM Maximo Operator Catalog",
        "",
        _row("Catalog Version", appInstance.params.get("mas_catalog_version")),
        _row("MAS Channel", appInstance.params.get("mas_channel")),
        "",
        "## MAS Instance Configuration",
        "",
        _row("Instance ID", appInstance.params.get("mas_instance_id")),
        _row("Workspace ID", appInstance.params.get("mas_workspace_id")),
        _row("Workspace Name", appInstance.params.get("mas_workspace_name")),
        _row("Operational Mode", appInstance.params.get("environment_type", "production")),
    ]

    admin_mode = getattr(appInstance, "mas_admin_mode", None) or appInstance.params.get("mas_admin_mode")
    if admin_mode:
        lines.append(_row("Admin Mode", admin_mode))

    lines += [
        "",
        "## Storage Configuration",
        "",
        _row("ReadWriteOnce (RWO) Storage Class", appInstance.params.get("storage_class_rwo")),
        _row("ReadWriteMany (RWX) Storage Class", appInstance.params.get("storage_class_rwx")),
        _row("Pipeline Storage Class", getattr(appInstance, "pipelineStorageClass", None) or appInstance.params.get("storage_class_rwx")),
        _row("Pipeline Storage Access Mode", getattr(appInstance, "pipelineStorageAccessMode", None) or "ReadWriteMany"),
        "",
        "## Licensing (SLS & DRO)",
        "",
        _row("SLS Action", appInstance.params.get("sls_action", "install")),
        _row("SLS Namespace", appInstance.params.get("sls_namespace", "ibm-sls")),
        _row("DRO Contact Email", appInstance.params.get("dro_contact_email")),
        "",
        "## Selected Applications",
        "",
    ]

    selected_apps = []
    if getattr(appInstance, "installManage", False) is True or bool(appInstance.params.get("mas_app_channel_manage")):
        selected_apps.append(f"Manage (`{appInstance.params.get('mas_app_channel_manage', 'default')}`)")
    if getattr(appInstance, "installIoT", False) is True or bool(appInstance.params.get("mas_app_channel_iot")):
        selected_apps.append(f"IoT (`{appInstance.params.get('mas_app_channel_iot', 'default')}`)")
    if getattr(appInstance, "installMonitor", False) is True or bool(appInstance.params.get("mas_app_channel_monitor")):
        selected_apps.append(f"Monitor (`{appInstance.params.get('mas_app_channel_monitor', 'default')}`)")
    if getattr(appInstance, "installAssist", False) is True or bool(appInstance.params.get("mas_app_channel_assist")):
        selected_apps.append(f"Assist (`{appInstance.params.get('mas_app_channel_assist', 'default')}`)")
    if getattr(appInstance, "installOptimizer", False) is True or bool(appInstance.params.get("mas_app_channel_optimizer")):
        selected_apps.append(f"Optimizer (`{appInstance.params.get('mas_app_channel_optimizer', 'default')}`)")
    if getattr(appInstance, "installInspection", False) is True or bool(appInstance.params.get("mas_app_channel_visualinspection")):
        selected_apps.append(f"Visual Inspection (`{appInstance.params.get('mas_app_channel_visualinspection', 'default')}`)")
    if getattr(appInstance, "installFacilities", False) is True or bool(appInstance.params.get("mas_app_channel_facilities")):
        selected_apps.append(f"Facilities (`{appInstance.params.get('mas_app_channel_facilities', 'default')}`)")
    if getattr(appInstance, "installAIService", False) is True or bool(appInstance.params.get("aiservice_channel")):
        selected_apps.append(f"AI Service (`{appInstance.params.get('aiservice_channel', 'default')}`)")

    if selected_apps:
        for app in selected_apps:
            lines.append(f"- {app}")
    else:
        lines.append("Core Platform Only")

    lines.append("")
    return "\n".join(lines)


def buildInstallWorkflow(appInstance: Any) -> WorkflowDefinition:
    """Build the workflow definition for the install command.

    Constructs the ordered list of steps shown in the TUI when the user
    invokes ``mas-cli install`` without arguments.

    The ten steps are:
    1. **connect-cluster** — Connect to OpenShift and run post-connect checks
       (detect architecture, default storage classes, SNO).
    2. **choose-catalog** — Select catalog version and MAS release channel.
    3. **license-acceptance** — Accept license terms for the chosen release channel.
    4. **icr-credentials** — Configure IBM container registry entitlement key.
    5. **storage-classes** — Configure RWO and RWX storage classes.
    6. **licensing-sls** — Configure AppPoint licensing and DRO contact details.
    7. **mas-instance** — Configure instance ID, workspace ID/name, admin mode.
    8. **applications** — Select applications to install.
    9. **review** — Review all configurations with non-interactive command generator.
    10. **launch** — Execute installation pipeline and monitor stages.

    Args:
        appInstance (Any): An ``InstallApp`` instance whose methods are used
            as step actions and validators.

    Returns:
        WorkflowDefinition: Ordered list of WorkflowStep objects.
    """
    catalogOptions = appInstance.getCatalogOptions()

    connectStep = connectClusterStep(appInstance, post_connect=appInstance.postConnectChecks)

    catalogStep = WorkflowStep(
        id="choose-catalog",
        heading="Choose Target Catalog",
        heading_level="h1",
        description=[
            "Select the IBM Maximo Operator Catalog version and MAS release channel to install.",
        ],
        fields=[
            WorkflowField(
                id="mas_catalog_version",
                label="Catalog Version",
                type="select",
                options=catalogOptions,
                required=True,
            ),
            WorkflowField(
                id="mas_channel",
                label="MAS Release Channel",
                type="select",
                options=lambda: list(getattr(appInstance, "catalogReleases", {}).values()) or ["9.2.x", "9.1.x"],
                required=True,
            ),
        ],
        validator=appInstance.validateCatalogSelection,
    )

    licenseAcceptanceStep = WorkflowStep(
        id="license-acceptance",
        heading="License Terms",
        heading_level="h1",
        description=[
            "To continue with the installation, you must accept the license terms for the target release.",
        ],
        screen_class=LicenseAcceptanceScreen,
        condition=lambda p: appInstance.licenseAcceptancePending(),
    )

    icrCredentialsStep = WorkflowStep(
        id="icr-credentials",
        heading="IBM Container Registry",
        heading_level="h1",
        description=[
            "Provide your IBM entitlement key to download Maximo Application Suite container images.",
        ],
        fields=[
            WorkflowField(
                id="ibm_entitlement_key",
                label="IBM Entitlement Key",
                type="password",
                sensitive=True,
                required=True,
            ),
        ],
        validator=appInstance.validateEntitlementKeyStep,
    )

    storageClassesStep = WorkflowStep(
        id="storage-classes",
        heading="Storage Classes",
        heading_level="h1",
        description=[
            "Configure ReadWriteOnce (RWO) and ReadWriteMany (RWX) storage classes for MAS volumes.",
        ],
        fields=[
            WorkflowField(
                id="storage_class_rwo",
                label="ReadWriteOnce (RWO) Storage Class",
                type="string",
                default=appInstance.params.get("storage_class_rwo", ""),
                required=True,
            ),
            WorkflowField(
                id="storage_class_rwx",
                label="ReadWriteMany (RWX) Storage Class",
                type="string",
                default=appInstance.params.get("storage_class_rwx", ""),
                required=True,
            ),
        ],
        validator=appInstance.validateStorageClasses,
    )

    licensingStep = WorkflowStep(
        id="licensing-sls",
        heading="AppPoint Licensing & Contacts",
        heading_level="h1",
        description=[
            "Configure AppPoint licensing (SLS) and contact information for the Data Reporter Operator (DRO).",
        ],
        fields=[
            WorkflowField(
                id="license_file",
                label="SLS License File Path (optional if SLS exists)",
                type="file",
                required=False,
            ),
            WorkflowField(
                id="dro_contact_email",
                label="Contact Email",
                type="string",
                required=True,
            ),
            WorkflowField(
                id="dro_contact_firstname",
                label="Contact First Name",
                type="string",
                required=True,
            ),
            WorkflowField(
                id="dro_contact_lastname",
                label="Contact Last Name",
                type="string",
                required=True,
            ),
        ],
        validator=appInstance.validateLicensing,
    )

    masInstanceStep = WorkflowStep(
        id="mas-instance",
        heading="Configure MAS Instance",
        heading_level="h1",
        description=[
            "Set your MAS instance identifier, workspace, and operational settings.",
        ],
        fields=[
            WorkflowField(
                id="mas_instance_id",
                label="Instance ID",
                type="string",
                required=True,
            ),
            WorkflowField(
                id="mas_workspace_id",
                label="Workspace ID",
                type="string",
                default="masdev",
                required=True,
            ),
            WorkflowField(
                id="mas_workspace_name",
                label="Workspace Name",
                type="string",
                default="MAS Workspace",
                required=True,
            ),
            WorkflowField(
                id="environment_type",
                label="Operational Mode",
                type="select",
                options=["production", "non-production"],
                default="production",
                required=True,
            ),
            WorkflowField(
                id="mas_admin_mode",
                label="MAS Admin Mode",
                type="select",
                options=["cluster", "namespaced", "minimal"],
                default="cluster",
                required=False,
            ),
        ],
        validator=appInstance.validateMasInstance,
    )

    applicationsStep = WorkflowStep(
        id="applications",
        heading="Select Applications",
        heading_level="h1",
        description=[
            "Select the Maximo Application Suite applications to install.",
        ],
        fields=[
            WorkflowField(
                id="selected_apps",
                label="Applications",
                type="multi_select",
                options=["manage", "iot", "monitor", "assist", "optimizer", "visualinspection", "facilities", "aiservice"],
                required=False,
            ),
        ],
        validator=appInstance.validateSelectedApps,
    )

    reviewStep = WorkflowStep(
        id="review",
        heading="Review Settings",
        heading_level="h1",
        description=["Please carefully review your choices below."],
        screen_class=ReviewScreen,
        screen_kwargs={
            "review_builder": buildInstallReview,
            "command_builder": _nonInteractiveCommand,
            "script_filename_builder": _scriptFilename,
        },
        summary=[
            WorkflowSummaryItem(label="MAS Instance ID", param="mas_instance_id"),
            WorkflowSummaryItem(label="Catalog Version", param="mas_catalog_version"),
            WorkflowSummaryItem(label="MAS Channel", param="mas_channel"),
            WorkflowSummaryItem(label="Workspace ID", param="mas_workspace_id"),
            WorkflowSummaryItem(label="Storage Class (RWO)", param="storage_class_rwo"),
            WorkflowSummaryItem(label="Storage Class (RWX)", param="storage_class_rwx"),
            WorkflowSummaryItem(label="Pipeline Storage Class", attr="pipelineStorageClass"),
            WorkflowSummaryItem(label="Pipeline Storage Access Mode", attr="pipelineStorageAccessMode"),
        ],
    )

    launchStep = WorkflowStep(
        id="launch",
        heading="Launch Install",
        heading_level="h1",
        description=["Submitting the Tekton pipeline for MAS install."],
        screen_class=LaunchScreen,
        screen_kwargs={
            "command_builder": _nonInteractiveCommand,
            "launch_method": "launchInstall",
        },
    )

    return [
        connectStep,
        catalogStep,
        licenseAcceptanceStep,
        icrCredentialsStep,
        storageClassesStep,
        licensingStep,
        masInstanceStep,
        applicationsStep,
        reviewStep,
        launchStep,
    ]
