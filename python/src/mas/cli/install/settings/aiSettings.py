# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from os import path
from typing import TYPE_CHECKING, Dict, List, Any
from prompt_toolkit import print_formatted_text


if TYPE_CHECKING:
    # Type hints for methods and attributes provided by other mixins
    # These are only used during type checking and have no runtime cost
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.validation import Validator


class AiSettingsMixin():
    if TYPE_CHECKING:
        # Attributes from BaseApp and other mixins
        params: Dict[str, str]
        devMode: bool
        showAdvancedOptions: bool
        localConfigDir: str | None

        # Methods from BaseApp
        def setParam(self, param: str, value: str) -> None:
            ...

        def getParam(self, param: str) -> str:
            ...

        # Methods from PrintMixin
        def printH1(self, message: str) -> None:
            ...

        def printH2(self, message: str) -> None:
            ...

        def printDescription(self, content: List[str]) -> None:
            ...

        # Methods from PromptMixin
        def yesOrNo(self, message: str, param: str | None = None) -> bool:
            ...

        def promptForString(
            self,
            message: str,
            param: str | None = None,
            default: str = "",
            isPassword: bool = False,
            validator: Validator | None = None,
            completer: WordCompleter | None = None
        ) -> str:
            ...

        def promptForListSelect(
            self,
            message: str,
            options: List[str],
            param: str | None = None,
            default: int | None = None
        ) -> str:
            ...

        # Methods from ConfigGeneratorMixin or InstallSettingsMixin
        def selectLocalConfigDir(self) -> None:
            ...

        def generateAiCfg(self, instanceId: str, scope: str, destination: str, workspaceId: str = "") -> None:
            ...

    def configAi(self, silentMode=False) -> None:
        """Configure AiCfg for MAS installation"""
        if not silentMode:
            self.printH1("Configure AiCfg")
            self.printDescription([
                "The installer can configure AiCfg integration for your MAS instance.",
                "AiCfg provides AI/ML capabilities for MAS applications like Manage, Monitor, and Predict.",
                "You can configure AiCfg at system scope or workspace scope."
            ])

        # Ask if user wants to configure AiCfg
        configureAi = True
        if not silentMode:
            configureAi = self.yesOrNo("Do you want to configure AiCfg")

        if not configureAi:
            self.setParam("ai_action", "none")
            print_formatted_text("AiCfg configuration skipped")
            return

        instanceId = self.getParam('mas_instance_id')

        # Determine scope
        if not silentMode:
            self.printH2("AiCfg Configuration Scope")
            self.printDescription([
                "AiCfg can be configured at different scopes:",
                " - System scope: Available to all workspaces",
                " - Workspace scope: Available to a specific workspace only"
            ])

        useSystemScope = True
        if not silentMode:
            useSystemScope = self.yesOrNo("Configure AiCfg at system scope (recommended)")

        if useSystemScope:
            scope = "system"
            workspaceId = ""
            self.setParam("ai_scope", "system")
        else:
            scope = "workspace"
            workspaceId = self.getParam("mas_workspace_id")
            self.setParam("ai_scope", "workspace")

        # Check if user wants to provide existing AiCfg or create configuration
        if not silentMode:
            self.printH2("AiCfg Configuration")
            self.printDescription([
                "You can provide connection details for an existing AI Service instance.",
                "The installer will create the necessary AiCfg custom resource."
            ])

        createAiConfig = True
        if not silentMode:
            createAiConfig = self.yesOrNo("Create AiCfg configuration")

        if createAiConfig:
            self.setParam("ai_action", "configure")

            self.selectLocalConfigDir()

            # Check if a configuration already exists before creating a new one
            assert self.localConfigDir is not None, "localConfigDir must be set"

            if scope == "system":
                aiCfgFile = path.join(self.localConfigDir, f"aicfg-{instanceId}-system.yaml")
                print_formatted_text(f"Searching for AiCfg configuration file in {aiCfgFile} ...")
            else:
                aiCfgFile = path.join(self.localConfigDir, f"aicfg-{instanceId}-{workspaceId}.yaml")
                print_formatted_text(f"Searching for AiCfg configuration file in {aiCfgFile} ...")

            if path.exists(aiCfgFile):
                if self.yesOrNo(f"AiCfg configuration file already exists. Do you want to generate a new one"):
                    self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)
            else:
                print_formatted_text(f"Expected file ({aiCfgFile}) was not found, generating a valid AiCfg configuration file now ...")
                self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)

            print_formatted_text(f"\nAiCfg configuration file created: {aiCfgFile}")
            print_formatted_text("This configuration will be applied during MAS installation.")
        else:
            self.setParam("ai_action", "none")
            print_formatted_text("AiCfg configuration skipped")

# Made with Bob
