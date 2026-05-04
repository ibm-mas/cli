#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from ..cli import BaseApp
from ..validators import InstanceIDFormatValidator
from .argParser import setupPreinstallRBACArgParser
from mas.devops.pre_install import applyPreInstallMASRBAC, permissionCheckForRBAC
from mas.devops.utils import isVersionEqualOrAfter

logger = logging.getLogger(__name__)

VALID_PREINSTALL_APPS = {
    "core",
    "aiservice",
    "arcgis",
    "facilities",
    "iot",
    "manage",
    "monitor",
    "optimizer",
    "predict",
    "visualinspection"
}


class SetupPreinstallRBACApp(BaseApp):

    def promptForMASInstanceId(self) -> None:
        self.printH2("MAS Instance")
        self.promptForString("Instance ID", "mas_instance_id", validator=InstanceIDFormatValidator())

    def promptForMASVersion(self) -> None:
        self.printH2("MAS Version")
        self.printDescription([
            "Enter the MAS version in x.y.z format.",
            "For example: 9.2.0"
        ])
        self.promptForString("MAS Version", "mas_version", default="9.2.0")

    def promptForPermissionMode(self) -> None:
        self.printH2("Permission Mode")
        self.printDescription([
            "Choose the permission mode for which pre-install RBAC should be set up:",
            "",
            "  1. cluster",
            "  2. namespaced",
            "  3. minimal"  # we do not require pre install for minimal, but we need it for the one role ingresscontroller
        ])
        permissionModeInt = self.promptForInt("Permission Mode", default=1, min=1, max=3)
        permissionModeMap = {1: "cluster", 2: "namespaced", 3: "minimal"}
        self.setParam("permission_mode", permissionModeMap[permissionModeInt])

    def promptForApps(self) -> None:
        self.printH2("MAS Applications")
        self.printDescription([
            "Enter a comma-separated list of MAS applications to determine which pre-install RBAC manifests are set up.",
            "For example: core,manage,iot"
        ])
        appCompleter = WordCompleter([
            "core",
            "aiservice",
            "arcgis",
            "facilities",
            "iot",
            "manage",
            "monitor",
            "optimizer",
            "predict",
            "visualinspection"
        ], ignore_case=True)
        apps = prompt("Apps: ", completer=appCompleter).strip()
        if apps == "":
            self.fatalError("Apps must be set")
        self.setParam("apps", apps)

    def setupPreinstallRBAC(self, argv):
        """
        Set up pre-install RBAC for MAS.
        """
        self.args = setupPreinstallRBACArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.interactive_mode = not all([
            self.args.mas_instance_id,
            self.args.mas_version,
            self.args.permission_mode,
            self.args.apps
        ])

        self.printH1("Set Target OpenShift Cluster")
        self.connect()

        if self.interactive_mode:

            if self.args.mas_instance_id is not None:
                self.setParam("mas_instance_id", self.args.mas_instance_id)
            else:
                self.promptForMASInstanceId()

            if self.args.mas_version is not None:
                self.setParam("mas_version", self.args.mas_version.strip())
            else:
                self.promptForMASVersion()
        else:
            requiredParams = ["mas_instance_id", "mas_version", "permission_mode", "apps"]
            for key in requiredParams:
                value = getattr(self.args, key)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    self.fatalError(f"{key} must be set")
                self.setParam(key, value.strip() if isinstance(value, str) else value)

        instanceId = self.getParam("mas_instance_id")
        masVersion = self.getParam("mas_version").strip()

        masVersionParts = masVersion.split(".")
        if len(masVersionParts) != 3 or not all(part.isdigit() for part in masVersionParts):
            self.fatalError("MAS version must be provided in x.y.z format, for example 9.2.0")

        masVersionForComparison = masVersion
        if not isVersionEqualOrAfter("9.2.0", masVersionForComparison):
            self.fatalError("mas pre-install is supported only for MAS version 9.2.0 and later")

        masVersion = ".".join(masVersionParts[:2])

        if self.interactive_mode:
            if self.args.permission_mode is not None:
                self.setParam("permission_mode", self.args.permission_mode.strip())
            else:
                self.promptForPermissionMode()

            if self.args.apps is not None:
                self.setParam("apps", self.args.apps.strip())
            else:
                self.promptForApps()

        permissionMode = self.getParam("permission_mode").strip()
        selectedApps = [app.strip().lower() for app in self.getParam("apps").split(",") if app.strip()]
        invalidApps = sorted({app for app in selectedApps if app not in VALID_PREINSTALL_APPS})
        if invalidApps:
            self.fatalError(
                f"Unsupported app value(s): {', '.join(invalidApps)}. "
                f"Supported apps are: {', '.join(sorted(VALID_PREINSTALL_APPS))}"
            )

        permissionResults = permissionCheckForRBAC(self.dynamicClient)
        hasAdminPermissions = all(result["allowed"] for result in permissionResults)
        if not hasAdminPermissions:
            self.fatalError("You do not have the appropriate permissions to set up pre-install RBAC for MAS. Only a cluster administrator can perform this action.")

        self.printH1("MAS Pre-Install")
        self.printDescription([
            "This will set up pre-install RBAC for MAS.",
            "",
            "This command is supported only for MAS version 9.2 and later.",
            "The RBAC that is applied is determined by the selected permission mode and apps."
        ])
        self.printSummary("Instance ID", instanceId)
        self.printSummary("MAS Version", masVersion)
        self.printSummary("Permission Mode", permissionMode)
        self.printSummary("Selected Apps", ", ".join(selectedApps))

        continueWithSetup = True
        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above before the RBAC setup begins."
            ])
            continueWithSetup = self.yesOrNo("Proceed with these settings")

        if not continueWithSetup:
            self.fatalError("Pre-install RBAC setup aborted")

        with Halo(text=f"Setting up pre-install RBAC for MAS instance {instanceId}...", spinner=self.spinner) as h:
            applyPreInstallMASRBAC(
                dynClient=self.dynamicClient,
                masVersion=masVersion,
                masInstanceId=instanceId,
                permissionMode=permissionMode,
                selectedApps=selectedApps
            )
            h.stop_and_persist(symbol=self.successIcon, text=f"Pre-install RBAC for MAS is ready for {instanceId}")

        self.printDescription([
            "The pre-install RBAC for MAS has been set up."
        ])
