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

    def _validateOpenShiftPipelines(self) -> tuple[bool, str]:
        """Validate OpenShift Pipelines installation.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        if installOpenShiftPipelines(self.dynamicClient):
            return True, "Operator is installed and ready to use"
        return False, "Operator installation failed"

    def _prepareNamespace(self, namespace: str) -> tuple[bool, str]:
        """Prepare pipelines namespace and secrets.

        Args:
            namespace (str): Namespace to prepare

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        createNamespace(self.dynamicClient, namespace)
        preparePipelinesNamespace(dynClient=self.dynamicClient)
        prepareUpdateSecrets(
            dynClient=self.dynamicClient,
            slack_token=self.getParam("slack_token"),
            slack_channel=self.getParam("slack_channel"),
            db2LicenseFile=self.db2LicenseFileSecret,
        )
        return True, namespace

    def _installTektonDefinitions(self, namespace: str) -> tuple[bool, str]:
        """Install Tekton definitions.

        Args:
            namespace (str): Namespace to install definitions in

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        updateTektonDefinitions(self.dynamicClient, namespace, self.tektonDefsPath)
        return True, f"v{self.version}"

    def _submitPipelineRun(self) -> tuple[bool, str]:
        """Submit the update PipelineRun.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        pipelineURL = launchUpdatePipeline(dynClient=self.dynamicClient, params=self.params)
        if pipelineURL:
            return True, pipelineURL
        return False, "Failed — see log file for details"

    def launchUpdate(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Submit the Tekton update pipeline with unified progress reporting.

        Uses the ProgressReporter abstraction to eliminate code duplication
        between CLI (Halo spinners) and TUI (callbacks) execution paths.

        Args:
            progressCallback (Callable, optional): TUI callback (label, ok, detail) -> None
            startCallback (Callable, optional): TUI start callback (label) -> None
        """
        from mas.cli.common.progress import HaloProgressReporter, CallbackProgressReporter

        # Select reporter based on execution mode
        if progressCallback is not None:
            reporter = CallbackProgressReporter(progressCallback, startCallback)
        else:
            reporter = HaloProgressReporter(self.spinner, self.successIcon, self.failureIcon)

        pipelinesNamespace = "mas-pipelines"

        # Stage 1: Validate OpenShift Pipelines
        reporter.start("Validate OpenShift Pipelines")
        success, detail = self._validateOpenShiftPipelines()
        if success:
            reporter.success("Validate OpenShift Pipelines", detail)
        else:
            reporter.failure("Validate OpenShift Pipelines", detail)
            raise RuntimeError("OpenShift Pipelines installation failed")

        # Stage 2: Apply pre-install RBAC (if needed)
        if self.applyPreInstallMASRBAC and self.instancesNeedingRBAC:
            if progressCallback is None:
                # CLI path: print header
                print()
                print_formatted_text(HTML(f"<Yellow>Applying RBAC for {len(self.instancesNeedingRBAC)} instance(s) transitioning to GA...</Yellow>"))
                print()

            for instanceInfo in self.instancesNeedingRBAC:
                instanceId = instanceInfo["id"]
                targetVersion = instanceInfo["targetVersion"]
                adminMode = instanceInfo["adminMode"]

                label = f"Apply pre-install RBAC: {instanceId}"
                reporter.start(label)

                selectedApps = getInstalledApps(self.dynamicClient, instanceId)
                applyPreInstallMASRBAC(
                    dynClient=self.dynamicClient,
                    masVersion=".".join(targetVersion.split(".")[:2]),
                    masInstanceId=instanceId,
                    adminMode=adminMode,
                    selectedApps=selectedApps,
                )
                reporter.success(label, f"{targetVersion}, mode: {adminMode}")

            if progressCallback is None:
                # CLI path: print footer
                print()
                print_formatted_text(HTML("<Green>✓ Pre-install RBAC applied successfully for all instances transitioning to GA</Green>"))
                print()

        # Stage 3: Prepare namespace
        reporter.start("Prepare pipelines namespace")
        success, detail = self._prepareNamespace(pipelinesNamespace)
        reporter.success("Prepare pipelines namespace", detail)

        # Stage 4: Install Tekton definitions
        reporter.start("Install Tekton definitions")
        success, detail = self._installTektonDefinitions(pipelinesNamespace)
        reporter.success("Install Tekton definitions", detail)

        # Stage 5: Submit PipelineRun
        reporter.start("Submit PipelineRun")
        success, detail = self._submitPipelineRun()
        if success:
            reporter.success("Submit PipelineRun", detail)
            if progressCallback is None:
                # CLI path: print URL
                print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{detail}</u></Cyan>\n"))
        else:
            reporter.failure("Submit PipelineRun", detail)
            if progressCallback is None:
                print()
