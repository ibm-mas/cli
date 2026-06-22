# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
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


class AiSettingsMixin:
    if TYPE_CHECKING:
        # Attributes from BaseApp and other mixins
        params: Dict[str, str]
        devMode: bool
        showAdvancedOptions: bool
        localConfigDir: str | None
        templatesDir: str
        dynamicClient: Any
        installAIService: bool

        # Methods from BaseApp
        def setParam(self, param: str, value: str) -> None: ...

        def getParam(self, param: str) -> str: ...

        # Methods from PrintMixin
        def printH1(self, message: str) -> None: ...

        def printH2(self, message: str) -> None: ...

        def printDescription(self, content: List[str]) -> None: ...

        # Methods from PromptMixin
        def yesOrNo(self, message: str, param: str | None = None) -> bool: ...

        def promptForString(
            self,
            message: str,
            param: str | None = None,
            default: str = "",
            isPassword: bool = False,
            validator: Validator | None = None,
            completer: WordCompleter | None = None,
        ) -> str: ...

        def promptForListSelect(self, message: str, options: List[str], param: str | None = None, default: int | None = None) -> str: ...

        # Methods from ConfigGeneratorMixin or InstallSettingsMixin
        def selectLocalConfigDir(self) -> None: ...

        def generateAiCfg(self, instanceId: str, scope: str, destination: str, workspaceId: str = "") -> None: ...

    def configAi(self) -> None:
        """Configure AiCfg for MAS installation"""

        # AiCfg is only supported in MAS 9.2+
        mas_channel = self.getParam("mas_channel")
        is_mas_92_or_later = False

        if mas_channel:
            try:
                # Extract major.minor version (e.g., "9.2" from "9.2.0")
                version_parts = mas_channel.split(".")
                if len(version_parts) >= 2:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    is_mas_92_or_later = (major > 9) or (major == 9 and minor >= 2)
            except (ValueError, IndexError):
                pass

        # If MAS 9.1 or earlier, force disable AiCfg regardless of user input
        if not is_mas_92_or_later:
            return

        self.printH1("Maximo AI Configuration")
        self.printDescription(
            [
                "The installer can configure AiCfg integration for your MAS instance.",
                "AiCfg provides AI/ML capabilities for MAS applications like Manage, Monitor, and Predict.",
                "AiCfg is configured at system scope and available to all workspaces.",
            ]
        )

        # Ask if user wants to configure AiCfg
        configureAi = self.yesOrNo("Do you want to configure AiCfg")

        if not configureAi:
            self.setParam("configure_aiassistant", "none")
            return

        instanceId = self.getParam("mas_instance_id")
        workspaceId = self.getParam("mas_workspace_id")

        # AiCfg is always configured at system scope
        scope = "system"
        self.setParam("ai_scope", "system")

        # Check if AI Service is being installed on the same cluster
        if hasattr(self, "installAIService") and self.installAIService:
            # Set action to indicate pipeline should handle it
            self.setParam("configure_aiassistant", "pipeline")
            print_formatted_text("\n✓ AiCfg will be automatically configured by the pipeline after AI Service installation")
        else:
            # Manual configuration for external AI Service
            createAiConfig = self.yesOrNo("Generate AiCfg configuration file (apply after operator install)")
            if createAiConfig:
                self.setParam("configure_aiassistant", "configure")
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
                    if self.yesOrNo("AiCfg configuration file already exists. Do you want to generate a new one"):
                        self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)
                else:
                    print_formatted_text(f"Expected file ({aiCfgFile}) was not found, generating a valid AiCfg configuration file now ...")
                    self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)

                print_formatted_text(f"\nAiCfg configuration file created: {aiCfgFile}")
                print_formatted_text("This configuration will be applied during MAS installation.")
            else:
                self.setParam("configure_aiassistant", "none")
                print_formatted_text("AiCfg configuration skipped")
