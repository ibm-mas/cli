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

    def promptForMASChannel(self) -> None:
        self.printH2("MAS Channel")
        self.printDescription(["Enter the MAS channel", "For example: 9.2.x"])
        self.mas_channel = self.promptForString("MAS Channel", default="9.2.x")

    def promptForAdminMode(self) -> None:
        self.printH2("Admin Mode")
        self.printDescription(
            [
                "Choose the admin mode for which pre-install RBAC should be set up:",
                "",
                "  1. cluster",
                "  2. namespaced",
            ]
        )
        adminModeInt = self.promptForInt("Admin Mode", default=1, min=1, max=2)
        adminModeMap = {1: "cluster", 2: "namespaced"}
        self.admin_mode = adminModeMap[adminModeInt]

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
        self.interactive_mode = not all([self.args.mas_instance_id, self.args.mas_channel, self.args.admin_mode])

        self.printH1("Set Target OpenShift Cluster")
        self.connect()

        if self.interactive_mode:

            if self.args.mas_instance_id is not None:
                self.mas_instance_id = self.args.mas_instance_id
            else:
                self.promptForMASInstanceId()

            if self.args.mas_channel is not None:
                self.mas_channel = self.args.mas_channel.strip()
            else:
                self.promptForMASChannel()

            if self.args.admin_mode is not None:
                self.admin_mode = self.args.admin_mode.strip()
            else:
                self.promptForAdminMode()
        else:
            # Non-interactive mode - validate required parameters
            if not self.args.mas_instance_id or self.args.mas_instance_id.strip() == "":
                self.fatalError("mas_instance_id must be set")
            if not self.args.mas_channel or self.args.mas_channel.strip() == "":
                self.fatalError("mas_channel must be set")
            if not self.args.admin_mode or self.args.admin_mode.strip() == "":
                self.fatalError("admin_mode must be set")

            self.mas_instance_id = self.args.mas_instance_id.strip()
            self.mas_channel = self.args.mas_channel.strip()
            self.admin_mode = self.args.admin_mode.strip()

        if self.admin_mode == "minimal":
            self.printH1("Minimal Admin Mode")
            self.printDescription(
                [
                    "Minimal admin mode does not require pre-install RBAC setup.",
                    "",
                    "In minimal mode, essential roles are installed by each operator during installation.",
                ]
            )
            return
        # Extract major.minor version from channel
        # Channel can be in formats like: 9.2.x, 9.2.0, 9.2.x-pre, etc.
        masVersion = ".".join(self.mas_channel.split(".")[:2])

        # Validate minimum version requirement
        channelVersion = f"{masVersion}.0"
        if not isVersionEqualOrAfter("9.2.0", channelVersion):
            self.fatalError("mas pre-install is supported only for MAS channel 9.2.x and later")

        # Only prompt for apps in namespaced mode
        if self.admin_mode == "namespaced":
            if self.interactive_mode:
                if self.args.apps is not None:
                    self.apps = self.args.apps.strip()
                else:
                    self.promptForApps()
            else:
                # In non-interactive mode, apps is required for namespaced mode
                if not self.args.apps or self.args.apps.strip() == "":
                    self.fatalError("apps must be set for namespaced admin mode")
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
                "The RBAC that is applied is determined by the selected Admin mode and apps.",
            ]
        )
        self.printSummary("Instance ID", self.mas_instance_id)
        self.printSummary("MAS Channel", self.mas_channel)
        self.printSummary("Admin Mode", self.admin_mode)
        if self.admin_mode == "namespaced":
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
                adminMode=self.admin_mode,
                selectedApps=selectedApps,
            )
            h.stop_and_persist(symbol=self.successIcon, text=f"Pre-install RBAC for MAS is ready for {self.mas_instance_id}")

        self.printDescription(["The pre-install RBAC for MAS has been set up."])
