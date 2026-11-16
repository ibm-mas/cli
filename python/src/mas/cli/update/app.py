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

import logging
import re
from typing import Callable, Optional

from halo import Halo
from prompt_toolkit import print_formatted_text, HTML

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from ..cli import BaseApp
from .argParser import updateArgParser
from .dependencies import DetectResult, _DEPENDENCY_CHECKS as _DEPENDENCY_CHECKS_REGISTRY
from mas.devops.data import getCatalog, getNewestCatalogTag, NoSuchCatalogError
from mas.devops.ocp import createNamespace, getConsoleURL, getClusterVersion, isClusterVersionInRange
from mas.devops.mas import listMasInstances, getCurrentCatalog, getMasChannel, getInstalledApps, getPermissionMode
from mas.devops.aiservice import listAiServiceInstances
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchUpdatePipeline, prepareUpdateSecrets
from mas.devops.pre_install import applyPreInstallMASRBAC
from mas.devops.utils import isVersionEqualOrAfter
from ..install.app import InstallApp
from ..install.settings import AdditionalConfigsMixin
from ..rbac_utils import evaluatePreinstallRBACAccess

logger = logging.getLogger(__name__)


class UpdateApp(BaseApp, AdditionalConfigsMixin):
    """Orchestrator for the ``mas-cli update`` command.

    The ``update()`` method drives both the non-interactive path (``--catalog``
    and friends) and the legacy interactive prompt path.  The Textual TUI path
    (``mas-cli update`` with no arguments) drives the same logic through the
    workflow definition in ``update/workflow.py`` via ``_postConnectChecks``,
    ``checkCatalog``/``validateCatalogSelection``, ``runDependencyChecks`` and
    ``launchUpdate``.
    """

    # Ordered registry of pre-update dependency checks (see update/dependencies.py)
    _DEPENDENCY_CHECKS = _DEPENDENCY_CHECKS_REGISTRY

    def __init__(self) -> None:
        """Initialise UpdateApp with safe defaults for all instance variables.

        All attributes read by the TUI execution path (which constructs
        ``UpdateApp()`` directly without calling ``update()``) are set here.
        The ``update()`` method overwrites these as needed.
        """
        super().__init__()
        self.installedCatalogId: Optional[str] = None
        self.chosenCatalog: Optional[dict] = None
        self.db2LicenseFileLocal: Optional[str] = None
        self.db2LicenseFileSecret: Optional[dict] = None
        self.instancesNeedingRBAC: list = []
        self.applyPreInstallMASRBAC: bool = False
        self.devMode: bool = False
        self.noConfirm: bool = False
        # Transient state populated by the dependency detectors and consumed
        # by reviewDependencyUpgrades() (CLI) / _assertUpgradeConfirmations() (TUI)
        self.rhoaiV2Detected: bool = False
        self.mongoCurrentVersion: Optional[str] = None
        self.mongoTargetVersion: Optional[str] = None
        self.db2CurrentMajorVersion: Optional[int] = None
        self.db2TargetMajorVersion: Optional[int] = None

    def shouldApplyRBACForInstance(self, instanceId, currentVersion, targetCatalog) -> bool:
        """
        Determine if RBAC should be applied for a specific MAS instance during update.
        Returns True if the instance is transitioning from pre-release to GA version.

        This method checks:
        1. Current version is a pre-release (e.g., "9.2.0-pre.stable+21734")
        2. Target catalog contains a GA version (e.g., "9.2.0") for the instance's channel
        3. The GA version is >= 9.2.0 (when RBAC was introduced)

        Args:
            instanceId: The MAS instance ID
            currentVersion: The current reconciled version (e.g., "9.2.0-pre.stable+21734")
            targetCatalog: The target catalog dictionary containing version mappings

        Returns:
            bool: True if RBAC should be applied for pre-release → GA transition, False otherwise
        """
        if not currentVersion or not targetCatalog:
            return False

        # Check if current version is a pre-release
        if "-pre" not in currentVersion:
            return False

        # Get the channel this instance is subscribed to
        channel = getMasChannel(self.dynamicClient, instanceId)
        if not channel:
            logger.warning(f"Could not determine channel for instance {instanceId}")
            return False

        # Get the target version from the catalog for this channel
        targetVersion = targetCatalog.get("mas_core_version", {}).get(channel)
        if not targetVersion:
            logger.warning(f"No target version found in catalog for channel {channel}")
            return False

        # Check if target version is GA (not pre-release)
        if "-pre" in targetVersion:
            logger.info(f"Instance {instanceId} will stay on pre-release (current: {currentVersion}, target: {targetVersion}). Skipping RBAC.")
            return False

        # Only apply RBAC if target GA version is >= 9.2.0

        if isVersionEqualOrAfter("9.2.0", targetVersion):
            logger.info(f"Instance {instanceId} will transition from pre-release to GA (current: {currentVersion}, target: {targetVersion}).")
            return True

        logger.info(f"Instance {instanceId} target version {targetVersion} is < 9.2.0. Skipping RBAC.")
        return False

    def evaluatePreinstallRBACAccessForUpdate(self) -> None:
        """
        Evaluate if pre-install RBAC should be applied for instances transitioning from pre-release to GA.
        Sets self.instancesNeedingRBAC list and self.applyPreInstallMASRBAC flag.

        This method identifies instances needing RBAC and calls the shared evaluatePreinstallRBACAccess()
        function from rbac_utils to check permissions for each instance needing RBAC.
        """

        self.instancesNeedingRBAC = []
        self.applyPreInstallMASRBAC = False

        try:
            masInstances = listMasInstances(self.dynamicClient)

            for instance in masInstances:
                instanceId = instance["metadata"]["name"]
                currentVersion = self.getReconciledVersion(instance)

                if self.shouldApplyRBACForInstance(instanceId, currentVersion, self.chosenCatalog):
                    channel = getMasChannel(self.dynamicClient, instanceId)
                    targetVersion = self.chosenCatalog.get("mas_core_version", {}).get(channel, "")

                    # Detect admin mode for this instance based on target version
                    detectedMode = None
                    if targetVersion == "9.2.0":
                        # Transitioning to 9.2.0 GA (first release with admin modes): default to cluster mode
                        detectedMode = "cluster"
                        logger.info(msg=f"MAS instance {instanceId} transitioning to 9.2.0 GA: defaulting to cluster mode")
                    elif isVersionEqualOrAfter("9.3.0", targetVersion):
                        # Transitioning to 9.3.0 GA or later: detect existing mode
                        detectedMode = getPermissionMode(self.dynamicClient, instanceId)
                        logger.info(f"Detected admin mode '{detectedMode}' for MAS instance {instanceId} (target: {targetVersion})")

                    self.instancesNeedingRBAC.append(
                        {"id": instanceId, "currentVersion": currentVersion, "targetVersion": targetVersion, "channel": channel, "adminMode": detectedMode}
                    )

            if not self.instancesNeedingRBAC:
                logger.info("No MAS instances require RBAC update (not transitioning from pre-release to GA)")
                return

            instancesNeedingRbacCheck = [inst for inst in self.instancesNeedingRBAC if inst["adminMode"] != "minimal"]

            if not instancesNeedingRbacCheck:
                logger.info("All instances are in minimal mode, no pre-install RBAC needed")
                return

            firstInstance = instancesNeedingRbacCheck[0]
            self.applyPreInstallMASRBAC = evaluatePreinstallRBACAccess(
                dynamicClient=self.dynamicClient,
                masChannel=firstInstance["targetVersion"],
                adminMode=firstInstance["adminMode"],
                instanceId=firstInstance["id"],
                noConfirm=self.noConfirm,
                printH1Func=self.printH1,
                printDescriptionFunc=self.printDescription,
                yesOrNoFunc=self.yesOrNo,
                fatalErrorFunc=self.fatalError,
                operation="update",
            )

        except Exception as e:
            logger.error(f"Error while evaluating pre-install RBAC: {e}")
            self.printWarning(f"Failed to evaluate pre-install RBAC: {e}\nContinuing with update, but RBAC may need to be applied manually.")

    def checkRoutingModeForUpdate(self) -> None:
        """Block the update when a MAS 9.2+ instance has routingMode "path" and is moving off a catalog without path routing support.

        Catalogs listed in InstallApp._PATH_ROUTING_UNSUPPORTED_CATALOGS do not support path-based routing, but a
        routingMode of "path" may have been accidentally written to Suite CRs while on them. Updating to a catalog
        that does support path-based routing would cause an unintended routing mode switch, so the update is stopped
        with remediation guidance.

        The check is skipped when the installed catalog is unknown, already supports path routing, or when the target
        catalog also lacks path routing support.
        """
        unsupportedCatalogs = InstallApp._PATH_ROUTING_UNSUPPORTED_CATALOGS
        targetCatalog = self.getParam("mas_catalog_version")

        if not self.installedCatalogId or not any(c in self.installedCatalogId for c in unsupportedCatalogs):
            return
        if any(c in targetCatalog for c in unsupportedCatalogs):
            return

        for instance in listMasInstances(self.dynamicClient):
            instanceId = instance["metadata"]["name"]
            if not isVersionEqualOrAfter("9.2.0", self.getReconciledVersion(instance)):
                continue

            if instance.get("spec", {}).get("settings", {}).get("routingMode") == "path":
                self.fatalError(
                    f'Cannot update from catalog {self.installedCatalogId} to {targetCatalog}: spec.settings.routingMode is set to "path" '
                    f"on the Suite CR for instance {instanceId}.\n\n"
                    f"Catalog {self.installedCatalogId} does not support path-based routing, so this value was set in error and the update\n"
                    "would attempt an unintended routing mode switch.\n\n"
                    "To resolve this, remove the field from the Suite CR before retrying the update:\n\n"
                    f"  oc patch suite {instanceId} -n mas-{instanceId}-core --type=json \\\n"
                    '    -p \'[{"op":"remove","path":"/spec/settings/routingMode"}]\'\n\n'
                    "After applying the patch, re-run the update."
                )

    def update(self, argv):
        """
        Update MAS instance
        """
        self.args = updateArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.devMode = self.args.dev_mode
        self.db2LicenseFileLocal = None
        self.instancesNeedingRBAC = []
        self.applyPreInstallMASRBAC = False
        self.rhoaiV2Detected = False
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
                # These fields we just pass straight through to the parameters and fail if they are not set
                if key in requiredParams:
                    if value is None:
                        self.fatalError(f"{key} must be set")
                    else:
                        self.setParam(key, value)

                # These fields we just pass straight through to the parameters
                elif key in optionalParams:
                    if value is not None:
                        self.setParam(key, value)

                # Arguments that we don't need to do anything with
                elif key in ["no_confirm", "help"]:
                    pass

                # Db2 License file has special handling
                elif key == "db2_license_file":
                    if value is not None and value != "":
                        self.db2LicenseFileLocal = value

                # Fail if there's any arguments we don't know how to handle
                else:
                    print(f"Unknown option: {key} {value}")
                    self.fatalError(f"Unknown option: {key} {value}")
        else:
            # Interactive mode
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()

        if self.dynamicClient is None:
            self.fatalError("Not successfully connected to a Kubernetes cluster.  See log file for details")

        # Perform a check whether the cluster is set up for airgap install, this will trigger an early failure if the cluster is using the now
        # deprecated MaximoApplicationSuite ImageContentSourcePolicy instead of the new ImageDigestMirrorSet
        self.isAirgap()
        self.reviewCurrentCatalog()
        isMasInstalled = self.reviewMASInstance()
        isAiServiceInstalled = self.reviewAiServiceInstance()
        if not isMasInstalled and not isAiServiceInstalled:
            self.fatalError("No MAS or AI Service instances were detected on the cluster => nothing to update! See log file for details")

        if self.args.mas_catalog_version is None:
            # Interactive mode
            self.chooseCatalog()

        # Validations
        if not self.devMode:
            self.validateCatalog()
        else:
            # In dev mode the catalog version may be a custom dev image tag that has no
            # corresponding YAML definition, so fall back to the newest known catalog.
            catalogVersion = self.getParam("mas_catalog_version") if self.args.mas_catalog_version else getNewestCatalogTag()
            try:
                self.chosenCatalog = getCatalog(catalogVersion)
            except NoSuchCatalogError:
                self.chosenCatalog = getCatalog(getNewestCatalogTag())

        self.checkRoutingModeForUpdate()

        self.printH1("Dependency Update Checks")
        self.runDependencyChecks()

        # Interactive confirmations for MongoDB / Db2 major version upgrades
        # (deferred until after all checks so the CLI and TUI share the same
        # detection logic)
        self.reviewDependencyUpgrades()

        print()

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
        if self.getParam("odh_to_rhoai_migration") == "":
            aiServiceDataScienceMigration = "No action required"
        elif self.rhoaiV2Detected:
            aiServiceDataScienceMigration = "Upgrade from RHOAI v2 to RHOAI v3"
        else:
            aiServiceDataScienceMigration = "Migrate from ODH to RHOAI"
        self.printSummary("AI Service Data Science Platform", aiServiceDataScienceMigration)

        if not self.noConfirm:
            print()
            self.printDescription(["Please carefully review your choices above, correcting mistakes now is much easier than after the update has begun"])
            continueWithUpdate = self.yesOrNo("Proceed with these settings")
        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithUpdate:
            self.printH1("Launch Update")
            self.launchUpdate()

    # ------------------------------------------------------------------
    # Catalog selection and review
    # ------------------------------------------------------------------

    def reviewCurrentCatalog(self) -> None:
        """Detect and display the currently installed Maximo Operator Catalog.

        Sets ``self.installedCatalogId`` to the catalog ID string, or ``None``
        when the identity cannot be determined.  Terminal output is suppressed
        when running under the TUI.
        """
        catalogInfo = getCurrentCatalog(self.dynamicClient)
        self.installedCatalogId = None
        if catalogInfo is None:
            self.fatalError("Unable to locate existing install of the IBM Maximo Operator Catalog")
        elif catalogInfo["catalogId"] is None:
            if not self.tuiMode:
                self.printWarning("Unable to determine identity & version of currently installed ibm-maximo-operator-catalog")
        else:
            self.installedCatalogId = catalogInfo["catalogId"]
            if not self.tuiMode:
                self.printH1("Review Installed Catalog")
                self.printDescription(
                    [f"The currently installed Maximo Operator Catalog is <u>{catalogInfo['displayName']}</u>", f" <u>{catalogInfo['image']}</u>"]
                )

    def reviewMASInstance(self) -> bool:
        """Review all MAS Suite instances on the cluster.

        Returns:
            bool: True when at least one Suite instance is found.
        """
        return self.reviewInstances(listMasInstances, "MAS", "Suite.core.mas.ibm.com/v1")

    def reviewAiServiceInstance(self) -> bool:
        """Review all AI Service instances on the cluster.

        Returns:
            bool: True when at least one AI Service instance is found.
        """
        return self.reviewInstances(listAiServiceInstances, "AI Service", "AIServiceApp.aiservice.ibm.com/v1", "aiservice_instance_ids")

    def reviewInstances(self, getInstances: Callable, name: str, kind: str, instanceParamKey: str = "") -> bool:
        """Review instances returned by a list function and print a summary.

        Args:
            getInstances (Callable): Zero-argument callable returning a list of instance dicts.
            name (str): Human-readable resource type label (e.g. "MAS").
            kind (str): Kubernetes kind string used in fallback messages.
            instanceParamKey (str, optional): Param key to populate with a comma-separated list of instance IDs.

        Returns:
            bool: True when at least one instance is found.
        """
        if not self.tuiMode:
            self.printH1(f"Review {name} Instances")
        try:
            instances = getInstances(self.dynamicClient)

            if len(instances) == 0:
                if instanceParamKey != "":
                    self.setParam(instanceParamKey, "")
                if not self.tuiMode:
                    self.printDescription([f"No {name} instances were detected on the cluster"])
                return False

            if instanceParamKey != "":
                self.setParam(instanceParamKey, "")
                for instance in instances:
                    param = self.getParam(instanceParamKey)
                    self.setParam(instanceParamKey, f"{param},{instance['metadata']['name']}".lstrip(","))

            if not self.tuiMode:
                self.printDescription([f"The following {name} instances are installed on the target cluster and will be affected by the catalog update:"])
                for instance in instances:
                    instanceId = instance["metadata"]["name"]
                    reconciledVersion = self.getReconciledVersion(instance)
                    self.printDescription([f"- <u>{instanceId}</u> v{reconciledVersion}"])
            return True
        except ResourceNotFoundError:
            if instanceParamKey != "":
                self.setParam(instanceParamKey, "")
            if not self.tuiMode:
                self.printDescription([f"No {name} instances were detected on the cluster ({kind} API is not available)"])
            return False

    def getCatalogOptions(self) -> list:
        """Return the update-eligible catalog version options.

        These are the same entries shown in the interactive ``chooseCatalog``
        prompt — a short, curated list of recent releases.

        Returns:
            list: Ordered list of catalog version strings, newest first.
        """
        return [
            "v9-261105-amd64",
            "v9-261029-amd64",
            "v9-260924-amd64",
        ]

    def chooseCatalog(self) -> None:
        """Interactively prompt the user to select a target catalog version."""
        self.printH1("Select IBM Maximo Operator Catalog Version")
        self.printDescription(
            [
                "Select MAS Catalog",
                "  1) Nov 05 2026 Update (MAS 9.2.10, 9.1.29, 9.0.35, 8.11.34, &amp; 8.10.37)",
                "  2) Oct 29 2026 Update (MAS 9.2.9, 9.1.28, 9.0.34, 8.11.34, &amp; 8.10.37)",
                "  3) Sep 24 2026 Update (MAS 9.2.7, 9.1.26, 9.0.32, 8.11.34, &amp; 8.10.37)",
            ]
        )
        self.promptForListSelect("Select catalog version", self.getCatalogOptions(), "mas_catalog_version", default=1)

    def checkCatalog(self) -> None:
        """Validate the chosen catalog against the current cluster state.

        Loads ``self.chosenCatalog`` and checks OCP compatibility and catalog
        ordering.  Raises ``ValueError`` on failure so it is safe to use as a
        TUI step validator.

        Raises:
            ValueError: When the catalog is incompatible with OCP or is older
                than the installed catalog.
        """
        ocpVersion = getClusterVersion(self.dynamicClient)
        # Load the catalog information
        self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))
        supportedReleases = self.chosenCatalog.get("ocp_compatibility", [])
        if len(supportedReleases) > 0 and not isClusterVersionInRange(ocpVersion, supportedReleases):
            raise ValueError(
                f"IBM Maximo Operator Catalog {self.getParam('mas_catalog_version')} is not compatible with OpenShift v{ocpVersion}.  "
                f"Compatible OpenShift releases are {supportedReleases}"
            )

        if self.installedCatalogId is not None and self.installedCatalogId > self.getParam("mas_catalog_version"):
            raise ValueError(
                f"Selected catalog is older than the currently installed catalog.  "
                f"Unable to update catalog from {self.installedCatalogId} to {self.getParam('mas_catalog_version')}"
            )

    def validateCatalog(self) -> None:
        """Validate the chosen catalog, calling fatalError on failure.

        Wraps ``checkCatalog`` for the non-interactive path where a validation
        failure should terminate the process.
        """
        try:
            self.checkCatalog()
        except ValueError as e:
            self.fatalError(str(e))

    def validateCatalogSelection(self) -> None:
        """Validate the catalog selection for the TUI choose-catalog step.

        Runs ``checkCatalog()`` followed by ``checkRoutingModeForUpdate()``.
        Both raise on failure so the TUI can display the error inline; on the
        CLI path ``validateCatalog()`` and the direct
        ``checkRoutingModeForUpdate()`` call in ``update()`` provide the same
        checks with ``fatalError`` semantics.
        """
        self.checkCatalog()
        self.checkRoutingModeForUpdate()

    def _postConnectChecks(self) -> None:
        """Run the post-connection cluster review for the TUI path.

        Called as the connect-cluster step's ``post_connect`` callable: after
        a successful connection it performs the airgap check, detects the
        installed catalog, and verifies that at least one MAS or AI Service
        instance exists.  Failures raise (via ``fatalError`` under TUI mode)
        so the connect screen can display them inline.
        """
        self.isAirgap()
        self.reviewCurrentCatalog()
        isMasInstalled = self.reviewMASInstance()
        isAiServiceInstalled = self.reviewAiServiceInstance()
        if not isMasInstalled and not isAiServiceInstalled:
            self.fatalError("No MAS or AI Service instances were detected on the cluster => nothing to update! See log file for details")

    # ------------------------------------------------------------------
    # Dependency detection
    # ------------------------------------------------------------------

    def isWatsonDiscoveryInstalled(self) -> DetectResult:
        """Check whether IBM Watson Discovery is installed.

        Returns:
            DetectResult: ok=False with blocking message if found; ok=True otherwise.
        """
        try:
            wdAPI = self.dynamicClient.resources.get(api_version="discovery.watson.ibm.com/v1", kind="WatsonDiscovery")
            wds = wdAPI.get(namespace="ibm-cpd").to_dict()["items"]
            if len(wds) > 0:
                return DetectResult(
                    ok=False,
                    message=(
                        "Watson Discovery is currently installed in the instance of Cloud Pak for Data that is managed by the MAS CLI "
                        "(in the ibm-cpd namespace), this is no longer supported and the update can not proceed as a result. "
                        "Please contact IBM support for assistance"
                    ),
                )
        except (ResourceNotFoundError, NotFoundError):
            # Watson Discovery has never been installed on this cluster
            pass
        return DetectResult(ok=True, message="IBM Watson Discovery is not installed")

    def isWatsonOpenscaleInstalled(self) -> DetectResult:
        """Check whether IBM Watson OpenScale (AI Fairness 360) is installed.

        Returns:
            DetectResult: ok=False with blocking message if found; ok=True otherwise.
        """
        try:
            wosAPI = self.dynamicClient.resources.get(api_version="wos.cpd.ibm.com/v1", kind="WOService")
            wos = wosAPI.get(namespace="ibm-cpd").to_dict()["items"]
            if len(wos) > 0:
                return DetectResult(
                    ok=False,
                    message=(
                        "Watson Openscale is currently installed in the instance of Cloud Pak for Data that is managed by the MAS CLI "
                        "(in the ibm-cpd namespace), this is no longer supported and the update can not proceed as a result. "
                        "Please contact IBM support for assistance"
                    ),
                )
        except (ResourceNotFoundError, NotFoundError):
            # Watson Openscale has never been installed on this cluster
            pass
        return DetectResult(ok=True, message="IBM Watson Openscale is not installed")

    def isIBMCertManagerInstalled(self) -> DetectResult:
        """Check whether the legacy IBM Certificate Manager is installed.

        Returns:
            DetectResult: ok=False with blocking message if found; ok=True otherwise.
        """
        try:
            # Check if 'ibm-common-services' namespace exist, this will throw NotFoundError exception when not found
            namespaceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
            namespaceAPI.get(name="ibm-common-services")

            podsAPI = self.dynamicClient.resources.get(api_version="v1", kind="Pod")
            podsList = podsAPI.get(namespace="ibm-common-services")
            for pod in podsList.items:
                if pod is not None and "cert-manager-cainjector" in pod.metadata.name:
                    logger.debug("Found IBM Certificate-Manager in ibm-common-services namespace")
                    return DetectResult(
                        ok=False,
                        message=(
                            "IBM Certificate-Manager is currently installed and automatic migration of IBM Certificate-Manager "
                            "is no longer supported. Please contact IBM support for assistance."
                        ),
                    )
            logger.debug("There is an ibm-common-services namespace, but we did not find the IBM Certificate-Manager installation")
        except NotFoundError:
            logger.debug("There is no ibm-common-services namespace")
        return DetectResult(ok=True, message="IBM Certificate-Manager is not installed")

    def _runWithHalo(self, label: str, fn: Callable) -> None:
        """Run a detect function wrapped in a Halo spinner (CLI path only).

        Calls ``fn()`` which must return a ``DetectResult``.  The spinner is
        stopped with ``successIcon`` when ``result.ok`` is True, or
        ``failureIcon`` + ``fatalError`` when ``result.ok`` is False.
        ``result.message`` is used verbatim as the final spinner line.

        Args:
            label (str): Spinner text shown while the check is running.
            fn (Callable): Zero-argument callable returning a ``DetectResult``.
        """
        with Halo(text=label, spinner=self.spinner) as h:
            result = fn()
            if result.ok:
                h.stop_and_persist(symbol=self.successIcon, text=result.message)
            else:
                h.stop_and_persist(symbol=self.failureIcon, text=result.message)
                self.fatalError(result.message)

    def detectGrafana4(self) -> DetectResult:
        """Detect Grafana Operator v4 and set grafana_v5_upgrade param.

        Returns:
            DetectResult: Message describes whether migration is needed.
        """
        try:
            grafanaAPI = self.dynamicClient.resources.get(api_version="integreatly.org/v1alpha1", kind="Grafana")
            grafanaVersion4s = grafanaAPI.get().to_dict()["items"]
            if len(grafanaVersion4s) > 0:
                self.setParam("grafana_v5_upgrade", "true")
                if not self.tuiMode:
                    self.printDescription(
                        [
                            "<u>Dependency Upgrade Notice</u>",
                            "Grafana Operator v4 is currently installed and will be updated to v5",
                            "- Grafana v5 instance will have a new URL and admin password",
                            "- User accounts set up in the v4 instance will not be migrated",
                        ]
                    )
                return DetectResult(ok=True, message="Grafana Operator v4 instance will be updated to v5")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="Grafana Operator v4 is not installed")

    def detectODH(self) -> DetectResult:
        """Detect if ODH (Open Data Hub) is installed and may need migration to RHOAI.

        This is a simplified check - the Ansible role will perform detailed validation.

        Returns:
            DetectResult: Message describes whether RHOAI migration is needed.
        """
        try:
            subscriptionAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
            subscriptions = subscriptionAPI.get(namespace="openshift-operators").to_dict()["items"]
            odh_installed = any(sub.get("spec", {}).get("name") == "opendatahub-operator" for sub in subscriptions)
            if odh_installed:
                # Set parameter to trigger ODH to RHOAI migration
                self.setParam("odh_to_rhoai_migration", "true")
                if not self.tuiMode:
                    self.printDescription(
                        [
                            "<u>Required Migration Notice</u>",
                            "Open Data Hub (ODH) is currently installed and will be migrated to Red Hat OpenShift AI (RHOAI)",
                            "- The update process will automatically handle the migration",
                            "- ODH will be replaced with RHOAI",
                            "- This migration is mandatory to continue receiving updates",
                            "",
                            "<u>Expected Downtime</u>",
                            "- AI Service will be unavailable during migration (~10-12 minutes)",
                            "- Data science workloads will be temporarily interrupted",
                            "- Deployed models will be preserved",
                        ]
                    )
                return DetectResult(ok=True, message="Open Data Hub detected - migration to RHOAI will be evaluated")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="Open Data Hub is not installed")

    def detectRHOAIv2(self) -> DetectResult:
        """Detect if RHOAI v2 is installed.

        RHOAI can not be upgraded in place from v2 to v3, so the aiservice_rhoai
        role removes v2 and installs v3 (the same pipeline task is used as for
        the ODH to RHOAI migration).

        Returns:
            DetectResult: Message describes whether a RHOAI v2 to v3 upgrade is needed.
        """
        self.rhoaiV2Detected = False
        try:
            subscriptionAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
            subscriptions = subscriptionAPI.get(namespace="redhat-ods-operator", name="rhods-operator")
            installedCSV = subscriptions.to_dict().get("status", {}).get("installedCSV", "")
            match = re.match(r"^rhods-operator\.v?(\d+)\.", installedCSV)

            if match and int(match.group(1)) == 2:
                self.setParam("odh_to_rhoai_migration", "true")
                self.rhoaiV2Detected = True
                if not self.tuiMode:
                    self.printDescription(
                        [
                            "<u>Required Migration Notice</u>",
                            "Red Hat OpenShift AI (RHOAI) v2 is currently installed and will be replaced with RHOAI v3",
                            "- An in-place upgrade from RHOAI v2 to v3 is not supported, so RHOAI v2 will be uninstalled and RHOAI v3 installed",
                            "- DSCInitialization and DataScienceCluster will be recreated",
                            "",
                            "<u>Expected Downtime</u>",
                            "- AI Service model serving will be unavailable during the upgrade",
                        ]
                    )
                return DetectResult(ok=True, message=f"RHOAI v2 detected ({installedCSV}) - upgrade to RHOAI v3 will be performed")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="RHOAI v2 is not installed")

    def detectMongoDb(self) -> DetectResult:
        """Detect MongoDB Community and set mongodb_namespace, mongodb_version, mongodb_replicas, and mongodb_action params.

        Stores ``self.mongoCurrentVersion`` and ``self.mongoTargetVersion`` for
        use in ``reviewDependencyUpgrades()`` (CLI) and
        ``_assertUpgradeConfirmations()`` (TUI).

        Returns:
            DetectResult: Message describes the detected MongoDB state.  ok=False
                only when a version downgrade would be required.
        """
        # TODO: Replace this with a lookup to just use whatever is already set up
        # because we should not be changing the scale of the mongodb cluster during
        # and update
        if self.isSNO():
            self.setParam("mongodb_replicas", "1")
        else:
            self.setParam("mongodb_replicas", "3")

        try:
            mongoDbAPI = self.dynamicClient.resources.get(api_version="mongodbcommunity.mongodb.com/v1", kind="MongoDBCommunity")

            if self.getParam("mongodb_namespace") != "":
                logger.debug(f"Looking for MongoDBCommunity instances in {self.getParam('mongodb_namespace')}")
                mongoClusters = mongoDbAPI.get(namespace=self.getParam("mongodb_namespace")).to_dict()["items"]
            else:
                logger.debug("Looking for MongoDBCommunity instances in all namespaces")
                mongoClusters = mongoDbAPI.get().to_dict()["items"]

            logger.debug(f"Found {len(mongoClusters)} MongoDBCommunity instances")
            if len(mongoClusters) == 0:
                return DetectResult(ok=True, message="No MongoDb CE instances found")

            mongoNamespace = mongoClusters[0]["metadata"]["namespace"]
            currentMongoVersion = mongoClusters[0]["status"]["version"]
            targetMongoVersion = self.chosenCatalog["mongo_extras_version_default"]

            self.mongoCurrentVersion = currentMongoVersion
            self.mongoTargetVersion = targetMongoVersion

            self.setParam("mongodb_namespace", mongoNamespace)
            self.setParam("mongodb_version", targetMongoVersion)

            targetMongoVersionMajor = targetMongoVersion.split(".")[0]
            currentMongoVersionMajor = currentMongoVersion.split(".")[0]

            if targetMongoVersionMajor > currentMongoVersionMajor:
                self.setParam("mongodb_action", "install")
                # Let users know that Mongo will be upgraded if existing MongoDb major.minor version
                # is lower than the target major version.  We don't show this message for normal
                # updates, e.g. 5.0.1 to 5.0.2.  Confirmation is handled in
                # reviewDependencyUpgrades() / _assertUpgradeConfirmations().
                return DetectResult(
                    ok=True,
                    message=f"MongoDb CE {currentMongoVersion} needs to be updated to {targetMongoVersion}",
                )
            elif targetMongoVersion < currentMongoVersion:
                return DetectResult(
                    ok=False,
                    message=f"Existing MongoDB Community Edition installation at version {currentMongoVersion} cannot be downgraded to version {targetMongoVersion}",
                )
            else:
                return DetectResult(
                    ok=True,
                    message=f"MongoDb CE is already installed at version {targetMongoVersion}",
                )

        except (ResourceNotFoundError, NotFoundError):
            # There's no MongoDb instance installed in the cluster, so nothing to do
            return DetectResult(ok=True, message="MongoDb CE is not installed")

    def showMongoDependencyUpdateNotice(self, currentMongoVersion: str, targetMongoVersion: str) -> None:
        """Print a highlighted notice about an upcoming MongoDB major-version update.

        Args:
            currentMongoVersion (str): Currently installed version string (or a placeholder such as "(current)").
            targetMongoVersion (str): Target version string from the catalog.
        """
        self.printHighlight(
            [
                "",
                "<u>Dependency Update Notice</u>",
                f"MongoDB Community Edition is currently running version {currentMongoVersion} and will be updated to {targetMongoVersion}",
                "It is recommended that you backup your MongoDB instance before proceeding:",
                "  <u>https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=suite-backing-up-mongodb-maximo-application</u>",
                "",
            ]
        )

    def detectCP4D(self) -> DetectResult:
        """Detect IBM Cloud Pak for Data and set cp4d_update and related params.

        Returns:
            DetectResult: Message describes the detected CP4D state.  ok=False
                when an unsupported upgrade path is detected.
        """
        try:
            cpdAPI = self.dynamicClient.resources.get(api_version="cpd.ibm.com/v1", kind="Ibmcpd")
            cpds = cpdAPI.get().to_dict()["items"]

            if len(cpds) > 1:
                cpdNamespaces = [cpd["metadata"]["namespace"] for cpd in cpds]
                nsStr = ", ".join(cpdNamespaces)
                logger.debug(f"Multiple CP4D instances detected, none will be updated: {nsStr}")
                if not self.tuiMode:
                    self.printDescription(
                        [
                            "<u>Multiple Cloud Pak for Data Instances</u>",
                            "The MAS install, update, and upgrade functions are designed to work together and support the Maximo reference deployment topology.",
                            "Multiple instances of Cloud Pak for Data have been detected on the target cluster, so none will be modified:",
                            "- If you used the Maximo Ansible collection to install CP4D, see: https://ibm-mas.github.io/ansible-devops/",
                            "- If you used the Cloud Pak for Data CLI to install CP4D, see: https://github.com/IBM/cpd-cli",
                        ]
                    )
                return DetectResult(ok=True, message=f"Detected multiple instances of Cloud Pak for Data in the cluster, these will NOT be updated: {nsStr}")

            if len(cpds) == 0:
                return DetectResult(ok=True, message="No IBM Cloud Pak for Data instance found")

            cpdUpgradePath = {
                "5.3.1": "5.4.0",
                "5.2.0": ["5.3.1", "5.4.0"],
                "5.1.3": "5.2.0",
                "5.0.0": "5.1.3",
            }
            cpdInstanceNamespace = cpds[0]["metadata"]["namespace"]
            cpdInstanceVersion = cpds[0]["spec"]["version"]

            if getattr(self, "args", None) and self.args.cpd_product_version:
                cpdTargetVersion = self.getParam("cpd_product_version")
            else:
                cpdTargetVersion = self.chosenCatalog["cpd_product_version_default"]

            if cpdInstanceNamespace != "ibm-cpd":
                logger.debug(f"CP4D instance in {cpdInstanceNamespace} is outside the Maximo reference topology and will NOT be updated")
                if not self.tuiMode:
                    self.printDescription(
                        [
                            "<u>Standalone Cloud Pak for Data</u>",
                            "The MAS install, update, and upgrade functions are designed to work together and support the Maximo reference deployment topology.",
                            "This instance of Cloud Pak for Data appears to have been created outside of this, so will not be modified:",
                            "- If you used the Maximo Ansible collection to install CP4D, see: https://ibm-mas.github.io/ansible-devops/",
                            "- If you used the Cloud Pak for Data CLI to install CP4D, see: https://github.com/IBM/cpd-cli",
                        ]
                    )
                return DetectResult(
                    ok=True,
                    message=f"Standalone Cloud Pak for Data {cpdInstanceVersion} in namespace {cpdInstanceNamespace} will NOT be updated",
                )

            if cpdInstanceVersion == cpdTargetVersion:
                return DetectResult(
                    ok=True, message=f"IBM Cloud Pak for Data ({cpdInstanceNamespace}) is already at the target version {cpdTargetVersion}, no update required"
                )

            if cpdInstanceVersion not in cpdUpgradePath:
                return DetectResult(
                    ok=False,
                    message="Skipping intermediate Cloud Pak for Data updates is not tested and thus not supported\n\nContact IBM support for assistance",
                )

            validNextVersions = cpdUpgradePath[cpdInstanceVersion]
            if isinstance(validNextVersions, str):
                validNextVersions = [validNextVersions]

            if cpdTargetVersion not in validNextVersions:
                return DetectResult(
                    ok=False,
                    message=(
                        f"Skipping intermediate Cloud Pak for Data updates is not tested and thus not supported\n\n"
                        f"Refer to the catalog documentation and first update to any catalog that carries Cloud Pak for data v{validNextVersions[0]}:\n"
                        f"- https://ibm-mas.github.io/cli/catalogs"
                    ),
                )

            if cpdInstanceVersion < cpdTargetVersion:
                # We have to update CP4D
                currentCpdVersionMajorMinor = f"{cpdInstanceVersion.split('.')[0]}.{cpdInstanceVersion.split('.')[1]}"
                targetCpdVersionMajorMinor = f"{cpdTargetVersion.split('.')[0]}.{cpdTargetVersion.split('.')[1]}"
                if not self.tuiMode and currentCpdVersionMajorMinor < targetCpdVersionMajorMinor:
                    # We only show the "backup first" notice for minor CP4D updates
                    self.printHighlight(
                        [
                            "" "<u>Dependency Update Notice</u>",
                            f"Cloud Pak For Data ({cpdInstanceNamespace}) is currently running version {cpdInstanceVersion} and will be updated to version {cpdTargetVersion}",
                            "It is recommended that you backup your Cloud Pak for Data instance before proceeding:",
                            "  <u>https://www.ibm.com/docs/en/cloud-paks/cp-data/5.0.x?topic=administering-backing-up-restoring-cloud-pak-data</u>",
                        ]
                    )

                # Lookup the storage classes already used by CP4D
                # TODO: this should be done by the Ansible role, but isn't
                if "storageClass" in cpds[0]["spec"]:
                    cpdFileStorage = cpds[0]["spec"]["storageClass"]
                elif "fileStorageClass" in cpds[0]["spec"]:
                    cpdFileStorage = cpds[0]["spec"]["fileStorageClass"]
                else:
                    return DetectResult(ok=False, message="Unable to determine the file storage class used in IBM Cloud Pak for Data")

                if "zenCoreMetadbStorageClass" in cpds[0]["spec"]:
                    cpdBlockStorage = cpds[0]["spec"]["zenCoreMetadbStorageClass"]
                elif "blockStorageClass" in cpds[0]["spec"]:
                    cpdBlockStorage = cpds[0]["spec"]["blockStorageClass"]
                else:
                    return DetectResult(ok=False, message="Unable to determine the block storage class used in IBM Cloud Pak for Data")

                # Set the desired storage classes (the same ones already in use)
                self.setParam("storage_class_rwx", cpdFileStorage)
                self.setParam("storage_class_rwo", cpdBlockStorage)

                # Set the desired target version
                self.setParam("cpd_product_version", cpdTargetVersion)
                self.setParam("cp4d_update", "true")
                self.setParam("skip_entitlement_key_flag", "true")

                self.detectCpdService("WS", "ws.cpd.ibm.com/v1beta1", "Watson Studio", "cp4d_update_ws")
                self.detectCpdService("WmlBase", "wml.cpd.ibm.com/v1beta1", "Watson Machine Learning", "cp4d_update_wml")
                self.detectCpdService("AnalyticsEngine", "ae.cpd.ibm.com/v1", "Analytics Engine", "cp4d_update_spark")
                self.detectCpdService("CAService", "ca.cpd.ibm.com/v1", "Cognos Analytics", "cp4d_update_cognos")

                return DetectResult(
                    ok=True,
                    message=f"IBM Cloud Pak for Data ({cpdInstanceNamespace}) {cpdInstanceVersion} needs to be updated to {cpdTargetVersion}",
                )
            else:
                return DetectResult(
                    ok=True,
                    message=f"IBM Cloud Pak for Data ({cpdInstanceNamespace}) is already installed at version {cpdTargetVersion}",
                )

        except (ResourceNotFoundError, NotFoundError):
            return DetectResult(ok=True, message="IBM Cloud Pak for Data is not installed")

    def detectCpdService(self, kind: str, api: str, name: str, param: str) -> None:
        """Detect a CP4D service and set its corresponding update flag param.

        Args:
            kind (str): Kubernetes kind of the CP4D service CR.
            api (str): API version string for the service CR.
            name (str): Human-readable service name (for debug logging).
            param (str): Params key to set to "true" or "false".
        """
        try:
            cpdServiceAPI = self.dynamicClient.resources.get(api_version=api, kind=kind)
            cpdServices = cpdServiceAPI.get().to_dict()["items"]

            if len(cpdServices) > 0:
                logger.debug(f"{name} is included in CP4D update")
                self.setParam(param, "true")
            else:
                logger.debug(f"{name} is not included in CP4D update")
                self.setParam(param, "false")

        except (ResourceNotFoundError, NotFoundError) as e:
            # No action required for this service
            logger.debug(f"{name} is not included in CP4D update: {e}")
            self.setParam(param, "false")

    def detectDb2u(self) -> DetectResult:
        """Detect Db2uCluster/Db2uInstance instances and set db2_namespace, db2_channel, and major-version upgrade params.

        Stores ``self.db2CurrentMajorVersion`` and ``self.db2TargetMajorVersion``
        for use in ``reviewDependencyUpgrades()`` (CLI) and
        ``_assertUpgradeConfirmations()`` (TUI).  The interactive namespace
        selection and upgrade confirmation prompts only run on the CLI path;
        under the TUI a multi-namespace installation or an unconfirmed major
        version upgrade returns ``ok=False`` with guidance to use the
        non-interactive CLI with the relevant arguments.

        Returns:
            DetectResult: Message describes the detected Db2 state.
        """
        apiVersion = "db2u.databases.ibm.com/v1"
        kinds = ["Db2uCluster", "Db2uInstance"]
        paramName = "db2_namespace"
        mode = "db2"
        # Get target Db2u version from catalog
        targetDb2uVersion = self.chosenCatalog["db2_channel_default"]

        try:
            instances = []
            for kind in kinds:
                k8sAPI = self.dynamicClient.resources.get(api_version=apiVersion, kind=kind)
                instances.extend(k8sAPI.get().to_dict()["items"])
                logger.debug(f"Found {len(instances)} {kind} instances on the cluster")

            kindString = "/".join([kind + "s" for kind in kinds])

            if len(instances) == 0:
                return DetectResult(ok=True, message=f"Found no {kindString} ({apiVersion}) instances to update")

            # Set db2_channel immediately after confirming instances exist and target version is available
            if targetDb2uVersion:
                self.setParam("db2_channel", targetDb2uVersion)
                logger.debug(f"Setting db2_channel to {targetDb2uVersion}")

            # If the user provided the namespace using --db2-namespace then we don't have any work to do here
            if self.getParam(paramName) == "":
                namespaces = set()
                for instance in instances:
                    namespaces.add(instance["metadata"]["namespace"])

                if len(namespaces) == 1:
                    # If db2u is only in one namespace, we will update that
                    logger.debug(f"There is only one namespace containing {kindString} so we will target that one: {namespaces}")
                    self.setParam(paramName, list(namespaces)[0])
                elif self.noConfirm:
                    # If db2u is in multiple namespaces and user has disabled prompts then we must error
                    namespaceList = ", ".join(list(namespaces))
                    logger.warning(
                        f"There are multiple namespaces containing {kindString} and user has enable --no-confirm without setting --{mode}-namespace: {namespaceList}"
                    )
                    return DetectResult(
                        ok=False,
                        message=f"{kindString} are installed in multiple namespaces.  You must instruct which one to update using the '--{mode}-namespace' argument",
                    )
                elif self.tuiMode:
                    # The TUI has no namespace selection prompt (yet) — direct the
                    # user to the non-interactive CLI with an explicit namespace.
                    namespaceList = ", ".join(sorted(namespaces))
                    return DetectResult(
                        ok=False,
                        message=(
                            f"{kindString} are installed in multiple namespaces ({namespaceList}).  "
                            f"Re-run with an explicit namespace: mas-cli update --catalog {self.getParam('mas_catalog_version')} --{mode}-namespace <namespace>"
                        ),
                    )
                else:
                    # Otherwise, provide user the list of namespaces we found and ask them to pick one
                    logger.debug(f"There are multiple namespaces containing {kindString}, user must choose: {namespaces}")
                    self.printDescription([f"{kindString}s were found in multiple namespaces, select the namespace to target from the list below:"])
                    for index, ns in enumerate(sorted(namespaces), start=1):
                        self.printDescription([f"{index}. {ns}"])
                    self.promptForListSelect("Select namespace", sorted(namespaces), paramName)

            db2Namespace = self.getParam(paramName)

            # Version comparison logic - check if Db2u needs major version upgrade
            if not targetDb2uVersion:
                logger.warning("Unable to determine target Db2u version from catalog")
                return DetectResult(ok=True, message=f"Db2u instances found in namespace '{db2Namespace}' — channel update will be applied")

            # Extract target major version (first two digits)
            # Handle version formats like "11.5.8.0", "12.0.0.0", "v11.5", "v12.0", "s11.5.9.0-cn6"
            match = re.match(r"^[vs]?(\d{2})[\d.]*", targetDb2uVersion)
            if not match:
                logger.error(f"Unable to parse target Db2u version: {targetDb2uVersion}")
                return DetectResult(ok=True, message=f"Db2u instances found in namespace '{db2Namespace}' — channel update will be applied")

            targetMajorVersion = int(match.group(1))

            # Check all instances to see if any need upgrade
            needsUpgrade = False
            instanceVersions = []

            for instance in instances:
                if not isinstance(instance, dict):
                    continue

                instanceName = instance["metadata"]["name"]
                currentVersion = instance["spec"].get("version", "")

                if not currentVersion:
                    logger.warning(f"No version found for Db2u instance: {instanceName}")
                    continue

                logger.debug(f"Current Db2u version {instanceName}: {currentVersion}")

                # Extract major version from current instance
                currentVersionStr = currentVersion.lstrip("s")
                try:
                    currentMajorVersion = int(currentVersionStr.split(".")[0])
                    instanceVersions.append((instanceName, currentMajorVersion, currentVersion))

                    # Check if this instance needs upgrade
                    if currentMajorVersion < targetMajorVersion:
                        needsUpgrade = True
                        logger.debug(f"Instance {instanceName} needs upgrade: {currentMajorVersion} -> {targetMajorVersion}")
                except (ValueError, IndexError):
                    logger.warning(f"Unable to parse version for Db2u instance: {instanceName}: {currentVersion}")
                    continue

            if not instanceVersions:
                logger.warning("Unable to determine current Db2u version from any instance")
                return DetectResult(ok=True, message=f"Db2u instances found in namespace '{db2Namespace}' — version information unavailable")

            logger.debug(f"Target Db2u version from catalog: {targetDb2uVersion} (major: {targetMajorVersion})")

            # Get the minimum version across all instances for user messaging
            minVersion = min(instanceVersions, key=lambda x: x[1])
            minMajorVersion = minVersion[1]

            self.db2CurrentMajorVersion = minMajorVersion
            self.db2TargetMajorVersion = targetMajorVersion

            # Check if upgrade to version or higher is needed.  Confirmation is
            # handled in reviewDependencyUpgrades() / _assertUpgradeConfirmations().
            if needsUpgrade:
                logger.debug(f"Db2u major version upgrade required: {minMajorVersion} -> {targetMajorVersion}")
                return DetectResult(
                    ok=True,
                    message=f"Db2 {minMajorVersion} needs to be updated to {targetMajorVersion}",
                )
            else:
                self.setParam(f"db2_v{targetMajorVersion}_upgrade", "false")
                logger.debug("No Db2u major version upgrade required")
                return DetectResult(ok=True, message=f"Db2 is already at the target version ({targetMajorVersion})")

        except (ResourceNotFoundError, NotFoundError):
            kindString = ", ".join(kinds)
            logger.debug(f"{'[' + kindString + ']'}.{apiVersion} is not available in the cluster")
            return DetectResult(ok=True, message=f"{kindString}.{apiVersion} is not available in the cluster")

    def detectKafka(self) -> DetectResult:
        """Detect Kafka instances to update and determine the provider.

        The interactive namespace selection prompt only runs on the CLI path;
        under the TUI a multi-namespace installation returns ``ok=False`` with
        guidance to use the non-interactive CLI with ``--kafka-namespace``.

        Returns:
            DetectResult: Message describes the detected Kafka state.  ok=False
                when the Kafka provider cannot be determined.
        """
        apiVersion = "kafka.strimzi.io/v1beta2"
        kind = "Kafka"
        paramName = "kafka_namespace"
        mode = "kafka"

        try:
            k8sAPI = self.dynamicClient.resources.get(api_version=apiVersion, kind=kind)
            instances = k8sAPI.get().to_dict()["items"]
            logger.debug(f"Found {len(instances)} {kind} instances on the cluster")

            if len(instances) > 0:
                # If the user provided the namespace using --kafka-namespace then we don't have any work to do here
                if self.getParam(paramName) == "":
                    namespaces = set()
                    for instance in instances:
                        namespaces.add(instance["metadata"]["namespace"])

                    if len(namespaces) == 1:
                        # If kafka is only in one namespace, we will update that
                        logger.debug(f"There is only one namespace containing {kind}s so we will target that one: {namespaces}")
                        self.setParam(paramName, list(namespaces)[0])
                    elif self.noConfirm:
                        # If kafka is in multiple namespaces and user has disabled prompts then we must error
                        namespaceList = ", ".join(list(namespaces))
                        logger.warning(
                            f"There are multiple namespaces containing {kind}s and user has enable --no-confirm without setting --{mode}-namespace: {namespaceList}"
                        )
                        return DetectResult(
                            ok=False,
                            message=f"{kind}s are installed in multiple namespaces.  You must instruct which one to update using the '--{mode}-namespace' argument",
                        )
                    elif self.tuiMode:
                        # The TUI has no namespace selection prompt (yet) — direct the
                        # user to the non-interactive CLI with an explicit namespace.
                        namespaceList = ", ".join(sorted(namespaces))
                        return DetectResult(
                            ok=False,
                            message=(
                                f"{kind}s are installed in multiple namespaces ({namespaceList}).  "
                                f"Re-run with an explicit namespace: mas-cli update --catalog {self.getParam('mas_catalog_version')} --{mode}-namespace <namespace>"
                            ),
                        )
                    else:
                        # Otherwise, provide user the list of namespaces we found and ask them to pick one
                        logger.debug(f"There are multiple namespaces containing {kind}s, user must choose: {namespaces}")
                        self.printDescription([f"{kind}s were found in multiple namespaces, select the namespace to target from the list below:"])
                        for index, ns in enumerate(sorted(namespaces), start=1):
                            self.printDescription([f"{index}. {ns}"])
                        self.promptForListSelect("Select namespace", sorted(namespaces), paramName)
            else:
                logger.debug(f"Found no instances of {kind}s to update")
                return DetectResult(ok=True, message=f"Found no {kind}s ({apiVersion}) instances to update")
        except (ResourceNotFoundError, NotFoundError):
            logger.debug(f"{kind}.{apiVersion} is not available in the cluster")
            return DetectResult(ok=True, message=f"{kind}.{apiVersion} is not available in the cluster")

        # With Kafka we also have to determine the provider (strimzi or redhat)
        if self.getParam("kafka_namespace") != "" and self.getParam("kafka_provider") == "":
            try:
                subAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
                subs = subAPI.get().to_dict()["items"]

                for sub in subs:
                    if sub["spec"]["name"] == "amq-streams":
                        self.setParam("kafka_provider", "redhat")
                    elif sub["spec"]["name"] == "strimzi-kafka-operator":
                        self.setParam("kafka_provider", "strimzi")
            except (ResourceNotFoundError, NotFoundError):
                pass

            # If the param is still undefined then there is a big problem
            if self.getParam("kafka_provider") == "":
                return DetectResult(ok=False, message="Unable to determine whether the installed Kafka instance is managed by Strimzi or Red Hat AMQ Streams")

        kafkaNamespace = self.getParam(paramName)
        provider = self.getParam("kafka_provider")
        return DetectResult(ok=True, message=f"Apache Kafka ({provider}) instances in namespace '{kafkaNamespace}' will be updated")

    # ------------------------------------------------------------------
    # Dependency-check orchestration
    # ------------------------------------------------------------------

    def runDependencyChecks(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Run all pre-update dependency checks.

        Drives ``_DEPENDENCY_CHECKS`` sequentially.  When ``progressCallback``
        is provided (TUI path) each check calls the detector directly and fires
        the callback with ``(label, result.ok, result.message)``; any failed
        check raises ``RuntimeError`` so the TUI blocks advancement.  When
        ``progressCallback`` is ``None`` (CLI path) each check is wrapped in a
        Halo spinner via ``_runWithHalo``, where a failed check is fatal.

        ``self.chosenCatalog`` must already be set (by ``validateCatalog()`` on
        the CLI path or ``checkCatalog()`` on the TUI path) before this method
        is called.

        Args:
            progressCallback (Callable, optional): Called as ``(label: str, ok: bool, detail: str) -> None`` after each check.
            startCallback (Callable, optional): Called as ``(label: str) -> None`` immediately before each check starts (TUI path only).

        Raises:
            RuntimeError: On the TUI path, when a check fails.
        """
        if progressCallback is not None:
            # TUI path: call detectors, forward DetectResult to callback.
            # Any failure is blocking — this matches the CLI semantics where
            # every failed check is fatal.  Major-version upgrade
            # confirmations are collected by the confirm-upgrades TUI step
            # (see upgradeConfirmationsPending).
            for item in self._DEPENDENCY_CHECKS:
                if startCallback is not None:
                    startCallback(item.label)
                result = getattr(self, item.method)()
                progressCallback(item.label, result.ok, result.message)
                if not result.ok:
                    raise RuntimeError(result.message)

            if startCallback is not None:
                startCallback("Pre-install RBAC evaluation")
            self.evaluatePreinstallRBACAccessForUpdate()
            progressCallback("Pre-install RBAC evaluation", True, "Complete")
        else:
            # CLI path: wrap every check in a Halo spinner via _runWithHalo.
            # Upgrade confirmations (MongoDB major, Db2 major, Db2 license)
            # are deferred to reviewDependencyUpgrades() which runs after
            # this method.
            for item in self._DEPENDENCY_CHECKS:
                self._runWithHalo(item.label, getattr(self, item.method))
            self.evaluatePreinstallRBACAccessForUpdate()

    def mongoUpgradeConfirmationPending(self) -> bool:
        """Return True when a MongoDB major-version upgrade still requires confirmation.

        Returns:
            bool: True when ``mongodb_action`` is "install", a target version is
                known, and the ``mongodb_v{N}_upgrade`` param is not yet "true".
        """
        if self.getParam("mongodb_action") != "install" or not self.mongoTargetVersion:
            return False
        targetMajor = self.mongoTargetVersion.split(".")[0]
        return self.getParam(f"mongodb_v{targetMajor}_upgrade") != "true"

    def db2UpgradeConfirmationPending(self) -> bool:
        """Return True when a Db2 major-version upgrade still requires confirmation.

        Returns:
            bool: True when the detected Db2 major version is below the target
                and the ``db2_v{N}_upgrade`` param is not yet "true".
        """
        if self.db2CurrentMajorVersion is None or self.db2TargetMajorVersion is None:
            return False
        if self.db2CurrentMajorVersion >= self.db2TargetMajorVersion:
            return False
        return self.getParam(f"db2_v{self.db2TargetMajorVersion}_upgrade") != "true"

    def db2LicenseFileNeeded(self) -> bool:
        """Return True when a Db2 v11 to v12 upgrade still needs a license file.

        Returns:
            bool: True when the upgrade is v11 to v12 and no license file has
                been provided via ``--db2-license-file`` or the TUI input.
        """
        if self.db2CurrentMajorVersion != 11 or self.db2TargetMajorVersion != 12:
            return False
        return self.db2LicenseFileLocal is None

    def upgradeConfirmationsPending(self) -> bool:
        """Return True when any interactive upgrade confirmation is still required.

        Drives the ``condition`` of the TUI confirm-upgrades step: the step is
        only shown when a MongoDB or Db2 major-version confirmation (or the
        Db2 v11 to v12 license file) is still needed.

        Returns:
            bool: True when at least one confirmation is pending.
        """
        return self.mongoUpgradeConfirmationPending() or self.db2UpgradeConfirmationPending() or self.db2LicenseFileNeeded()

    def resetWorkflowState(self) -> None:
        """Clear user-collected state so a TUI workflow reset re-collects it.

        Called by the Textual shell on WorkflowReset.  Params are cleared by
        the shell itself and the dependency detectors re-populate the version
        state when the checks re-run, but the Db2 license path is user input
        with no detector: without this method a stale path would silently
        survive a reset (and the license input would not be re-rendered,
        because ``db2LicenseFileNeeded`` only checks for None).
        """
        self.db2LicenseFileLocal = None
        self.db2LicenseFileSecret = None

    def reviewDependencyUpgrades(self) -> None:
        """Prompt for or validate upgrade confirmations for MongoDB and Db2 major-version upgrades.

        Called after ``runDependencyChecks()`` on the CLI path only.  Both the
        interactive and ``--no-confirm`` paths are handled here so the logic
        lives in exactly one place.

        For MongoDB: if a major-version bump is required and not already confirmed
        via ``--mongodb-vN-upgrade``, prompt the user (interactive) or abort
        (``--no-confirm``).

        For Db2: same pattern, plus a Db2 v11→v12 license file prompt/abort.
        """
        # --- MongoDB major version upgrade ---
        mongoAction = self.getParam("mongodb_action")
        mongoNamespace = self.getParam("mongodb_namespace")
        if mongoNamespace and mongoAction == "install" and self.mongoTargetVersion:
            targetMajor = self.mongoTargetVersion.split(".")[0]
            currentDisplay = self.mongoCurrentVersion or "(current)"
            self.showMongoDependencyUpdateNotice(currentDisplay, self.mongoTargetVersion)
            if self.getParam(f"mongodb_v{targetMajor}_upgrade") != "true":
                if self.noConfirm:
                    self.fatalError(
                        f"By choosing {self.getParam('mas_catalog_version')} you must confirm MongoDb update to version {targetMajor} "
                        f"using '--mongodb-v{targetMajor}-upgrade' when using '--no-confirm'"
                    )
                if not self.yesOrNo(f"Confirm update from MongoDb {self.mongoCurrentVersion} to {self.mongoTargetVersion}", f"mongodb_v{targetMajor}_upgrade"):
                    # If the user did not approve the update, abort
                    exit(1)
                print()

        # --- Db2 major version upgrade ---
        if self.db2CurrentMajorVersion is not None and self.db2TargetMajorVersion is not None:
            currentMajor = self.db2CurrentMajorVersion
            targetMajor = self.db2TargetMajorVersion
            if currentMajor < targetMajor:
                if self.getParam(f"db2_v{targetMajor}_upgrade") != "true":
                    if self.noConfirm:
                        self.fatalError(
                            f"By choosing {self.getParam('mas_catalog_version')} you must confirm Db2 update to version {targetMajor} "
                            f"using '--db2-v{targetMajor}-upgrade' when using '--no-confirm'"
                        )
                    if not self.yesOrNo(f"Confirm update from Db2 {currentMajor} to {targetMajor}", f"db2_v{targetMajor}_upgrade"):
                        exit(1)
                    print()

                # Db2 v11 to v12 upgrades require a customer-provided Db2 v12 license file.
                # Enforce this here so the update is blocked before the Tekton pipeline is launched.
                if currentMajor == 11 and targetMajor == 12:
                    if self.db2LicenseFileLocal is None:
                        # In non-interactive mode we must fail fast because there is no safe way to recover.
                        if self.noConfirm:
                            self.fatalError("The Db2 v11 to v12 upgrade cannot proceed without a valid '--db2-license-file' argument when using '--no-confirm'")
                        # In interactive mode, prompt for a valid license file before allowing the upgrade to continue.
                        self.printDescription(
                            [
                                "Db2 v11 to v12 upgrades require a valid Db2 v12 activation license file.",
                                "If you cannot provide a valid file, the update must be aborted.",
                            ]
                        )
                        self.db2LicenseFileLocal = self.promptForFile(
                            "Path to a valid Db2 v12 license file", envVar="DB2_LICENSE_FILE", default="", mustExist=False
                        )

    # ------------------------------------------------------------------
    # Pipeline launch
    # ------------------------------------------------------------------

    def _validateOpenShiftPipelines(self) -> tuple[bool, str]:
        """Validate OpenShift Pipelines installation.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        if installOpenShiftPipelines(self.dynamicClient):
            return True, "OpenShift Pipelines Operator is installed and ready to use"
        return False, "OpenShift Pipelines Operator installation failed"

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
            artifactory_token=self.getParam("artifactory_token"),
            artifactory_username=self.getParam("artifactory_username"),
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
        between the CLI (Halo spinners) and TUI (callbacks) execution paths.
        Both paths share the same stages: Db2 license secret and Tekton
        definitions preparation, OpenShift Pipelines validation, optional
        pre-install RBAC, namespace preparation, Tekton definitions install,
        and PipelineRun submission.

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

        # Db2 license secret and Tekton definitions with digest (shared by
        # both execution paths; no-ops when no license file / no airgap)
        self.db2LicenseFile()
        self.createTektonFileWithDigest()

        pipelinesNamespace = "mas-pipelines"

        # Stage 1: Validate OpenShift Pipelines
        reporter.start("Validate OpenShift Pipelines")
        success, detail = self._validateOpenShiftPipelines()
        if success:
            reporter.success("Validate OpenShift Pipelines", detail)
        else:
            reporter.failure("Validate OpenShift Pipelines", detail)
            self.fatalError("Installation failed")

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

                label = f"Apply pre-install RBAC for instance: {instanceId} ({targetVersion}, mode: {adminMode})"
                reporter.start(label)

                selectedApps = getInstalledApps(self.dynamicClient, instanceId)
                applyPreInstallMASRBAC(
                    dynClient=self.dynamicClient,
                    masVersion=".".join(targetVersion.split(".")[:2]),
                    masInstanceId=instanceId,
                    adminMode=adminMode,
                    selectedApps=selectedApps,
                )
                reporter.success(label, f"Pre-install RBAC applied for {instanceId} ({targetVersion}, mode: {adminMode})")

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
        reporter.success("Install Tekton definitions", f"Latest Tekton definitions are installed ({detail})")

        # Stage 5: Submit PipelineRun
        reporter.start("Submit PipelineRun")
        success, detail = self._submitPipelineRun()
        if success:
            # ``detail`` is the pipeline run URL: the CLI success line ends
            # with it, and the TUI renders it beneath the step list (where
            # the Copy URL button gets it from).  Reporting a static message
            # here would leave the TUI copying that message as the "URL".
            reporter.success("Submit PipelineRun", detail)
        else:
            reporter.failure("Submit PipelineRun", "Failed to submit PipelineRun for MAS update, see log file for details")
            if progressCallback is None:
                print()
