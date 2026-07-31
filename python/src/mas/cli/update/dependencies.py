# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Dependency detection mixin for the update command.

Provides ``DetectResult``, ``CheckItem``, ``DependencyDetectionMixin``, and the
``_DEPENDENCY_CHECKS`` registry that drives both the CLI spinner path and
the TUI progress-callback path.

Each ``detectXxx()`` method returns a ``DetectResult(ok, message)`` that carries:
- ``ok``      — whether the result is a success/informational state (True) or a
                blocking failure (False).
- ``message`` — the specific human-readable status string shown in the Halo
                spinner (CLI) and the TUI progress log.

No ``RuntimeError`` is raised from detectors; failures are expressed as
``DetectResult(ok=False, message=…)``.

Upgrade confirmations that require user interaction (MongoDB/Db2 major-version
bumps) are handled separately in ``reviewDependencyUpgrades()``.
"""

import logging
import re
from dataclasses import dataclass
from typing import Callable, Optional

from halo import Halo
from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

logger = logging.getLogger(__name__)


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
        method (str): Name of the ``UpdateApp`` method to call.
        param (str): Unused — kept for backwards-compatible ``_DEPENDENCY_CHECKS``
            entries.  May be removed in a future refactor.
        fatal_if_present (bool): When True a ``DetectResult(ok=False, …)`` causes
            the check loop to raise ``RuntimeError`` and abort the update.
            Defaults to False.
        present_message (str): Unused legacy field.  Defaults to empty string.
        absent_message (str): Unused legacy field.  Defaults to "No action required".
    """

    label: str
    method: str
    param: str
    fatal_if_present: bool = False
    present_message: str = ""
    absent_message: str = "No action required"


