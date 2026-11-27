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

import base64
import json
import sys
import logging
import logging.handlers
from typing import Callable, Optional
from prompt_toolkit import prompt, print_formatted_text, HTML

from kubernetes.dynamic.exceptions import NotFoundError, ResourceNotFoundError

from ..cli import BaseApp
from ..common.olmApprovals import OlmApprovalDetectionMixin, resolveOlmApprovalTimeout
from ..common.storageClasses import StorageClassMixin
from ..validators import StorageClassValidator
from .argBuilder import upgradeArgBuilderMixin
from .argParser import upgradeArgParser
from .settings import UpgradeSettingsMixin

from mas.devops.ocp import createNamespace, getStorageClasses, getStorageClass
from mas.devops.mas import (
    listMasInstances,
    getMasChannel,
    getAppsSubscriptionChannel,
    getDefaultStorageClasses,
    getWorkspaceId,
    verifyAppInstance,
    getPermissionMode,
    getInstalledApps,
)
from mas.devops.utils import isVersionEqualOrAfter
from mas.devops.tekton import (
    preparePipelinesNamespace,
    installOpenShiftPipelines,
    updateTektonDefinitions,
    launchUpgradePipeline,
    lookupPipelineStorageClass,
    prepareUpgradeSecrets,
)
from mas.devops.pre_install import applyPreInstallMASRBAC
from ..rbac_utils import evaluatePreinstallRBACAccess

logger = logging.getLogger(__name__)


class NoUpgradeRequiredError(RuntimeError):
    """The instance is already fully upgraded: there is nothing to submit.

    A distinct subclass of RuntimeError so the two paths can treat it differently while sharing one resolver: the non-interactive path exits cleanly with the message,
    and the TUI displays it on the step like any other validation outcome (today's behavior on both paths).
    """


