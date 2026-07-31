#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Update command entry-point for the MAS CLI.

``UpdateApp`` is the thin orchestrator that wires together the four mixins:

- ``CatalogMixin``             — catalog validation and instance review
- ``DependencyDetectionMixin`` — third-party workload detection
- ``UpdateRBACMixin``          — pre-install RBAC evaluation
- ``AdditionalConfigsMixin``   — additional-config file handling (from install)

The ``update()`` method is the only piece of logic that lives here; everything
else delegates to one of the mixins above.
"""

import logging
from typing import Callable, Optional

from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

from ..cli import BaseApp
from .argParser import updateArgParser
from .catalog import CatalogMixin
from .dependencies import DependencyDetectionMixin
from .rbac import UpdateRBACMixin
from mas.devops.data import getCatalog, getNewestCatalogTag
from mas.devops.ocp import createNamespace, getConsoleURL
from mas.devops.mas import getInstalledApps
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchUpdatePipeline, prepareUpdateSecrets
from mas.devops.pre_install import applyPreInstallMASRBAC
from ..install.settings import AdditionalConfigsMixin

logger = logging.getLogger(__name__)


class UpdateApp(BaseApp, AdditionalConfigsMixin, CatalogMixin, DependencyDetectionMixin, UpdateRBACMixin):
    """Orchestrator for the ``mas-cli update`` command.

    Inherits all method implementations from the four mixins; this class owns
    only ``update(argv)``, ``launchUpdate()``, and the instance-variable
    initialisation shared by both the CLI and TUI execution paths.
    """

    def __init__(self) -> None:
        """Initialise UpdateApp with safe defaults for all instance variables.

        All attributes read by launchUpdate() are set here so the TUI path
        (which constructs UpdateApp() directly without calling update()) works
        correctly. The CLI path's update() method overwrites these as needed.
        """
        super().__init__()
        self.db2LicenseFileLocal: Optional[str] = None
        self.db2LicenseFileSecret = None
        self.instancesNeedingRBAC: list = []
        self.applyPreInstallMASRBAC: bool = False
        self.devMode: bool = False
        self.noConfirm: bool = False
        # Transient state populated by detectMongoDb() and detectDb2u()
        self.mongoCurrentVersion: Optional[str] = None
        self.mongoTargetVersion: Optional[str] = None
        self.db2CurrentMajorVersion: Optional[int] = None
        self.db2TargetMajorVersion: Optional[int] = None

    def update(self, argv):
        """Parse arguments and execute the full update workflow.

        Args:
            argv: Raw argument list passed from the CLI entry-point or test.
        """
        self.args = updateArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode
        self.db2LicenseFileLocal = None
        self.instancesNeedingRBAC = []
        self.applyPreInstallMASRBAC = False
        self.mongoCurrentVersion = None
        self.mongoTargetVersion = None
        self.db2CurrentMajorVersion = None
        self.db2TargetMajorVersion = None

        if self.args.mas_catalog_version:
            # Non-interactive mode
            logger.debug("Maximo Operator Catalog version is set, so we assume already connected to the desired OCP")
            requiredParams = ["mas_catalog_version"]
            optionalParams = [
                "db2_namespace",
                "db2_v12_upgrade",
                "mongodb_namespace",
                "mongodb_v5_upgrade",
                "mongodb_v6_upgrade",
                "mongodb_v7_upgrade",
                "mongodb_v8_upgrade",
                "kafka_namespace",
                "kafka_provider",
                "dro_storage_class",
                "dro_namespace",
                "skip_pre_check",
                "dev_mode",
                "cpd_product_version",
                "image_pull_policy",
                # Dev Mode
                "artifactory_username",
                "artifactory_token",
                # Slack Integration
                "slack_token",
                "slack_channel",
            ]
            for key, value in vars(self.args).items():
                if key in requiredParams:
                    if value is None:
                        self.fatalError(f"{key} must be set")
                    else:
                        self.setParam(key, value)
                elif key in optionalParams:
                    if value is not None:
                        self.setParam(key, value)
                elif key in ["no_confirm", "help"]:
                    pass
                elif key == "db2_license_file":
                    if value is not None and value != "":
                        self.db2LicenseFileLocal = value
                else:
                    print(f"Unknown option: {key} {value}")
                    self.fatalError(f"Unknown option: {key} {value}")
        else:
            # Interactive mode — handled by serveTuiMode in __main__.py
            pass

        if self.dynamicClient is None:
            self.fatalError("Not successfully connected to a Kubernetes cluster.  See log file for details")

        # Check whether the cluster is set up for airgap install; triggers an
        # early failure if the cluster is using the deprecated ICSP instead of IDMS.
        self.isAirgap()
        self.reviewCurrentCatalog()
        isMasInstalled = self.reviewMASInstance()
        isAiServiceInstalled = self.reviewAiServiceInstance()
        if not isMasInstalled and not isAiServiceInstalled:
            self.fatalError("No MAS or AI Service instances were detected on the cluster => nothing to update! See log file for details")

        # Validate or load the chosen catalog
        if not self.devMode:
            self.validateCatalog()
        else:
            catalogVersion = self.getParam("mas_catalog_version") if self.args.mas_catalog_version else getNewestCatalogTag()
            self.chosenCatalog = getCatalog(catalogVersion)

        self.printH1("Dependency Update Checks")
        self.runDependencyChecks()

        print()

        self.reviewDependencyUpgrades()

        self.printH1("Review Settings")
        self.printDescription(["Connected to:", f" - <u>{getConsoleURL(self.dynamicClient)}</u>"])

        self.printH2("IBM Maximo Operator Catalog")
        assert self.installedCatalogId is not None, "Catalog ID is not set"
        self.printSummary("Installed Catalog", self.installedCatalogId)
        self.printSummary("Updated Catalog", self.getParam("mas_catalog_version"))

        self.printH2("Supported Dependency Updates")
        if self.getParam("db2_namespace") != "":
            self.printSummary("IBM Db2", f"All Db2uCluster and Db2uInstance instances in {self.getParam('db2_namespace')}")
        else:
            self.printSummary("IBM Db2", "No action required")

        if self.getParam("mongodb_namespace") != "":
            self.printSummary("MongoDb CE", f"All MongoDbCommunity instances in {self.getParam('mongodb_namespace')}")
        else:
            self.printSummary("MongoDb CE", "No action required")

        if self.getParam("kafka_namespace") != "":
            self.printSummary("Apache Kafka", f"All Kafka instances in {self.getParam('kafka_namespace')}")
        else:
            self.printSummary("Apache Kafka", "No action required")

        if self.getParam("cp4d_update") != "":
            self.printSummary("IBM Cloud Pak for Data", "Platform and services in ibm-cpd")
        else:
            self.printSummary("IBM Cloud Pak for Data", "No action required")

        self.printH2("Required Migrations")
        self.printSummary("Grafana v4 Operator", "Migrate to Grafana v5 Operator" if self.getParam("grafana_v5_upgrade") != "" else "No action required")
        self.printSummary(
            "AI Service Data Science Platform", "Migrate from ODH to RHOAI" if self.getParam("odh_to_rhoai_migration") != "" else "No action required"
        )

        if not self.noConfirm:
            print()
            self.printDescription(["Please carefully review your choices above, correcting mistakes now is much easier than after the update has begun"])
            continueWithUpdate = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the update pipeline
        if self.noConfirm or continueWithUpdate:
            self.db2LicenseFile()
            self.createTektonFileWithDigest()

            self.printH1("Launch Update")
            self.launchUpdate()

    def launchUpdate(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Submit the Tekton update pipeline, reporting stages via progressCallback.

        Pure-work method with no printH1, yesOrNo, or printDescription calls.
        Called from the TUI LaunchScreen (with a progressCallback that streams
        each stage to the step-list) and from the non-interactive update() path
        (with progressCallback=None, where Halo spinners are used directly —
        keeping existing CLI behaviour completely unchanged).

        Args:
            progressCallback (Callable, optional): Called as
                (label: str, ok: bool, detail: str) -> None after each stage.
                When None, Halo spinners are used instead.
            startCallback (Callable, optional): Called as (label: str) -> None
                immediately before each stage starts (TUI path only).  Allows
                the UI to mark the step as in-progress before the work runs.
                Defaults to None.
        """
        pipelinesNamespace = "mas-pipelines"

        if progressCallback is not None:
            # TUI path — call devops functions directly and report each stage.
            if startCallback is not None:
                startCallback("Validate OpenShift Pipelines")
            if installOpenShiftPipelines(self.dynamicClient):
                progressCallback("Validate OpenShift Pipelines", True, "Operator is installed and ready to use")
            else:
                progressCallback("Validate OpenShift Pipelines", False, "Operator installation failed")
                raise RuntimeError("OpenShift Pipelines installation failed")

            if self.applyPreInstallMASRBAC and self.instancesNeedingRBAC:
                for instanceInfo in self.instancesNeedingRBAC:
                    instanceId = instanceInfo["id"]
                    targetVersion = instanceInfo["targetVersion"]
                    adminMode = instanceInfo["adminMode"]
                    if startCallback is not None:
                        startCallback(f"Apply pre-install RBAC: {instanceId}")
                    selectedApps = getInstalledApps(self.dynamicClient, instanceId)
                    applyPreInstallMASRBAC(
                        dynClient=self.dynamicClient,
                        masVersion=".".join(targetVersion.split(".")[:2]),
                        masInstanceId=instanceId,
                        adminMode=adminMode,
                        selectedApps=selectedApps,
                    )
                    progressCallback(f"Apply pre-install RBAC: {instanceId}", True, f"{targetVersion}, mode: {adminMode}")

            if startCallback is not None:
                startCallback("Prepare pipelines namespace")
            createNamespace(self.dynamicClient, pipelinesNamespace)
            preparePipelinesNamespace(dynClient=self.dynamicClient)
            prepareUpdateSecrets(
                dynClient=self.dynamicClient,
                slack_token=self.getParam("slack_token"),
                slack_channel=self.getParam("slack_channel"),
                db2LicenseFile=self.db2LicenseFileSecret,
            )
            progressCallback("Prepare pipelines namespace", True, pipelinesNamespace)

            if startCallback is not None:
                startCallback("Install Tekton definitions")
            updateTektonDefinitions(self.dynamicClient, pipelinesNamespace, self.tektonDefsPath)
            progressCallback("Install Tekton definitions", True, f"v{self.version}")

            if startCallback is not None:
                startCallback("Submit PipelineRun")
            pipelineURL = launchUpdatePipeline(dynClient=self.dynamicClient, params=self.params)
            if pipelineURL is not None:
                progressCallback("Submit PipelineRun", True, pipelineURL)
            else:
                progressCallback("Submit PipelineRun", False, "Failed — see log file for details")
        else:
            # CLI path — use Halo spinners exactly as before.
            with Halo(text="Validating OpenShift Pipelines installation", spinner=self.spinner) as h:
                if installOpenShiftPipelines(self.dynamicClient):
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator installation failed")
                    self.fatalError("Installation failed")

            # Apply pre-install RBAC if user has permissions
            if self.applyPreInstallMASRBAC and self.instancesNeedingRBAC:
                print()
                print_formatted_text(HTML(f"<Yellow>Applying RBAC for {len(self.instancesNeedingRBAC)} instance(s) transitioning to GA...</Yellow>"))
                print()

                for instanceInfo in self.instancesNeedingRBAC:
                    instanceId = instanceInfo["id"]
                    targetVersion = instanceInfo["targetVersion"]
                    adminMode = instanceInfo["adminMode"]

                    selectedApps = getInstalledApps(self.dynamicClient, instanceId)

                    with Halo(text=f"Applying pre-install RBAC for instance: {instanceId} ({targetVersion}, mode: {adminMode})", spinner=self.spinner) as h:
                        applyPreInstallMASRBAC(
                            dynClient=self.dynamicClient,
                            masVersion=".".join(targetVersion.split(".")[:2]),
                            masInstanceId=instanceId,
                            adminMode=adminMode,
                            selectedApps=selectedApps,
                        )
                        h.stop_and_persist(symbol=self.successIcon, text=f"Pre-install RBAC applied for {instanceId} ({targetVersion}, mode: {adminMode})")

                print()
                print_formatted_text(HTML("<Green>✓ Pre-install RBAC applied successfully for all instances transitioning to GA</Green>"))
                print()

            with Halo(text=f"Preparing namespace ({pipelinesNamespace})", spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(dynClient=self.dynamicClient)
                prepareUpdateSecrets(
                    dynClient=self.dynamicClient,
                    slack_token=self.getParam("slack_token"),
                    slack_channel=self.getParam("slack_channel"),
                    db2LicenseFile=self.db2LicenseFileSecret,
                )

            with Halo(text=f"Installing latest Tekton definitions (v{self.version})", spinner=self.spinner) as h:
                updateTektonDefinitions(self.dynamicClient, pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text="Submitting PipelineRun for MAS update", spinner=self.spinner) as h:
                pipelineURL = launchUpdatePipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text="PipelineRun for MAS update submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text="Failed to submit PipelineRun for MAS update, see log file for details")
                    print()