class DependencyDetectionMixin:
    """Mixin providing third-party workload detection for UpdateApp.

    Attributes:
        _DEPENDENCY_CHECKS: Ordered registry of checks driven by
            ``runDependencyChecks()``.  Fatal-if-present checks must appear
            before all non-fatal checks.
    """

    _DEPENDENCY_CHECKS = [
        CheckItem("IBM Watson Discovery", "isWatsonDiscoveryInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
        CheckItem("IBM Watson Openscale", "isWatsonOpenscaleInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
        CheckItem("IBM Certificate-Manager", "isIBMCertManagerInstalled", "", fatal_if_present=True, present_message="Installed — update cannot proceed"),
        CheckItem("Grafana Operator v4", "detectGrafana4", "grafana_v5_upgrade", present_message="Migrate to v5"),
        CheckItem("Open Data Hub (ODH)", "detectODH", "odh_to_rhoai_migration", present_message="Migrate to RHOAI"),
        CheckItem("MongoDB Community", "detectMongoDb", "mongodb_namespace", present_message="Found"),
        CheckItem("IBM Db2", "detectDb2u", "db2_namespace", present_message="Found"),
        CheckItem("Apache Kafka", "detectKafka", "kafka_namespace", present_message="Found"),
        CheckItem("IBM Cloud Pak for Data", "detectCP4D", "cp4d_update", present_message="Platform and services in ibm-cpd"),
    ]

    # ------------------------------------------------------------------
    # Fatal pre-condition checks
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
                return DetectResult(ok=False, message="IBM Watson Discovery is installed — update cannot proceed")
        except (ResourceNotFoundError, NotFoundError):
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
                return DetectResult(ok=False, message="IBM Watson OpenScale is installed — update cannot proceed")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="IBM Watson OpenScale is not installed")

    def isIBMCertManagerInstalled(self) -> DetectResult:
        """Check whether the legacy IBM Certificate Manager is installed.

        Returns:
            DetectResult: ok=False with blocking message if found; ok=True otherwise.
        """
        try:
            namespaceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
            namespaceAPI.get(name="ibm-common-services")
            podsAPI = self.dynamicClient.resources.get(api_version="v1", kind="Pod")
            podsList = podsAPI.get(namespace="ibm-common-services")
            for pod in podsList.items:
                if pod is not None and "cert-manager-cainjector" in pod.metadata.name:
                    logger.debug("Found IBM Certificate-Manager in ibm-common-services namespace")
                    return DetectResult(ok=False, message="IBM Certificate-Manager is installed — update cannot proceed")
            logger.debug("ibm-common-services namespace exists but IBM Certificate-Manager was not found")
        except NotFoundError:
            logger.debug("There is no ibm-common-services namespace")
        return DetectResult(ok=True, message="IBM Certificate-Manager is not installed")

    # ------------------------------------------------------------------
    # CLI spinner helper
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Dependency detectors
    # ------------------------------------------------------------------

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
                return DetectResult(ok=True, message="Grafana Operator v4 detected — will be migrated to v5")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="Grafana Operator v4 is not installed")

    def detectODH(self) -> DetectResult:
        """Detect ODH installation and set odh_to_rhoai_migration param.

        This is a simplified check — the Ansible role will perform detailed validation.

        Returns:
            DetectResult: Message describes whether RHOAI migration is needed.
        """
        try:
            subscriptionAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="Subscription")
            subscriptions = subscriptionAPI.get(namespace="openshift-operators").to_dict()["items"]
            odh_installed = any(sub.get("spec", {}).get("name") == "opendatahub-operator" for sub in subscriptions)
            if odh_installed:
                self.setParam("odh_to_rhoai_migration", "true")
                return DetectResult(ok=True, message="Open Data Hub detected — will be migrated to RHOAI")
        except (ResourceNotFoundError, NotFoundError):
            pass
        return DetectResult(ok=True, message="Open Data Hub (ODH) is not installed")

    def detectMongoDb(self) -> DetectResult:
        """Detect MongoDB Community and set mongodb_namespace, mongodb_version, mongodb_replicas, and mongodb_action params.

        Stores ``self.mongoCurrentVersion`` and ``self.mongoTargetVersion`` for
        use in ``reviewDependencyUpgrades()``.

        Returns:
            DetectResult: Message describes the detected MongoDB state.  ok=False
                only when a version downgrade would be required.
        """
        # TODO: Replace replicas lookup with the value already configured on the cluster
        # rather than recalculating during an update.
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
                return DetectResult(ok=True, message="MongoDB Community Edition is not installed")

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
                return DetectResult(
                    ok=True,
                    message=f"MongoDB Community Edition {currentMongoVersion} will be updated to {targetMongoVersion}",
                )
            elif targetMongoVersion < currentMongoVersion:
                return DetectResult(
                    ok=False,
                    message=f"MongoDB Community Edition {currentMongoVersion} cannot be downgraded to {targetMongoVersion}",
                )
            else:
                return DetectResult(
                    ok=True,
                    message=f"MongoDB Community Edition is already at the target version ({targetMongoVersion})",
                )

        except (ResourceNotFoundError, NotFoundError):
            return DetectResult(ok=True, message="MongoDB Community Edition is not installed")

    def showMongoDependencyUpdateNotice(self, currentMongoVersion: str, targetMongoVersion: str) -> None:
        """Print a highlighted notice about an upcoming MongoDB major-version update.

        Args:
            currentMongoVersion (str): Currently installed version string
                (or a placeholder such as "(current)").
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
                return DetectResult(ok=True, message=f"Multiple CP4D instances detected ({nsStr}) — none will be updated")

            if len(cpds) == 0:
                return DetectResult(ok=True, message="IBM Cloud Pak for Data is not installed")

            cpdUpgradePath = {"5.2.0": "5.2.0", "5.1.3": "5.2.0", "5.0.0": "5.1.3"}
            cpdInstanceNamespace = cpds[0]["metadata"]["namespace"]
            cpdInstanceVersion = cpds[0]["spec"]["version"]

            if self.args.cpd_product_version:
                cpdTargetVersion = self.getParam("cpd_product_version")
            else:
                cpdTargetVersion = self.chosenCatalog["cpd_product_version_default"]

            if cpdInstanceNamespace != "ibm-cpd":
                logger.debug(f"CP4D instance in {cpdInstanceNamespace} is outside the Maximo reference topology and will NOT be updated")
                return DetectResult(
                    ok=True,
                    message=f"IBM Cloud Pak for Data {cpdInstanceVersion} in {cpdInstanceNamespace} is not managed by MAS — no action required",
                )

            if cpdInstanceVersion not in cpdUpgradePath:
                return DetectResult(
                    ok=False,
                    message="Skipping intermediate Cloud Pak for Data updates is not supported. Contact IBM support for assistance.",
                )
            if cpdUpgradePath[cpdInstanceVersion] != cpdTargetVersion:
                return DetectResult(
                    ok=False,
                    message=(
                        f"Skipping intermediate Cloud Pak for Data updates is not supported. "
                        f"First update to any catalog that carries CP4D v{cpdUpgradePath[cpdInstanceVersion]}. "
                        "See https://ibm-mas.github.io/cli/catalogs"
                    ),
                )

            if cpdInstanceVersion < cpdTargetVersion:
                if "storageClass" in cpds[0]["spec"]:
                    cpdFileStorage = cpds[0]["spec"]["storageClass"]
                elif "fileStorageClass" in cpds[0]["spec"]:
                    cpdFileStorage = cpds[0]["spec"]["fileStorageClass"]
                else:
                    return DetectResult(ok=False, message="Unable to determine the file storage class used by IBM Cloud Pak for Data")

                if "zenCoreMetadbStorageClass" in cpds[0]["spec"]:
                    cpdBlockStorage = cpds[0]["spec"]["zenCoreMetadbStorageClass"]
                elif "blockStorageClass" in cpds[0]["spec"]:
                    cpdBlockStorage = cpds[0]["spec"]["blockStorageClass"]
                else:
                    return DetectResult(ok=False, message="Unable to determine the block storage class used by IBM Cloud Pak for Data")

                self.setParam("storage_class_rwx", cpdFileStorage)
                self.setParam("storage_class_rwo", cpdBlockStorage)
                self.setParam("cpd_product_version", cpdTargetVersion)
                self.setParam("cp4d_update", "true")
                self.setParam("skip_entitlement_key_flag", "true")

                self.detectCpdService("WS", "ws.cpd.ibm.com/v1beta1", "Watson Studio", "cp4d_update_ws")
                self.detectCpdService("WmlBase", "wml.cpd.ibm.com/v1beta1", "Watson Machine Learning", "cp4d_update_wml")
                self.detectCpdService("AnalyticsEngine", "ae.cpd.ibm.com/v1", "Analytics Engine", "cp4d_update_spark")
                self.detectCpdService("CAService", "ca.cpd.ibm.com/v1", "Cognos Analytics", "cp4d_update_cognos")

                return DetectResult(
                    ok=True,
                    message=f"IBM Cloud Pak for Data {cpdInstanceVersion} will be updated to {cpdTargetVersion}",
                )
            else:
                return DetectResult(
                    ok=True,
                    message=f"IBM Cloud Pak for Data is already at the target version ({cpdTargetVersion})",
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
            logger.debug(f"{name} is not included in CP4D update: {e}")
            self.setParam(param, "false")

    def detectDb2u(self) -> DetectResult:
        """Detect Db2uCluster/Db2uInstance instances and set db2_namespace, db2_channel, and major-version upgrade flag params.

        Stores ``self.db2CurrentMajorVersion`` and ``self.db2TargetMajorVersion``
        for use in ``reviewDependencyUpgrades()``.  Returns ok=False when
        ``--no-confirm`` is set and instances are in multiple namespaces without
        an explicit ``--db2-namespace`` argument.

        Returns:
            DetectResult: Message describes the detected Db2 state.
        """
        apiVersion = "db2u.databases.ibm.com/v1"
        kinds = ["Db2uCluster", "Db2uInstance"]
        paramName = "db2_namespace"
        targetDb2uVersion = self.chosenCatalog["db2_channel_default"]

        try:
            instances = []
            for kind in kinds:
                k8sAPI = self.dynamicClient.resources.get(api_version=apiVersion, kind=kind)
                instances.extend(k8sAPI.get().to_dict()["items"])
                logger.debug(f"Found {len(instances)} {kind} instances on the cluster")

            if len(instances) == 0:
                return DetectResult(ok=True, message="No Db2uCluster or Db2uInstance instances found")

            kindString = "/".join([k + "s" for k in kinds])
            if targetDb2uVersion:
                self.setParam("db2_channel", targetDb2uVersion)

            if self.getParam(paramName) == "":
                namespaces = set(instance["metadata"]["namespace"] for instance in instances)
                if len(namespaces) == 1:
                    self.setParam(paramName, list(namespaces)[0])
                elif len(namespaces) > 1:
                    if self.noConfirm:
                        return DetectResult(
                            ok=False,
                            message=(
                                f"{kindString} are installed in multiple namespaces. "
                                "You must instruct which one to update using the '--db2-namespace' argument"
                            ),
                        )
                    # Interactive path: prompt handled in reviewDependencyUpgrades()
                    self.setParam(paramName, sorted(namespaces)[0])

            db2Namespace = self.getParam(paramName)

            # Major version upgrade detection
            if not targetDb2uVersion:
                return DetectResult(ok=True, message=f"Db2u instances found in {db2Namespace} — channel update will be applied")

            match = re.match(r"^[vs]?(\d{2})[\d.]*", targetDb2uVersion)
            if not match:
                return DetectResult(ok=True, message=f"Db2u instances found in {db2Namespace} — channel update will be applied")

            targetMajorVersion = int(match.group(1))
            needsUpgrade = False
            instanceVersions = []
            for instance in instances:
                if not isinstance(instance, dict):
                    continue
                currentVersion = instance["spec"].get("version", "")
                if not currentVersion:
                    continue
                try:
                    currentMajorVersion = int(currentVersion.lstrip("s").split(".")[0])
                    instanceVersions.append((instance["metadata"]["name"], currentMajorVersion, currentVersion))
                    if currentMajorVersion < targetMajorVersion:
                        needsUpgrade = True
                except (ValueError, IndexError):
                    continue

            if not instanceVersions:
                return DetectResult(ok=True, message=f"Db2u instances found in {db2Namespace} — version information unavailable")

            minVersion = min(instanceVersions, key=lambda x: x[1])
            self.db2CurrentMajorVersion = minVersion[1]
            self.db2TargetMajorVersion = targetMajorVersion

            if needsUpgrade:
                return DetectResult(
                    ok=True,
                    message=f"Db2u {minVersion[1]} instances in {db2Namespace} will be updated to {targetMajorVersion}",
                )
            else:
                self.setParam(f"db2_v{targetMajorVersion}_upgrade", "false")
                return DetectResult(
                    ok=True,
                    message=f"Db2u instances in {db2Namespace} are already at the target version ({targetMajorVersion})",
                )

        except (ResourceNotFoundError, NotFoundError):
            return DetectResult(ok=True, message="Db2u is not installed on this cluster")

    def detectKafka(self) -> DetectResult:
        """Detect Kafka instances and set kafka_namespace and kafka_provider params.

        When instances span multiple namespaces the first sorted namespace is used.

        Returns:
            DetectResult: Message describes the detected Kafka state.  ok=False
                when the Kafka provider cannot be determined.
        """
        apiVersion = "kafka.strimzi.io/v1beta2"
        kind = "Kafka"
        paramName = "kafka_namespace"

        try:
            k8sAPI = self.dynamicClient.resources.get(api_version=apiVersion, kind=kind)
            instances = k8sAPI.get().to_dict()["items"]
            logger.debug(f"Found {len(instances)} {kind} instances on the cluster")

            if len(instances) > 0 and self.getParam(paramName) == "":
                namespaces = set(instance["metadata"]["namespace"] for instance in instances)
                if len(namespaces) == 1:
                    self.setParam(paramName, list(namespaces)[0])
                elif len(namespaces) > 1:
                    self.setParam(paramName, sorted(namespaces)[0])
        except (ResourceNotFoundError, NotFoundError):
            return DetectResult(ok=True, message="Apache Kafka is not installed on this cluster")

        kafkaNamespace = self.getParam(paramName)
        if not kafkaNamespace:
            return DetectResult(ok=True, message="No Apache Kafka instances found")

        if self.getParam("kafka_provider") == "":
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

            if self.getParam("kafka_provider") == "":
                return DetectResult(
                    ok=False,
                    message="Unable to determine whether Kafka is managed by Strimzi or Red Hat AMQ Streams",
                )

        provider = self.getParam("kafka_provider")
        return DetectResult(ok=True, message=f"Apache Kafka ({provider}) instances in {kafkaNamespace} will be updated")

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def runDependencyChecks(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Run all pre-update dependency checks.

        Drives ``_DEPENDENCY_CHECKS`` sequentially.  When ``progressCallback``
        is provided (TUI path) each check calls the detector directly and fires
        the callback with ``(label, result.ok, result.message)``.
        When ``progressCallback`` is ``None`` (CLI path) each check is wrapped in
        a Halo spinner via ``_runWithHalo``.  All upgrade confirmations are deferred
        to ``reviewDependencyUpgrades()``.

        ``self.chosenCatalog`` must already be set by ``checkCatalog()`` before
        this method is called.

        Args:
            progressCallback (Callable, optional): Called as
                ``(label: str, ok: bool, detail: str) -> None`` after each check.
                Must be safe to call from any thread.  Defaults to None.
            startCallback (Callable, optional): Called as ``(label: str) -> None``
                immediately before each check starts (TUI path only).  Allows the
                UI to mark the step as in-progress before the work runs.
                Defaults to None.

        Raises:
            RuntimeError: When a fatal-if-present check returns ok=False.
        """
        if progressCallback is not None:
            # TUI path: call detectors, forward DetectResult to callback
            for item in self._DEPENDENCY_CHECKS:
                if startCallback is not None:
                    startCallback(item.label)
                method = getattr(self, item.method)
                result = method()
                progressCallback(item.label, result.ok, result.message)
                if item.fatal_if_present and not result.ok:
                    raise RuntimeError(result.message)
            if startCallback is not None:
                startCallback("Pre-install RBAC evaluation")
            self.evaluatePreinstallRBACAccessForUpdate()
            progressCallback("Pre-install RBAC evaluation", True, "Complete")
        else:
            # CLI path: wrap every check in a Halo spinner via _runWithHalo.
            # Upgrade confirmations (MongoDB major, Db2 major, Db2 license) are
            # deferred to reviewDependencyUpgrades() which runs after this method.
            for item in self._DEPENDENCY_CHECKS:
                self._runWithHalo(item.label, getattr(self, item.method))
            self.evaluatePreinstallRBACAccessForUpdate()

    def reviewDependencyUpgrades(self) -> None:
        """Prompt for or validate upgrade confirmations for MongoDB and Db2 major-version upgrades.

        Called after ``runDependencyChecks()`` on the CLI path only.  Both the
        interactive and ``--no-confirm`` paths are handled here so the logic lives
        in exactly one place.

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
            if self.getParam(f"mongodb_v{targetMajor}_upgrade") != "true":
                self.showMongoDependencyUpdateNotice(currentDisplay, self.mongoTargetVersion)
                if self.noConfirm:
                    self.fatalError(
                        f"By choosing {self.getParam('mas_catalog_version')} you must confirm MongoDB update to version {targetMajor} "
                        f"using '--mongodb-v{targetMajor}-upgrade' when using '--no-confirm'"
                    )
                if not self.yesOrNo(f"Confirm update to MongoDB {self.mongoTargetVersion}", f"mongodb_v{targetMajor}_upgrade"):
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

                if currentMajor == 11 and targetMajor == 12:
                    if self.db2LicenseFileLocal is None:
                        if self.noConfirm:
                            self.fatalError("The Db2 v11 to v12 upgrade cannot proceed without a valid '--db2-license-file' argument when using '--no-confirm'")
                        self.printDescription(
                            [
                                "Db2 v11 to v12 upgrades require a valid Db2 v12 activation license file.",
                                "If you cannot provide a valid file, the update must be aborted.",
                            ]
                        )
                        self.db2LicenseFileLocal = self.promptForFile(
                            "Path to a valid Db2 v12 license file", envVar="DB2_LICENSE_FILE", default="", mustExist=False
                        )