class UpgradeApp(BaseApp, upgradeArgBuilderMixin, UpgradeSettingsMixin, OlmApprovalDetectionMixin, StorageClassMixin):
    """Orchestrator for the ``mas-cli upgrade`` command.

    Two execution paths share this class, and both end in the same ``launchUpgrade()``:

    - **Interactive (the TUI)**: the mas-cli dispatch launches the Textual workflow (``upgrade/workflow.py``) whenever ``--mas-instance-id`` is absent -- including invocations
      carrying optional flags, which ``serveTuiMode`` applies to the app first via ``applyCliArgs`` so a guided run carries them into the PipelineRun exactly as a fully-specified
      command line would. The workflow drives this class through ``fetchInstalledInstanceIds`` (the connect step), ``prepareUpgrade`` /
      ``prepareUpgradeForInstanceSelection`` (instance selection and target-channel validation), ``licenseAcceptancePending`` / ``manageFoundationPending`` /
      ``prepareManageFoundation`` (the conditional license and Manage Foundation steps) and ``launchUpgrade`` (the launch screen).
    - **Non-interactive**: ``mas upgrade --mas-instance-id ...`` runs ``upgrade()``, which requires the command line to carry the parameters the wizard exists to choose
      (``--mas-instance-id`` above all) and prompts for nothing beyond the license acceptance and the final review confirmation.

    The sections below follow that structure: the shared command-line mapping first, then the non-interactive path, the TUI step validators, and the validation / storage /
    launch logic both paths call.
    """

    def __init__(self) -> None:
        """Initialise UpgradeApp with safe defaults for all instance variables.

        All attributes read by the TUI execution path (which constructs
        ``UpgradeApp()`` directly without calling ``upgrade()``) are set here.
        The ``upgrade()`` method overwrites these as needed.
        """
        super().__init__()
        self.noConfirm: bool = False
        self.skipPreCheck: bool = False
        self.licenseAccepted: bool = False
        self.devMode: bool = False
        self.masInstanceId: Optional[str] = None
        # Channel state populated by prepareUpgrade() on the TUI path (and
        # inline in upgrade() on the CLI path)
        self.nextChannel: str = ""
        self.currentChannel: str = ""
        self.effectiveCurrentChannel: str = ""
        # The target auto-derived by prepareUpgrade() (before any explicit
        # choice on the target-channel step): the default selection for that
        # step's field
        self.autoNextChannel: str = ""
        # RBAC state populated by prepareUpgrade() / upgrade() and consumed
        # by launchUpgrade() / the launch section of upgrade()
        self.applyPreInstallMASRBAC: bool = False
        self.selectedAppsForRBAC: list = []
        self.detectedMode: Optional[str] = None
        # Manage Foundation state: isManageFoundation is set by prepareUpgrade()
        # when the 9.0.x -> 9.1.x upgrade needs to install Manage; the
        # install flags and app name are set by prepareManageFoundation()
        # (and inline in upgrade()) for configDb2 to read
        self.isManageFoundation: bool = False
        self.installIoT: bool = False
        self.installMonitor: bool = False
        self.installFacilities: bool = False
        self.installManage: bool = False
        self.manageAppName: Optional[str] = None
        self.showAdvancedOptions: bool = False
        # Pipeline storage class resolved by configPipelineStorageClass()
        self.pipelineStorageClass: Optional[str] = None
        self.pipelineStorageAccessMode: Optional[str] = None
        # Aggregate OLM install plan approval mode detected over the upgrade
        # scope (the mas-{instance_id}-* namespaces)
        self.olmApprovalStatus: Optional[dict] = None

    # ------------------------------------------------------------------
    # Command-line argument mapping (shared by both paths)
    # ------------------------------------------------------------------
    def applyCliArgs(self, args) -> None:
        """
        Apply parsed command-line arguments to the app state.

        The arg-to-state mapping shared by both execution paths: the non-interactive preamble in ``upgrade()`` and the TUI bootstrap in ``serveTuiMode``, which routes optional flags (image pull policy, storage classes, OLM approval timeout, ...) into the guided workflow. Only pure state mapping lives here -- cluster interaction and prompts stay with the callers.
        """
        self.noConfirm = args.no_confirm
        self.skipPreCheck = args.skip_pre_check
        self.licenseAccepted = args.accept_license
        self.nextChannel = args.next_channel
        self.devMode = args.dev_mode
        self.applyPreInstallMASRBAC = False
        self.selectedAppsForRBAC = []

        # Pre-populate pipeline storage class from CLI args so configPipelineStorageClass
        self.pipelineStorageClass = args.storage_pipeline or None
        self.pipelineStorageAccessMode = args.storage_accessmode or None

        # Pre-populate RWO/RWX storage classes from CLI args (used for Manage Foundation Db2 instances)
        if args.storage_class_rwo:
            self.params["storage_class_rwo"] = args.storage_class_rwo
        if args.storage_class_rwx:
            self.params["storage_class_rwx"] = args.storage_class_rwx

        # Set image_pull_policy if provided
        if args.image_pull_policy and args.image_pull_policy != "":
            self.setParam("image_pull_policy", args.image_pull_policy)

        # Skip pre-check flag: only rendered into the PipelineRun when set —
        # the pipeline's own default (empty) runs the pre-checks
        if args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        # OLM approval timeout: flag > OLM_APPROVAL_TIMEOUT environment
        # variable > omitted (the collection's 7200s default then applies).
        # The approval mode itself is not a flag on upgrade: it is a property
        # of the cluster, detected over the instance's namespaces by
        # detectOLMApprovalMode()
        try:
            olmApprovalTimeout = resolveOlmApprovalTimeout(args.olm_approval_timeout)
        except ValueError as e:
            self.fatalError(f"Error: {e}")
        if olmApprovalTimeout is not None:
            self.setParam("olm_approval_timeout", str(olmApprovalTimeout))

    # ------------------------------------------------------------------
    # Non-interactive path
    # ------------------------------------------------------------------
    def upgrade(self, argv):
        """
        Non-interactive MAS instance upgrade.

        This is the non-interactive path: it runs when the required parameters are provided on the command line, of which ``--mas-instance-id`` is the one the guided workflow exists to choose. The interactive mode is the Textual TUI, launched by the mas-cli dispatch whenever that parameter is absent (with any optional flags passed through to it) -- nothing finds its way through this method by prompts other than the license acceptance and the final review confirmation.
        """
        args = upgradeArgParser.parse_args(args=argv)
        instanceId = args.mas_instance_id
        if instanceId is None:
            self.fatalError("--mas-instance-id is required on the non-interactive path; run 'mas upgrade' with no arguments for the guided workflow")

        self.applyCliArgs(args)

        # Non-interactive mode assumes the target cluster is already the
        # active Kubernetes context. Look up the target architecture because
        # configDb2 will try to access self.architecture
        self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: Not successfully connected to a Kubernetes cluster.  See log file for details</Red>"))
            sys.exit(1)

        # The instance ID is a PipelineRun param: write it into params as
        # soon as it is resolved (the TUI path does the same via the
        # instance-selection step field, which prepareUpgrade reads back)
        self.setParam("mas_instance_id", instanceId)

        # Resolve the upgrade path (shared with the TUI's prepareUpgrade):
        # an explicit --next-channel is a complete override of the derived
        # target, and dev mode carries an informative target with app
        # compatibility validation deliberately skipped (core-upgrade uses
        # its own compatibility matrix, so nextChannel is only informative
        # for the core upgrade)
        if self.devMode and self.nextChannel == "":
            self.fatalError("--next-channel is required with --dev-mode on the non-interactive path (the guided workflow prompts for it)")

        explicitTarget = self.nextChannel if self.nextChannel != "" else None
        try:
            self._resolveUpgradePath(instanceId, explicitTarget=explicitTarget, validateCompatibility=not self.devMode)
        except NoUpgradeRequiredError as e:
            # The instance is already fully upgraded: exit cleanly (the TUI
            # surfaces the same condition as an error on its step)
            print_formatted_text(HTML(f"<LightSlateGrey>{e}</LightSlateGrey>"))
            return
        except RuntimeError as e:
            self.fatalError(str(e))

        if explicitTarget is not None and self.nextChannel == self.currentChannel:
            # Retry scenario: MAS core already on the target channel —
            # re-run the upgrade to complete any unfinished components
            # (the pipeline is idempotent, so this is safe even when
            # everything is already on the target channel)
            print_formatted_text(
                HTML(
                    f"<LightSlateGrey>Next Channel {self.nextChannel} equals Current MAS Core Channel {self.currentChannel}. "
                    f"Re-running the {self.nextChannel} upgrade — apps or the Manage Foundation install may still need to be completed.</LightSlateGrey>"
                )
            )

        # The mas_channel PipelineRun param is the upgrade's target channel:
        # write it into params here, where the channel state is final — the
        # launch path must make no channel decisions of its own
        self.resolveMasChannelParam()

        if not self.licenseAccepted and not self.devMode:
            self.printH1("License Terms")
            self.printDescription(["To continue with the upgrade, you must accept the license terms:", self.licenses[self.nextChannel]])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

        # The only scenario where Manage Foundation needs to be installed during an upgrade is from 9.0.x to 9.1.x (if Manage was not already installed in 9.0.x).
        self.setParam("should_install_manage_foundation", "false")
        if self.nextChannel.startswith("9.1") and not verifyAppInstance(self.dynamicClient, instanceId, "manage"):
            self.isManageFoundation = True
            self.printDescription(
                ["Manage foundation installs the following capabilities: User, Security groups, Application configurator and Mobile configurator."]
            )

            if self.devMode:
                # The guided workflow collects Artifactory credentials in dev
                # mode; the upgrade argument parser deliberately has no flags
                # for them, so this combination cannot be run non-interactively
                self.fatalError(
                    "Dev mode with a Manage Foundation install requires the guided workflow for Artifactory credentials; run 'mas upgrade' with no arguments"
                )

            # Entitlement key, install flags, pipeline params and the Db2
            # configuration (shared with the TUI's manage-foundation step)
            self._configureManageFoundation(instanceId)

        # Compute Monitor install order for upgrade
        self.computeMonitorInstallOrderForUpgrade(instanceId)

        # Validate Kafka requirements for Civil component during upgrade
        self.validateKafkaForCivilUpgrade(instanceId)

        # Block upgrade if Suite CR has a stale routingMode=path from a pre-9.2 install
        self.checkRoutingModeForUpgrade(instanceId, self.currentChannel)

        # Admin-mode detection and RBAC evaluation (shared with the TUI's
        # prepareUpgrade); launchUpgrade's RBAC stage reads self.detectedMode
        self._detectAdminModeAndEvaluateRBAC(instanceId, self.currentChannel)

        self.configPipelineStorageClass(instanceId)

        # Detect the aggregate OLM install plan approval mode over the
        # instance's namespaces (the upgrade's blast radius) and pass the
        # effective mode to the PipelineRun so the approval gates behave
        # consistently with the cluster
        self.detectOLMApprovalMode(namespacePrefix=f"mas-{instanceId}-")

        # Show the equivalent non-interactive command before the review screen
        self.masInstanceId = instanceId
        nonInteractiveCommand = self.buildCommand()
        self.printH1("Non-Interactive Upgrade Command")
        self.printDescription(
            [
                "Save and re-use the following script to re-run this upgrade non-interactively:",
                "",
                nonInteractiveCommand,
            ]
        )

        self.printH1("Review Settings")
        print_formatted_text(HTML(f"<LightSlateGrey>Instance ID ..................... {instanceId}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Current MAS Channel ............. {self.currentChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Next MAS Channel ................ {self.nextChannel}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Skip Pre-Upgrade Checks ......... {self.skipPreCheck}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Pipeline Storage Class .......... {self.pipelineStorageClass}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>Pipeline Storage Access Mode .... {self.pipelineStorageAccessMode}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>OLM Approval Mode ............... {self.olmApprovalSummary()}</LightSlateGrey>"))

        if not self.noConfirm:
            print()
            continueWithUpgrade = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithUpgrade:
            # The shared launch sequence -- the same stages the TUI's launch
            # screen runs, via the ProgressReporter abstraction (Halo
            # spinners on this path, callbacks under the TUI)
            self.launchUpgrade()

            # Re-print the command so it is not lost in the scrollback above the
            # pipeline launch output
            self.printDescription(
                [
                    "For reference, the non-interactive command equivalent to this upgrade:",
                    "",
                    nonInteractiveCommand,
                ]
            )

    # ------------------------------------------------------------------
    # Guided workflow (TUI): step validators and conditional steps
    # ------------------------------------------------------------------
    def prepareUpgrade(self) -> None:
        """Detect the upgrade path and validate compatibility for the selected instance.

        Called as the ``validator`` on the TUI instance-selection step, and
        again by the target-channel step once the user has chosen a target.
        Reads ``mas_instance_id`` from ``self.params``, then runs the channel
        detection, compatibility validation, Monitor install order, Civil
        Kafka validation, routing-mode pre-flight check, RBAC evaluation,
        and pipeline storage class resolution that the classic ``upgrade()``
        method performs — raising ``RuntimeError`` on failure so the TUI
        displays the error inline and the step does not advance.  License
        acceptance is deliberately not enforced here: the conditional
        license-acceptance step collects it once the target channel is
        known (see ``licenseAcceptancePending``).

        When the target-channel step has written a choice to the
        ``upgrade_target_channel`` param, that choice is an explicit target
        and takes precedence over the auto-derived one.  An explicit target
        is a complete override: it is used as-is (validated to be either the
        current core channel or the next hop) and never short-circuited with
        "No action required" — the upgrade pipeline is idempotent, so
        re-running the current channel's upgrade is the supported way to
        complete an upgrade that failed part-way (e.g. core reached 9.1.x
        but the Manage Foundation install never happened).

        On success, populates ``self.currentChannel``, ``self.nextChannel``,
        ``self.autoNextChannel``, ``self.effectiveCurrentChannel``,
        ``self.detectedMode``, ``self.applyPreInstallMASRBAC`` and the
        pipeline storage class attributes so the review screen and
        ``buildCommand()`` have the right data.

        Raises:
            RuntimeError: If the upgrade path is invalid, or apps are
                incompatible with the target channel.  License acceptance
                and the Manage Foundation inputs are not enforced here —
                the conditional license-acceptance and manage-foundation
                steps collect them after this validator has run (see
                ``licenseAcceptancePending`` and ``manageFoundationPending``).
        """
        instanceId = self.params.get("mas_instance_id", "")
        self.masInstanceId = instanceId

        # The TUI cannot run interactive prompts, so every check below uses
        # its non-interactive variant (matching the classic --no-confirm
        # behaviour).
        self.noConfirm = True

        self.lookupTargetArchitecture()

        # Resolve the upgrade path (shared with the non-interactive
        # upgrade()): the target-channel step's choice is an explicit target
        # that completely overrides the derivation. RuntimeError propagates:
        # the TUI displays it on the step and the step does not advance.
        explicitTarget = self.params.get("upgrade_target_channel", "")
        self._resolveUpgradePath(instanceId, explicitTarget=explicitTarget if explicitTarget != "" else None)

        # The mas_channel PipelineRun param is the upgrade's target channel:
        # write it into params here, where the channel state is final — the
        # launch path must make no channel decisions of its own
        self.resolveMasChannelParam()

        # The channel-based checks below compare versions, which cannot parse
        # the "Unknown" placeholder — skip them when the channel was not
        # detectable (the classic path has the same effective behaviour: the
        # checks are all no-ops for an undetectable target).
        knownChannel = self.nextChannel not in ("", "Unknown")

        # License acceptance is NOT enforced here: the workflow's conditional
        # license-acceptance step collects it (see licenseAcceptancePending)
        # after this validator has run, so the remaining checks below always
        # execute and the review screen has the full upgrade state.

        # The only scenario where Manage Foundation needs to be installed during an upgrade is
        # from 9.0.x to 9.1.x (if Manage was not already installed in 9.0.x).  The conditional
        # manage-foundation step collects the inputs that path needs (entitlement key and
        # storage classes — see manageFoundationPending / prepareManageFoundation).
        self.isManageFoundation = False
        if knownChannel and self.nextChannel.startswith("9.1") and not verifyAppInstance(self.dynamicClient, instanceId, "manage"):
            self.isManageFoundation = True
        else:
            # Reset on re-validation (e.g. the user went back and selected a
            # different instance) so the manage-foundation step is not shown
            # and the pipeline param carries the correct value.
            self.setParam("should_install_manage_foundation", "false")

        # Compute Monitor install order for upgrade
        if knownChannel:
            self.computeMonitorInstallOrderForUpgrade(instanceId)

            # Validate Kafka requirements for Civil component during upgrade
            self.validateKafkaForCivilUpgrade(instanceId)

            # Block upgrade if Suite CR has a stale routingMode=path from a pre-9.2 install
            self.checkRoutingModeForUpgrade(instanceId, self.currentChannel)

        # Admin-mode detection and RBAC evaluation (shared with the
        # non-interactive upgrade()) — stored so launchUpgrade() can apply
        # the pre-install RBAC when the pipeline is submitted
        self._detectAdminModeAndEvaluateRBAC(instanceId, self.currentChannel)

        # Resolve the pipeline storage class now (normally read from the
        # existing config-pvc created at install time) so the review screen
        # summary and the generated non-interactive command include it
        self.configPipelineStorageClass(instanceId)

        # Detect the aggregate OLM install plan approval mode over the
        # instance's namespaces so the review screen can report it and the
        # launch step passes the effective mode to the PipelineRun
        self.detectOLMApprovalMode(namespacePrefix=f"mas-{instanceId}-")

    def prepareUpgradeForInstanceSelection(self) -> None:
        """Clear any chosen target channel, then run ``prepareUpgrade``.

        Used as the TUI instance-selection step's validator: re-entering
        instance selection invalidates the target chosen on the
        target-channel step (the newly selected instance may have different
        upgrade paths), so the choice is cleared and the target re-derived
        from the new instance's state.
        """
        self.setParam("upgrade_target_channel", "")
        self.prepareUpgrade()

    def targetChannelOptions(self) -> list:
        """The valid targets for the target-channel step's select field.

        Returns the auto-derived next hop followed by the current core
        channel (an idempotent re-run of the current release's upgrade —
        the supported way to complete an upgrade that failed part-way),
        deduplicated.  The auto-derived target is first so it is the
        pre-selected option.  Empty when the current channel could not be
        detected (the target-channel step is not shown then).

        Returns:
            list: The selectable target channels, auto-derived first.
        """
        if self.currentChannel in (None, "", "Unknown"):
            return []

        options = []
        for channel in (self.autoNextChannel, self.currentChannel):
            if channel not in (None, "", "Unknown") and channel not in options:
                options.append(channel)
        return options

    def licenseAcceptancePending(self) -> bool:
        """Return True when the target release's license still needs accepting.

        Drives the ``condition`` of the TUI license-acceptance step: the step
        is only shown when ``prepareUpgrade`` has resolved a target channel
        carrying a license that has not been accepted yet (the TUI equivalent
        of the classic wizard's license yes/no prompt, and of
        ``--accept-license`` on the non-interactive path).  Re-evaluated by
        the shell whenever a step completes, so it always reflects the
        currently selected instance's target channel.

        Returns:
            bool: True when the license-acceptance step must be shown.
        """
        return not self.licenseAccepted and not self.devMode and self.nextChannel in self.licenses

    def manageFoundationPending(self) -> bool:
        """Return True when the manage-foundation step must be shown.

        Drives the ``condition`` of the TUI manage-foundation step: the step
        is only shown when ``prepareUpgrade`` detected that this upgrade
        needs to install Manage Foundation (9.0.x to 9.1.x without Manage)
        and its inputs have not been collected yet.  Once
        ``prepareManageFoundation`` completes, ``should_install_manage_foundation``
        is set and the step is skipped on re-navigation (e.g. going back to
        instance-selection and returning).

        Returns:
            bool: True when the manage-foundation step must be shown.
        """
        return self.isManageFoundation and self.getParam("should_install_manage_foundation") != "true"

    def lookupEntitlementKey(self, instanceId: str) -> Optional[str]:
        """Read the IBM entitlement key from the cluster's ibm-entitlement secret.

        The MAS installation writes a ``kubernetes.io/dockerconfigjson``
        Secret named ``ibm-entitlement`` into every ``mas-<instanceId>-*``
        namespace (and the SLS namespace) — the ``cp.icr.io/cp`` entry's
        password is the entitlement key (see the ansible-devops
        ``entitlement_key_rotation`` role, which manages the same secret).
        Reading it back means the user is never asked to re-enter a key the
        installation already stored.

        Args:
            instanceId (str): The MAS instance ID (secret is read from
                ``mas-<instanceId>-core``).

        Returns:
            Optional[str]: The entitlement key, or None when the secret is
            missing or carries no cp.icr.io credentials.
        """
        try:
            secretsAPI = self.dynamicClient.resources.get(api_version="v1", kind="Secret")
            secret = secretsAPI.get(name="ibm-entitlement", namespace=f"mas-{instanceId}-core")
            dockerConfigJson = json.loads(base64.b64decode(secret["data"][".dockerconfigjson"]))
            auths = dockerConfigJson.get("auths", {})
            # The install template writes the entitlement under cp.icr.io/cp;
            # accept the bare registry spelling too, in case the secret was
            # created by other tooling
            for registry in ("cp.icr.io/cp", "cp.icr.io"):
                password = auths.get(registry, {}).get("password")
                if password:
                    return password
        except (NotFoundError, ResourceNotFoundError, KeyError, ValueError, TypeError):
            logger.debug(f"Unable to read the ibm-entitlement secret from the mas-{instanceId}-core namespace")
        return None

    def prepareManageFoundation(self) -> None:
        """Configure the Manage Foundation installation for the TUI path.

        Called as the ``validator`` on the TUI manage-foundation step, after
        the (optional) storage classes have been written to ``self.params``.
        Performs the same configuration as the classic wizard's Manage
        Foundation block: reads the IBM entitlement key back from the
        cluster's ``ibm-entitlement`` secret (it is never prompted for or
        accepted as an input), sets the install flags and pipeline params,
        resolves the Db2 storage classes (validating any provided values
        against the cluster, auto-detecting the rest), and runs the
        silent-mode Db2 configuration.

        Raises:
            RuntimeError: When the entitlement key cannot be read from the
                cluster (fatal — the key is a prerequisite, not an input), a
                provided storage class does not exist on the cluster, or no
                storage classes can be resolved.
        """
        instanceId = self.params.get("mas_instance_id", "")

        # The TUI cannot run interactive prompts, so every configuration
        # below uses its non-interactive variant (matching the classic
        # --no-confirm behaviour).
        self.noConfirm = True

        # Entitlement key, install flags, pipeline params and the Db2
        # configuration (shared with the non-interactive path's Manage
        # Foundation block); fatalError under tuiMode raises RuntimeError,
        # which the step displays inline
        self._configureManageFoundation(instanceId)

    def fetchInstalledInstanceIds(self) -> None:
        """Fetch and cache the MAS instance IDs from the connected cluster.

        Run as ``post_connect`` on the TUI connect-cluster step, in the worker
        thread immediately after a successful connection.  Raises
        ``RuntimeError`` when no MAS instances are found so the error
        surfaces on the connect screen rather than leaving the
        instance-selection step empty.

        Raises:
            RuntimeError: When no MAS Suite instances are found on the cluster.
        """
        suites = listMasInstances(self.dynamicClient)
        instanceIds = sorted([suite["metadata"]["labels"]["mas.ibm.com/instanceId"] for suite in suites])
        if not instanceIds:
            raise RuntimeError("No MAS instances were found on this cluster.")
        self._installedInstanceIds = instanceIds

    # ------------------------------------------------------------------
    # Storage configuration (shared by both paths)
    # ------------------------------------------------------------------
    def configPipelineStorageClass(self, instanceId: str) -> None:
        """
        Determine the storage class and access mode for the upgrade pipeline config-pvc.
        Sets self.pipelineStorageClass and self.pipelineStorageAccessMode.
        """

        if self.pipelineStorageClass and self.pipelineStorageAccessMode:
            if getStorageClass(self.dynamicClient, self.pipelineStorageClass) is None:
                self.fatalError(f"Storage class '{self.pipelineStorageClass}' specified via --storage-pipeline is not available on this cluster.")
            logger.debug(f"Using pipeline storage class from CLI args: {self.pipelineStorageClass} ({self.pipelineStorageAccessMode})")
            return

        # Read storage class from existing config-pvc on the cluster.
        # This is the normal upgrade path - the PVC was created during the original
        # install and already has the correct storage class for this cluster.
        existingStorageClass, existingAccessMode = lookupPipelineStorageClass(self.dynamicClient, instanceId)
        if existingStorageClass:
            self.pipelineStorageClass = existingStorageClass
            self.pipelineStorageAccessMode = existingAccessMode or ("ReadWriteOnce" if self.isSNO() else "ReadWriteMany")
            logger.debug(f"Using pipeline storage class from existing config-pvc: {self.pipelineStorageClass} ({self.pipelineStorageAccessMode})")
            return

        # No existing config-pvc found — MAS was not installed via the CLI.
        # Prompt the user to configure a storage class for the pipeline PVC,
        self.printH1("Configure Pipeline Storage Class")
        self.printDescription(
            [
                "The upgrade pipeline requires a PersistentVolumeClaim (config-pvc) to store pipeline data.",
                "No existing config-pvc was found in the pipelines namespace.",
            ]
        )

        # Try to auto-detect a known storage provider as a default suggestion
        suggestedStorageClass = None
        suggestedAccessMode = None
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)

        if defaultStorageClasses.provider is not None:
            if self.isSNO() or defaultStorageClasses.rwx is None:
                suggestedStorageClass = defaultStorageClasses.rwo
                suggestedAccessMode = "ReadWriteOnce"
            else:
                suggestedStorageClass = defaultStorageClasses.rwx
                suggestedAccessMode = "ReadWriteMany"

            if not self.tuiMode:
                print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class : {suggestedStorageClass}</LightSlateGrey>"))
                print_formatted_text(HTML(f"<LightSlateGrey>  - Access mode   : {suggestedAccessMode}</LightSlateGrey>"))

        # Accept the suggestion, or fall through to manual prompt
        useDetected = False
        if suggestedStorageClass:
            if self.noConfirm:
                # Non-interactive mode: accept auto-detected value without prompting
                self.pipelineStorageClass = suggestedStorageClass
                self.pipelineStorageAccessMode = suggestedAccessMode
                return
            useDetected = self.yesOrNo("Use the auto-detected storage class")

        if not useDetected:
            # No provider detected or user declined - fail fast in non-interactive mode
            if self.noConfirm:
                if self.tuiMode:
                    self.fatalError(
                        "No storage class could be detected for the pipeline config-pvc. "
                        "The upgrade pipeline requires one to create the config-pvc; re-run with --storage-pipeline and --storage-accessmode."
                    )
                self.fatalError(
                    "No storage class could be detected for the pipeline config-pvc and --no-confirm is set. "
                    "Please re-run with --storage-pipeline and --storage-accessmode."
                )

            # Customer declined the suggested class — keep the suggested access mode,
            # show the full list and let them pick a different storage class name.
            accessMode = suggestedAccessMode or ("ReadWriteOnce" if self.isSNO() else "ReadWriteMany")
            self.pipelineStorageAccessMode = accessMode

            self.printDescription([f"Select a {accessMode} storage class from the list below:"])
            for storageClass in getStorageClasses(self.dynamicClient):
                print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))
            print()

            self.pipelineStorageClass = prompt(
                HTML(f"<Yellow>Enter the name of the {accessMode} storage class</Yellow> "),
                validator=StorageClassValidator(),
                validate_while_typing=False,
            )
        else:
            self.pipelineStorageClass = suggestedStorageClass
            self.pipelineStorageAccessMode = suggestedAccessMode

    def configStorageClasses(self) -> None:
        """
        Determine storage_class_rwo and storage_class_rwx for Manage Foundation Db2/PVC provisioning.
        Only called when Manage Foundation is being installed during upgrade (9.0 → 9.1).

        Thin wrapper over the shared implementation (``StorageClassMixin`` in
        ``mas/cli/common/storageClasses.py``) with the upgrade flavour
        (CLI args / TUI dropdown selections win over auto-detection) and the
        Manage Foundation-specific no-detection error messages.  See the
        mixin for the resolution flow and its priorities.
        """
        StorageClassMixin.configStorageClasses(
            self,
            noDetectionTuiMessage=(
                "No storage classes could be detected for the Manage Foundation Db2 instances. "
                "Enter the ReadWriteOnce and ReadWriteMany storage classes to use on this step."
            ),
            noDetectionFatalMessage=(
                "No storage classes could be detected for Manage Foundation Db2 instances and --no-confirm is set. "
                "Please re-run with --storage-class-rwo and --storage-class-rwx."
            ),
        )

    # ------------------------------------------------------------------
    # Upgrade path resolution, validations and shared configuration (both paths)
    # ------------------------------------------------------------------
    def _resolveUpgradePath(self, instanceId: str, explicitTarget: Optional[str] = None, validateCompatibility: bool = True) -> None:
        """Detect the current channel and resolve the upgrade's target channel.

        The single implementation of upgrade-path resolution, shared by the TUI's ``prepareUpgrade`` and the non-interactive ``upgrade()``: detects the instance's current channel, validates an explicit target against it (or derives the target from the oldest channel across Core + all installed apps, which handles partial upgrade resumption correctly), and validates installed apps' compatibility with the target.

        On success sets ``self.currentChannel``, ``self.nextChannel`` and -- when the target was derived -- ``self.effectiveCurrentChannel`` and ``self.autoNextChannel``. An explicit target is a complete override: it is used as-is and never short-circuits with "No action required" -- the upgrade pipeline is idempotent, so re-running the current channel's upgrade is the supported way to complete an upgrade that failed part-way.

        Args:
            instanceId (str): The MAS instance ID.
            explicitTarget (str, optional): The user-chosen target (the TUI target-channel step's choice, or ``--next-channel``); None derives the target from the instance's state.
            validateCompatibility (bool, optional): Whether to validate the installed apps against the target channel. Dev mode passes False (core-upgrade consults its own compatibility matrix, so the target is only informative). Defaults to True.

        Raises:
            NoUpgradeRequiredError: Every component is on the latest channel -- there is nothing to submit (the non-interactive path exits cleanly on this; the TUI shows it on the step).
            RuntimeError: No valid upgrade path to the explicit target, no upgrade available from the current channel, or an installed app is incompatible with the target.
        """
        currentChannel = getMasChannel(self.dynamicClient, instanceId)
        if currentChannel is not None:
            # Fetched when the target is derived or compatibility is
            # validated (dev mode's informative target needs neither)
            if explicitTarget in (None, "") or validateCompatibility:
                installedAppsChannel = getAppsSubscriptionChannel(self.dynamicClient, instanceId)
            else:
                installedAppsChannel = []

            if explicitTarget not in (None, ""):
                if explicitTarget == currentChannel:
                    # Retry scenario: MAS core is already on the target channel.
                    # The upgrade pipeline is idempotent, so re-running it is
                    # safe (and is how an upgrade that failed part-way is
                    # completed) — never short-circuit with "No action
                    # required", even when every component is already there.
                    pass
                elif explicitTarget == self.upgrade_path.get(currentChannel):
                    # Valid upgrade path: currentChannel -> explicitTarget
                    pass
                else:
                    raise RuntimeError(f"No upgrade path available from {currentChannel} to {explicitTarget}")

                self.nextChannel = explicitTarget
            else:
                # Derive the target from upgrade_path using the oldest channel
                # across Core + all installed apps: this handles partial
                # upgrade resumption correctly — e.g. if Core reached 9.1.x
                # but Manage is still on 9.0.x, effectiveCurrentChannel will
                # be 9.0.x and the target will be 9.1.x instead of 9.2.x.
                allChannels = [currentChannel] + [app["channel"] for app in installedAppsChannel]

                def channelOrder(ch):
                    keys = list(self.upgrade_path.keys())
                    return keys.index(ch) if ch in keys else -1

                self.effectiveCurrentChannel = max(allChannels, key=channelOrder)

                # Early exit BEFORE the upgrade_path lookup: if every
                # component is on the same channel and that channel has no
                # further upgrade target, the instance is fully upgraded
                # (no self-referencing entry like "9.2.x": "9.2.x" is needed
                # in upgrade_path)
                if self.effectiveCurrentChannel not in self.upgrade_path and all(ch == self.effectiveCurrentChannel for ch in allChannels):
                    raise NoUpgradeRequiredError(
                        f"No action required, {instanceId} is already fully upgraded. All components are on channel {self.effectiveCurrentChannel}."
                    )

                if self.effectiveCurrentChannel not in self.upgrade_path:
                    raise RuntimeError(f"No upgrade available, {instanceId} is already on the latest release {self.effectiveCurrentChannel}")

                self.nextChannel = self.upgrade_path[self.effectiveCurrentChannel]

                # Remember the auto-derived target: the default selection for
                # the TUI's target-channel step (kept as-is when an explicit
                # target was chosen — the choice wins)
                self.autoNextChannel = self.nextChannel

            # An explicit target equal to the current channel deliberately
            # does NOT short-circuit above: the pipeline is idempotent, so
            # the re-run is submitted and simply completes whatever is left.
            # The auto-derived path can never reach that state (a derived
            # target equals the current channel only when an app is behind,
            # which means there is work to do).

            if validateCompatibility and self.nextChannel in self.compatibilityMatrix:
                incompatibleApps = []
                for installedApp in installedAppsChannel:
                    appId = installedApp["appId"]
                    appChannel = installedApp["channel"]

                    # Check if app is supported in the target channel
                    if appId not in self.compatibilityMatrix[self.nextChannel]:
                        if "feature" in self.nextChannel:
                            incompatibleApps.append(f"  - {appId}: Not available in feature channel {self.nextChannel}")
                        elif appId == "assist":
                            # Assist was withdrawn in MAS 9.2; its functionality was migrated to the Collaborate add-on
                            incompatibleApps.append(
                                f"  - {appId}: Not supported in {self.nextChannel} (Assist has been replaced by the Collaborate add-on in MAS 9.2+)"
                            )
                        else:
                            incompatibleApps.append(f"  - {appId}: Not supported in {self.nextChannel}")
                    else:
                        # Check if current app channel is compatible with target MAS channel
                        compatibleAppChannels = self.compatibilityMatrix[self.nextChannel][appId]
                        if appChannel not in compatibleAppChannels:
                            incompatibleApps.append(
                                f"  - {appId} (currently on {appChannel}): Must be on one of {compatibleAppChannels} to upgrade to MAS {self.nextChannel}"
                            )

                if incompatibleApps:
                    raise RuntimeError(f"Cannot upgrade to {self.nextChannel}. The following apps have compatibility issues:\n" + "\n".join(incompatibleApps))
        else:
            # We still allow the upgrade to proceed even though we can't detect the MAS instance
            # (e.g. the upgrade may be queued up to run after install)
            currentChannel = "Unknown"
            self.autoNextChannel = ""
            if self.nextChannel == "":
                self.nextChannel = "Unknown"

        self.currentChannel = currentChannel

    def _detectAdminModeAndEvaluateRBAC(self, instanceId: str, currentChannel: str) -> None:
        """Detect the upgrade's admin mode and evaluate pre-install RBAC access.

        The single implementation shared by the TUI's ``prepareUpgrade`` and the non-interactive ``upgrade()``: determines the permission mode the target channel requires (detecting the existing mode when upgrading to 9.3.x+ from 9.2.x+, defaulting to cluster mode for 9.2.x targets) and, when a mode applies, evaluates whether the pre-install MAS RBAC can be applied. Stores ``self.detectedMode`` and ``self.applyPreInstallMASRBAC`` for ``launchUpgrade()``'s RBAC stage and the review summary.

        Args:
            instanceId (str): The MAS instance ID.
            currentChannel (str): The instance's current channel ("Unknown" when undetectable -- both mode conditions are no-ops then).
        """
        detectedMode = None

        # The version comparisons below cannot parse the "Unknown"
        # placeholder (isVersionEqualOrAfter raises on it) -- skip both
        # branches when either channel is undetectable
        knownChannel = self.nextChannel not in ("", "Unknown") and currentChannel not in (None, "", "Unknown")
        if knownChannel and isVersionEqualOrAfter("9.3.0", self.nextChannel) and isVersionEqualOrAfter("9.2.0", currentChannel):
            # Upgrading TO 9.3.x+ FROM 9.2.x+: detect existing permission mode
            logger.info(f"Upgrading from {currentChannel} to {self.nextChannel}: detecting existing permission mode")
            detectedMode = getPermissionMode(self.dynamicClient, instanceId)
        elif knownChannel and self.nextChannel.startswith("9.2"):
            # Upgrading TO 9.2.x: default to cluster mode
            # (covers both 9.1.x→9.2.x and 9.2.x-feature→9.2.x)
            logger.info("Upgrading to 9.2.x: defaulting to cluster mode")
            detectedMode = "cluster"

        # launchUpgrade's RBAC stage reads the app attribute
        self.detectedMode = detectedMode

        if detectedMode:
            self.applyPreInstallMASRBAC = evaluatePreinstallRBACAccess(
                dynamicClient=self.dynamicClient,
                masChannel=self.nextChannel,
                adminMode=detectedMode,
                instanceId=instanceId,
                noConfirm=self.noConfirm,
                printH1Func=self.printH1,
                printDescriptionFunc=self.printDescription,
                yesOrNoFunc=self.yesOrNo,
                fatalErrorFunc=self.fatalError,
                operation="upgrade",
            )

    def _configureManageFoundation(self, instanceId: str) -> None:
        """Configure the Manage Foundation installation an upgrade requires.

        The single implementation shared by the TUI's ``prepareManageFoundation`` step validator and the non-interactive ``upgrade()``'s Manage Foundation block: reads the IBM entitlement key back from the cluster's ``ibm-entitlement`` secret (it is never prompted for or accepted as an input), sets the install flags and pipeline params, resolves the Db2 storage classes (validating any provided values against the cluster, auto-detecting the rest), runs the silent-mode Db2 configuration, and only then marks the installation configured -- a failure above leaves ``should_install_manage_foundation`` unset so the TUI step stays pending for a retry.

        Args:
            instanceId (str): The MAS instance ID.

        Raises:
            RuntimeError: When the entitlement key cannot be read from the cluster (fatal -- the key is a prerequisite, not an input), a provided storage class does not exist on the cluster, or no storage classes can be resolved (fatalError under tuiMode raises RuntimeError; on the non-interactive path it exits).
        """
        # The entitlement key is read from the cluster's ibm-entitlement
        # secret (written during the original installation) — it is neither
        # prompted for nor accepted as a CLI argument.
        entitlementKey = self.lookupEntitlementKey(instanceId)
        if entitlementKey is None:
            self.fatalError(
                f"Unable to read the IBM entitlement key from the cluster (no 'ibm-entitlement' secret with cp.icr.io "
                f"credentials found in the mas-{instanceId}-core namespace).  Restore the secret and re-run the upgrade."
            )
        self.setParam("ibm_entitlement_key", entitlementKey)

        # Attributes configDb2 reads
        self.manageAppName = "Manage foundation"
        self.showAdvancedOptions = False
        self.installIoT = False
        self.installMonitor = False
        self.installFacilities = False
        self.installManage = True

        self.setParam("mas_appws_components", "")
        self.setParam("mas_app_settings_aio_flag", "false")
        self.setParam("mas_app_channel_manage", self.nextChannel)
        self.setParam("mas_workspace_id", getWorkspaceId(self.dynamicClient, instanceId))

        # Storage classes for the Manage Foundation Db2 instances: validates
        # any provided values against the cluster, auto-detecting the rest
        self.configStorageClasses()

        # Silent-mode Db2 configuration: defaults for everything the classic
        # wizard prompts for (dedicated Db2 Warehouse instance for Manage)
        self.configDb2(silentMode=True)

        # Mark the Manage Foundation installation configured only now that
        # every input has validated — a failure above leaves the TUI step
        # pending so the user can correct the inputs and retry
        self.setParam("should_install_manage_foundation", "true")

    def computeMonitorInstallOrderForUpgrade(self, instanceId):
        """
        Determine the installation order for Monitor relative to IoT based on TARGET Monitor version.
        This is needed for upgrade scenarios where Monitor >= 9.2.0 must upgrade before IoT.
        For upgrades, we check the TARGET channel (where we're going), not current channel.
        """
        installedApps = getAppsSubscriptionChannel(self.dynamicClient, instanceId)
        hasMonitor = False
        hasIoT = False

        for app in installedApps:
            if app["appId"] == "monitor":
                hasMonitor = True
            elif app["appId"] == "iot":
                hasIoT = True

        if hasMonitor and hasIoT:
            # For upgrade, check the TARGET channel (self.nextChannel), not current channel
            # If upgrading TO 9.2.x or higher, Monitor must upgrade before IoT
            if self.nextChannel and isVersionEqualOrAfter("9.2.0", self.nextChannel):
                # Upgrading to Monitor >= 9.2.0: Monitor must upgrade before IoT
                self.setParam("mas_monitor_install_order", "before-iot")
                logger.debug(f"Upgrading to MAS {self.nextChannel} (>= 9.2.0): Monitor will upgrade before IoT")
            else:
                # Upgrading to Monitor < 9.2.0: Monitor upgrades after IoT (legacy)
                self.setParam("mas_monitor_install_order", "after-iot")
                logger.debug(f"Upgrading to MAS {self.nextChannel} (< 9.2.0): Monitor will upgrade after IoT (legacy behavior)")
        elif hasMonitor:
            # Only Monitor, no IoT - order doesn't matter but set default
            self.setParam("mas_monitor_install_order", "before-iot")
        else:
            # No Monitor installed - set default
            self.setParam("mas_monitor_install_order", "after-iot")

    def validateKafkaForCivilUpgrade(self, instanceId):
        """
        Validate Kafka requirements when upgrading Manage with Civil to 9.2+.
        Civil >= 9.2 requires Kafka configuration.
        Warns user and gives option to proceed without Kafka (Defect Detection will not function).
        """
        # Check if upgrading TO Manage 9.2+ (use TARGET channel, not current)
        if not self.nextChannel or not isVersionEqualOrAfter("9.2.0", self.nextChannel):
            return

        # Query the ManageWorkspace CR to check if Civil component is installed
        workspaceId = getWorkspaceId(self.dynamicClient, instanceId)
        if not workspaceId:
            logger.debug("Could not determine workspace ID, skipping Civil Kafka validation")
            return

        try:
            # Query ManageWorkspace CR
            workspaceAPI = self.dynamicClient.resources.get(api_version="apps.mas.ibm.com/v1", kind="ManageWorkspace")
            workspace = workspaceAPI.get(name=f"{instanceId}-{workspaceId}", namespace=f"mas-{instanceId}-manage")

            # Check if Civil component is in the workspace spec
            components = workspace.get("spec", {}).get("components", {})
            hasCivil = "civil" in components

            if hasCivil:
                logger.debug(f"Civil component detected, upgrading to {self.nextChannel} (>= 9.2.0): Kafka required")

                # Validate Kafka configuration exists
                kafkaAction = self.getParam("kafka_action_system")
                hasKafkaConfig = kafkaAction in ["install", "byo"]

                if not hasKafkaConfig:
                    # Warn user but give option to proceed
                    print_formatted_text(HTML("<Yellow>⚠ Warning: Kafka Configuration Required</Yellow>"))
                    print_formatted_text(
                        HTML(
                            f"<LightSlateGrey>Upgrading to Manage {self.nextChannel} with Civil Infrastructure component "
                            "requires Kafka configuration. Civil versions >= 9.2.0 require a shared system-scope Kafka instance.</LightSlateGrey>"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            "<LightSlateGrey>Without Kafka, the Defect Detection functionality within Civil Infrastructure will not work, "
                            "but other Civil and Manage components will continue to function.</LightSlateGrey>"
                        )
                    )
                    print()

                    if self.noConfirm:
                        # In non-interactive mode, log warning and proceed
                        logger.warning(
                            f"Upgrading to Manage {self.nextChannel} with Civil component without Kafka configuration. "
                            "Defect Detection functionality will not work."
                        )
                    else:
                        # In interactive mode, ask user if they want to proceed
                        if not self.yesOrNo("Do you want to proceed with the upgrade without Kafka? (Defect Detection will not work)"):
                            self.fatalError("Upgrade cancelled. Please configure Kafka before upgrading.")

        except Exception as e:
            logger.warning(f"Could not query ManageWorkspace CR for Civil component check: {e}")
            # Don't fail the upgrade if we can't query - let ansible handle it

    def checkRoutingModeForUpgrade(self, instanceId: str, currentChannel: str) -> None:
        """Block the upgrade when a pre-9.2 Suite CR has spec.settings.routingMode set to "path".

        A routingMode value was accidentally written to Suite CRs on pre-9.2 instances.
        If that stale value is present when upgrading from pre-9.2 to 9.2+, the pipeline will
        attempt an unintended routing mode switch. This check fails early with clear remediation guidance.

        Upgrades where the current channel is already 9.2+ are not blocked — routingMode=path
        on a 9.2+ instance was set intentionally and must be preserved.

        Args:
            instanceId (str): The MAS instance ID to inspect.
            currentChannel (str): The currently installed MAS channel.
        """
        # Only relevant when upgrading TO 9.2+
        if not self.nextChannel or not isVersionEqualOrAfter("9.2.0", self.nextChannel):
            return

        # Already on 9.2+: routingMode=path was set intentionally, do not block
        if currentChannel and isVersionEqualOrAfter("9.2.0", currentChannel):
            return

        try:
            suiteAPI = self.dynamicClient.resources.get(api_version="core.mas.ibm.com/v1", kind="Suite")
            suite = suiteAPI.get(name=instanceId, namespace=f"mas-{instanceId}-core")
            routingMode = suite.get("spec", {}).get("settings", {}).get("routingMode")

            if routingMode == "path":
                self.fatalError(
                    f'Cannot upgrade to {self.nextChannel}: spec.settings.routingMode is set to "path" on the Suite CR.\n\n'
                    "This value was accidentally written to pre-9.2 Suite CRs and will cause the upgrade\n"
                    "pipeline to attempt an unintended routing mode switch.\n\n"
                    "To resolve this, remove the field from the Suite CR before retrying the upgrade:\n\n"
                    f"  oc patch suite {instanceId} -n mas-{instanceId}-core --type=json \\\n"
                    '    -p \'[{"op":"remove","path":"/spec/settings/routingMode"}]\'\n\n'
                    "After applying the patch, re-run the upgrade."
                )
        except Exception as e:
            logger.warning(f"Could not query Suite CR to check routingMode for upgrade pre-flight check: {e}")

    def resolveMasChannelParam(self) -> None:
        """Write the ``mas_channel`` PipelineRun param: the upgrade's target channel.

        Aligns with the ``suite_upgrade`` role's semantics — ``mas_channel``
        is the destination channel (the channel we are upgrading TO; see
        ansible-devops suite_upgrade, where an unset value auto-selects the
        next release and an explicit value is used as-is).  Called once the
        channel state is final — by ``prepareUpgrade`` on the TUI path and
        after channel resolution in ``upgrade()`` on the classic path — so
        that the launch path makes no channel decisions of its own:

        - Derived target (the TUI's only mode, and the classic path without
          ``--next-channel``): ``nextChannel`` is derived from
          ``effectiveCurrentChannel`` (the oldest channel across Core and
          all installed apps) so the upgrade targets the correct hop.
        - Explicit ``--next-channel`` (or the TUI target-channel choice):
          ``nextChannel`` is the requested target as-is.
        - Retry scenario (Core already on the target channel): a
          first-class explicit choice — the target equals the current
          channel, the role's core-upgrade recognises Core is already
          there, and the app upgrade tasks bring the remaining components
          (including a pending Manage Foundation install) up to it.  The
          pipeline is idempotent, so this never short-circuits with "No
          action required".
        - Undetectable target: the param is left empty so the role
          auto-selects the next release from the live subscription.
        """
        masChannel = self.nextChannel if self.nextChannel not in ("", "Unknown") else ""
        self.setParam("mas_channel", masChannel)

    # ------------------------------------------------------------------
    # Pipeline launch (shared by both paths)
    # ------------------------------------------------------------------
    def _validateOpenShiftPipelines(self) -> tuple[bool, str]:
        """Validate OpenShift Pipelines installation.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        if installOpenShiftPipelines(self.dynamicClient):
            return True, "OpenShift Pipelines Operator is installed and ready to use"
        return False, "OpenShift Pipelines Operator installation failed"

    def _prepareUpgradeNamespace(self, namespace: str, instanceId: str) -> tuple[bool, str]:
        """Create and prepare the upgrade pipelines namespace and secrets.

        Args:
            namespace (str): Pipelines namespace (``mas-<instanceId>-pipelines``).
            instanceId (str): The MAS instance being upgraded.

        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        createNamespace(self.dynamicClient, namespace)
        preparePipelinesNamespace(
            dynClient=self.dynamicClient,
            instanceId=instanceId,
            storageClass=self.pipelineStorageClass,
            accessMode=self.pipelineStorageAccessMode,
        )
        prepareUpgradeSecrets(
            dynClient=self.dynamicClient,
            namespace=namespace,
            ibm_entitlement_key=self.getParam("ibm_entitlement_key"),
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

    def _submitUpgradePipelineRun(self) -> tuple[bool, str]:
        """Submit the upgrade PipelineRun.

        Every PipelineRun param is already in ``self.params`` by this point:
        ``mas_instance_id`` and ``skip_pre_check`` were written at their
        origin, and ``mas_channel`` was resolved by ``prepareUpgrade`` when
        the channel state was final — no decisions are made here.

        Returns:
            tuple[bool, str]: (success, detail_message — the pipeline run URL on success)
        """
        pipelineURL = launchUpgradePipeline(self.dynamicClient, params=self.params)
        if pipelineURL:
            return True, pipelineURL
        return False, "Failed — see log file for details"

    def launchUpgrade(self, progressCallback: Optional[Callable] = None, startCallback: Optional[Callable] = None) -> None:
        """Submit the Tekton upgrade pipeline with unified progress reporting.

        Uses the ProgressReporter abstraction to share one execution path
        between the CLI (Halo spinners) and TUI (callbacks) — the same
        pattern as ``UpdateApp.launchUpdate``.  Stages: Tekton definitions
        with digest, OpenShift Pipelines validation, optional pre-install
        RBAC, namespace preparation, Tekton definitions install, and
        PipelineRun submission.

        Args:
            progressCallback (Callable, optional): TUI callback (label, ok, detail) -> None
            startCallback (Callable, optional): TUI start callback (label) -> None
        """
        from mas.cli.common.progress import HaloProgressReporter, CallbackProgressReporter

        if progressCallback is not None:
            reporter = CallbackProgressReporter(progressCallback, startCallback)
        else:
            reporter = HaloProgressReporter(self.spinner, self.successIcon, self.failureIcon)

        # Tekton definitions with digest (no-op unless airgap / CLI digest);
        # shared by both execution paths as in the classic launch section
        self.createTektonFileWithDigest()

        instanceId = self.params.get("mas_instance_id", "")
        pipelinesNamespace = f"mas-{instanceId}-pipelines"

        # Stage 1: Validate OpenShift Pipelines
        reporter.start("Validate OpenShift Pipelines")
        success, detail = self._validateOpenShiftPipelines()
        if success:
            reporter.success("Validate OpenShift Pipelines", detail)
        else:
            reporter.failure("Validate OpenShift Pipelines", detail)
            self.fatalError("Installation failed")

        # Stage 2: Apply pre-install RBAC (if needed)
        if self.applyPreInstallMASRBAC and self.detectedMode:
            # Resolve before any output so a failure is reported cleanly
            rbacRootDir = self.getPreinstallRBACRootDir()

            label = "Apply pre-install MAS RBAC"
            reporter.start(label)
            self.selectedAppsForRBAC = getInstalledApps(self.dynamicClient, instanceId)
            applyPreInstallMASRBAC(
                dynClient=self.dynamicClient,
                masVersion=".".join(self.nextChannel.split(".")[:2]),
                masInstanceId=instanceId,
                adminMode=self.detectedMode,
                selectedApps=self.selectedAppsForRBAC,
                rbacRootDir=rbacRootDir,
            )
            reporter.success(label, f"Pre-install MAS RBAC applied for target version {self.nextChannel} (mode: {self.detectedMode})")

        # Stage 3: Prepare pipelines namespace
        reporter.start("Prepare pipelines namespace")
        success, detail = self._prepareUpgradeNamespace(pipelinesNamespace, instanceId)
        reporter.success("Prepare pipelines namespace", detail)

        # Stage 4: Install Tekton definitions
        reporter.start("Install Tekton definitions")
        success, detail = self._installTektonDefinitions(pipelinesNamespace)
        reporter.success("Install Tekton definitions", f"Latest Tekton definitions are installed ({detail})")

        # Stage 5: Submit PipelineRun
        reporter.start("Submit PipelineRun")
        success, detail = self._submitUpgradePipelineRun()
        if success:
            # ``detail`` is the pipeline run URL: the TUI renders it beneath
            # the step list and the Copy URL button copies it (see
            # LaunchScreen._on_checklist_done).
            reporter.success("Submit PipelineRun", detail)
        else:
            reporter.failure("Submit PipelineRun", f"Failed to submit PipelineRun for {instanceId} upgrade, see log file for details")
