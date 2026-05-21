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

VALID_PREINSTALL_APPS = {"core", "aiservice", "arcgis", "facilities", "iot", "manage", "monitor", "optimizer", "predict", "visualinspection"}


class SetupPreinstallRBACApp(BaseApp):

    def promptForMASInstanceId(self) -> None:
        self.printH2("MAS Instance")
        self.mas_instance_id = self.promptForString("Instance ID", validator=InstanceIDFormatValidator())

    def promptForMASVersion(self) -> None:
        self.printH2("MAS Version")
        self.printDescription(["Enter the MAS version in x.y.z format.", "For example: 9.2.0"])
        self.mas_version = self.promptForString("MAS Version", default="9.2.0")

    def promptForPermissionMode(self) -> None:
        self.printH2("Permission Mode")
        self.printDescription(
            [
                "Choose the permission mode for which pre-install RBAC should be set up:",
                "",
                "  1. cluster",
                "  2. namespaced",
            ]
        )
        permissionModeInt = self.promptForInt("Permission Mode", default=1, min=1, max=2)
        permissionModeMap = {1: "cluster", 2: "namespaced"}
        self.permission_mode = permissionModeMap[permissionModeInt]

    def promptForApps(self) -> None:
        self.printH2("MAS Applications")
        self.printDescription(
            ["Enter a comma-separated list of MAS applications to determine which pre-install RBAC manifests are set up.", "For example: core,manage,iot"]
        )
        appCompleter = WordCompleter(
            ["core", "aiservice", "arcgis", "facilities", "iot", "manage", "monitor", "optimizer", "predict", "visualinspection"], ignore_case=True
        )
        apps = prompt("Apps: ", completer=appCompleter).strip()
        if apps == "":
            self.fatalError("Apps must be set")
        self.apps = apps

    def setupPreinstallRBAC(self, argv):
        """
        Set up pre-install RBAC for MAS.
        """
        self.args = setupPreinstallRBACArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm
        self.interactive_mode = not all([self.args.mas_instance_id, self.args.mas_version, self.args.permission_mode])

        self.printH1("Set Target OpenShift Cluster")
        self.connect()

        if self.interactive_mode:

            if self.args.mas_instance_id is not None:
                self.mas_instance_id = self.args.mas_instance_id
            else:
                self.promptForMASInstanceId()

            if self.args.mas_version is not None:
                self.mas_version = self.args.mas_version.strip()
            else:
                self.promptForMASVersion()

            if self.args.permission_mode is not None:
                self.permission_mode = self.args.permission_mode.strip()
            else:
                self.promptForPermissionMode()
        else:
            # Non-interactive mode - validate required parameters
            if not self.args.mas_instance_id or self.args.mas_instance_id.strip() == "":
                self.fatalError("mas_instance_id must be set")
            if not self.args.mas_version or self.args.mas_version.strip() == "":
                self.fatalError("mas_version must be set")
            if not self.args.permission_mode or self.args.permission_mode.strip() == "":
                self.fatalError("permission_mode must be set")

            self.mas_instance_id = self.args.mas_instance_id.strip()
            self.mas_version = self.args.mas_version.strip()
            self.permission_mode = self.args.permission_mode.strip()

        # Validate MAS version format
        masVersionParts = self.mas_version.split(".")
        if len(masVersionParts) != 3 or not all(part.isdigit() for part in masVersionParts):
            self.fatalError("MAS version must be provided in x.y.z format, for example 9.2.0")

        if not isVersionEqualOrAfter("9.2.0", self.mas_version):
            self.fatalError("mas pre-install is supported only for MAS version 9.2.0 and later")

        # Convert to x.y format for RBAC selection
        masVersion = ".".join(masVersionParts[:2])

        # Only prompt for apps in namespaced mode
        if self.permission_mode == "namespaced":
            if self.interactive_mode:
                if self.args.apps is not None:
                    self.apps = self.args.apps.strip()
                else:
                    self.promptForApps()
            else:
                # In non-interactive mode, apps is required for namespaced mode
                if not self.args.apps or self.args.apps.strip() == "":
                    self.fatalError("apps must be set for namespaced permission mode")
                self.apps = self.args.apps.strip()

            selectedApps = [app.strip().lower() for app in self.apps.split(",") if app.strip()]
            invalidApps = sorted({app for app in selectedApps if app not in VALID_PREINSTALL_APPS})
            if invalidApps:
                self.fatalError(f"Unsupported app value(s): {', '.join(invalidApps)}. " f"Supported apps are: {', '.join(sorted(VALID_PREINSTALL_APPS))}")
        else:
            # For cluster mode, set empty apps list
            selectedApps = []

        permissionResults = permissionCheckForRBAC(self.dynamicClient)
        hasAdminPermissions = all(result["allowed"] for result in permissionResults)
        if not hasAdminPermissions:
            self.fatalError(
                "You do not have the appropriate permissions to set up pre-install RBAC for MAS. Only a cluster administrator can perform this action."
            )

        self.printH1("MAS Pre-Install")
        self.printDescription(
            [
                "This will set up pre-install RBAC for MAS.",
                "",
                "This command is supported only for MAS version 9.2 and later.",
                "The RBAC that is applied is determined by the selected permission mode and apps.",
            ]
        )
        self.printSummary("Instance ID", self.mas_instance_id)
        self.printSummary("MAS Version", masVersion)
        self.printSummary("Permission Mode", self.permission_mode)
        if self.permission_mode == "namespaced":
            self.printSummary("Selected Apps", ", ".join(selectedApps))

        continueWithSetup = True
        if not self.noConfirm:
            print()
            self.printDescription(["Please carefully review your choices above before the RBAC setup begins."])
            continueWithSetup = self.yesOrNo("Proceed with these settings")

        if not continueWithSetup:
            self.fatalError("Pre-install RBAC setup aborted")

        with Halo(text=f"Setting up pre-install RBAC for MAS instance {self.mas_instance_id}...", spinner=self.spinner) as h:
            applyPreInstallMASRBAC(
                dynClient=self.dynamicClient,
                masVersion=masVersion,
                masInstanceId=self.mas_instance_id,
                permissionMode=self.permission_mode,
                selectedApps=selectedApps,
            )
            h.stop_and_persist(symbol=self.successIcon, text=f"Pre-install RBAC for MAS is ready for {self.mas_instance_id}")

        self.printDescription(["The pre-install RBAC for MAS has been set up."])
