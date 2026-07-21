# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Pre-install RBAC evaluation mixin for the update command.

Provides ``UpdateRBACMixin`` which is mixed into ``UpdateApp`` to supply the
logic that decides whether pre-install RBAC must be applied before the Tekton
pipeline is submitted (i.e. when instances are transitioning from a pre-release
build to a GA release that introduced RBAC support).
"""

import logging

from mas.devops.mas import listMasInstances, getMasChannel, getPermissionMode
from mas.devops.utils import isVersionEqualOrAfter
from ..rbac_utils import evaluatePreinstallRBACAccess

logger = logging.getLogger(__name__)


class UpdateRBACMixin:
    """Mixin providing pre-install RBAC evaluation helpers for UpdateApp."""

    def shouldApplyRBACForInstance(self, instanceId, currentVersion, targetCatalog) -> bool:
        """Determine whether pre-install RBAC should be applied for a MAS instance.

        Returns ``True`` when the instance is transitioning from a pre-release
        build to a GA version that is >= 9.2.0 (the first release that required
        RBAC initialisation before the operator upgrade).

        Args:
            instanceId: The MAS instance ID.
            currentVersion: The current reconciled version string
                (e.g. "9.2.0-pre.stable+21734").
            targetCatalog: The target catalog dict containing version mappings.

        Returns:
            bool: True if RBAC should be applied for the pre-release → GA
                transition, False otherwise.
        """
        if not currentVersion or not targetCatalog:
            return False

        if "-pre" not in currentVersion:
            return False

        channel = getMasChannel(self.dynamicClient, instanceId)
        if not channel:
            logger.warning(f"Could not determine channel for instance {instanceId}")
            return False

        targetVersion = targetCatalog.get("mas_core_version", {}).get(channel)
        if not targetVersion:
            logger.warning(f"No target version found in catalog for channel {channel}")
            return False

        if "-pre" in targetVersion:
            logger.info(f"Instance {instanceId} will stay on pre-release (current: {currentVersion}, target: {targetVersion}). Skipping RBAC.")
            return False

        if isVersionEqualOrAfter("9.2.0", targetVersion):
            logger.info(f"Instance {instanceId} will transition from pre-release to GA (current: {currentVersion}, target: {targetVersion}).")
            return True

        logger.info(f"Instance {instanceId} target version {targetVersion} is < 9.2.0. Skipping RBAC.")
        return False

    def evaluatePreinstallRBACAccessForUpdate(self) -> None:
        """Evaluate whether pre-install RBAC should be applied for transitioning instances.

        Populates ``self.instancesNeedingRBAC`` and ``self.applyPreInstallMASRBAC``.
        Calls the shared ``evaluatePreinstallRBACAccess`` utility to check cluster
        permissions for the first instance that requires RBAC.
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

                    detectedMode = None
                    if targetVersion == "9.2.0":
                        detectedMode = "cluster"
                        logger.info(f"MAS instance {instanceId} transitioning to 9.2.0 GA: defaulting to cluster mode")
                    elif isVersionEqualOrAfter("9.3.0", targetVersion):
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
