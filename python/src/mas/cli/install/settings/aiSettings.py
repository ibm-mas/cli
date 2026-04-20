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
from base64 import b64decode


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
        templatesDir: str
        dynamicClient: Any
        installAIService: bool

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

    def _detectAiServiceFromCluster(self) -> Dict[str, str]:
        """
        Auto-detect AI Service connection details from the cluster.
        Returns a dictionary with: url, tenant_id, apikey, certificate
        """
        try:
            aiservice_instance_id = self.getParam('aiservice_instance_id')
            aiservice_tenant_id = self.getParam('aiservice_tenant_id') or "user"
            aiservice_channel = self.getParam('aiservice_channel')

            if not aiservice_instance_id:
                return {}

            # Set namespaces
            aiservice_namespace = f"aiservice-{aiservice_instance_id}"
            aiservice_tenant_name = f"aiservice-{aiservice_instance_id}-{aiservice_tenant_id}"

            # Determine tenant namespace based on channel
            if aiservice_channel and aiservice_channel.startswith('9.1.'):
                aiservice_tenant_namespace = aiservice_namespace
            else:
                aiservice_tenant_namespace = aiservice_tenant_name

            print_formatted_text("\nAuto-detecting AI Service details from cluster...")
            print_formatted_text(f"  AI Service namespace: {aiservice_namespace}")
            print_formatted_text(f"  Tenant namespace: {aiservice_tenant_namespace}")

            # 1. Get API Key from secret
            secret_name = f"{aiservice_tenant_name}----apikey-secret"
            try:
                secret = self.dynamicClient.resources.get(api_version='v1', kind='Secret')
                apikey_secret = secret.get(name=secret_name, namespace=aiservice_tenant_namespace)
                apikey = b64decode(apikey_secret.data['AIBROKER_APIKEY']).decode('utf-8')
                print_formatted_text(f"  ✓ API key retrieved from secret: {secret_name}")
            except Exception as e:
                print_formatted_text(f"  ✗ Failed to retrieve API key: {str(e)}")
                return {}

            # 2. Get URL from route
            try:
                route = self.dynamicClient.resources.get(api_version='route.openshift.io/v1', kind='Route')
                aibroker_route = route.get(name='aibroker', namespace=aiservice_namespace)
                url = f"https://{aibroker_route.spec.host}/ibm/aibroker/service/rest/api/v1"
                print_formatted_text(f"  ✓ URL retrieved from route: {url}")
            except Exception as e:
                print_formatted_text(f"  ✗ Failed to retrieve URL: {str(e)}")
                return {}

            # 3. Get TLS certificate from secret
            tls_secret_name = f"{aiservice_instance_id}-public-aibroker-tls"
            try:
                tls_secret = secret.get(name=tls_secret_name, namespace=aiservice_namespace)
                certificate = b64decode(tls_secret.data['ca.crt']).decode('utf-8')
                print_formatted_text(f"  ✓ Certificate retrieved from secret: {tls_secret_name}")
            except Exception as e:
                print_formatted_text(f"  ✗ Failed to retrieve certificate: {str(e)}")
                return {}

            print_formatted_text("\n✓ Successfully auto-detected all AI Service details\n")

            return {
                'url': url,
                'tenant_id': aiservice_tenant_name,
                'apikey': apikey,
                'certificate': certificate
            }

        except Exception as e:
            print_formatted_text(f"\n✗ Error during auto-detection: {str(e)}\n")
            return {}

    def _generateAiCfgWithValues(self, instanceId: str, scope: str, destination: str, workspaceId: str,
                                 url: str, tenantId: str, apikey: str, certificate: str,
                                 enabled: bool, metaAgentEnabled: bool, sslEnabled: bool) -> None:
        """
        Generate AiCfg file with provided values (used for auto-detection).
        """
        from jinja2 import Template

        templateFile = path.join(self.templatesDir, "aicfg.yml.j2")
        with open(templateFile) as tFile:
            template = Template(tFile.read())

        cfg = template.render(
            scope=scope,
            mas_instance_id=instanceId,
            mas_workspace_id=workspaceId,
            cfg_display_name="AI Service Configuration",
            ai_url=url,
            ai_tenant_id=tenantId,
            ai_apikey=apikey,
            ai_enabled=enabled,
            meta_agent_enabled=metaAgentEnabled,
            ai_ssl_enabled=sslEnabled,
            ai_cert_local_file_content=certificate
        )

        with open(destination, 'w') as f:
            f.write(cfg)
            f.write('\n')

    def configAi(self, silentMode=False) -> None:
        """Configure AiCfg for MAS installation"""
        if not silentMode:
            self.printH1("Configure AiCfg")
            self.printDescription([
                "The installer can configure AiCfg integration for your MAS instance.",
                "AiCfg provides AI/ML capabilities for MAS applications like Manage, Monitor, and Predict.",
                "AiCfg is configured at system scope and available to all workspaces."
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
        workspaceId = self.getParam('mas_workspace_id')

        # AiCfg is always configured at system scope
        scope = "system"
        self.setParam("ai_scope", "system")

        # Check if AI Service is being installed on the same cluster
        if hasattr(self, 'installAIService') and self.installAIService:
            # Auto-detect AI Service details from cluster
            if not silentMode:
                self.printH2("AiCfg Configuration (Auto-Detection)")
                self.printDescription([
                    "AI Service is being installed on this cluster.",
                    "The installer will automatically detect connection details from the cluster.",
                    "",
                    "IMPORTANT: The AiCfg file must be applied AFTER the MAS Core operator is installed,",
                    "as the AiCfg CRD is created by the operator (not during initial config phase).",
                    "Do NOT include this file in the initial configuration directory.",
                    "Apply it after the operator creates the CRD."
                ])

            createAiConfig = True
            if not silentMode:
                createAiConfig = self.yesOrNo("Generate AiCfg configuration file (apply after operator install)")

            if createAiConfig:
                self.setParam("ai_action", "configure")
                self.selectLocalConfigDir()
                assert self.localConfigDir is not None, "localConfigDir must be set"

                aiCfgFile = path.join(self.localConfigDir, f"aicfg-{instanceId}-system.yaml")

                # Try to auto-detect from cluster
                detected_config = self._detectAiServiceFromCluster()

                if detected_config:
                    # Use detected values
                    print_formatted_text("\nUsing auto-detected AI Service configuration:")
                    print_formatted_text(f"  URL: {detected_config['url']}")
                    print_formatted_text(f"  Tenant ID: {detected_config['tenant_id']}")
                    print_formatted_text("  API Key: " + ('*' * 32))
                    print_formatted_text("  Certificate: Retrieved")
                    print_formatted_text("  Enabled: true (default)")
                    print_formatted_text("  Meta Agent: true (default)")
                    print_formatted_text("  SSL Enabled: true (default)\n")

                    # Generate AiCfg with detected values
                    self._generateAiCfgWithValues(
                        instanceId=instanceId,
                        scope=scope,
                        destination=aiCfgFile,
                        workspaceId=workspaceId,
                        url=detected_config['url'],
                        tenantId=detected_config['tenant_id'],
                        apikey=detected_config['apikey'],
                        certificate=detected_config['certificate'],
                        enabled=True,
                        metaAgentEnabled=True,
                        sslEnabled=True
                    )

                    print_formatted_text(f"\n✓ AiCfg configuration file created: {aiCfgFile}")
                    print_formatted_text("This configuration will be applied during MAS installation.")
                else:
                    print_formatted_text("\n⚠ Auto-detection failed. Falling back to manual configuration.\n")
                    # Fall back to manual configuration
                    self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)
            else:
                self.setParam("ai_action", "none")
                print_formatted_text("AiCfg configuration skipped")
        else:
            # Manual configuration for external AI Service
            if not silentMode:
                self.printH2("AiCfg Configuration")
                self.printDescription([
                    "You can provide connection details for an existing AI Service instance.",
                    "The installer will generate the AiCfg YAML file with your connection details.",
                    "",
                    "IMPORTANT: The AiCfg file must be applied AFTER the MAS Core operator is installed,",
                    "as the AiCfg CRD is created by the operator (not during initial config phase).",
                    "Do NOT include this file in the initial configuration directory.",
                    "Apply it after the operator creates the CRD."
                ])

            createAiConfig = True
            if not silentMode:
                createAiConfig = self.yesOrNo("Generate AiCfg configuration file (apply after operator install)")

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
                    if self.yesOrNo("AiCfg configuration file already exists. Do you want to generate a new one"):
                        self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)
                else:
                    print_formatted_text(f"Expected file ({aiCfgFile}) was not found, generating a valid AiCfg configuration file now ...")
                    self.generateAiCfg(instanceId=instanceId, scope=scope, destination=aiCfgFile, workspaceId=workspaceId)

                print_formatted_text(f"\nAiCfg configuration file created: {aiCfgFile}")
                print_formatted_text("This configuration will be applied during MAS installation.")
            else:
                self.setParam("ai_action", "none")
                print_formatted_text("AiCfg configuration skipped")
