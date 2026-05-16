# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from typing import TYPE_CHECKING, List, NoReturn
from os import path
from base64 import b64encode
from glob import glob
from prompt_toolkit import print_formatted_text

import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ..context import InstallContext


class AdditionalConfigsMixin:
    if TYPE_CHECKING:
        # Context object with all state
        context: InstallContext

        # Methods from PrintMixin
        def printH1(self, message: str) -> None: ...  # noqa: E704

        def printH2(self, message: str) -> None: ...  # noqa: E704

        def printDescription(self, content: List[str]) -> None: ...  # noqa: E704

        # Methods from PromptMixin
        def yesOrNo(
            self, message: str, param: str | None = None
        ) -> bool: ...  # noqa: E704

        def promptForInt(  # noqa: E704
            self,
            message: str,
            param: str | None = None,
            default: int | None = None,
            min: int | None = None,
            max: int | None = None,
        ) -> int: ...

        def promptForDir(  # noqa: E704
            self, message: str, mustExist: bool = True, default: str = ""
        ) -> str: ...

        def fatalError(  # noqa: E704
            self, message: str, exception: Exception | None = None
        ) -> NoReturn: ...

        # Methods from other mixins
        def selectLocalConfigDir(self) -> None: ...  # noqa: E704

        def selectOne(self, message: str, options: List[str]) -> str: ...  # noqa: E704

    def additionalConfigs(self) -> None:
        if self.context.isInteractiveMode:
            self.printH1("Additional Configuration")
            self.printDescription(
                [
                    "Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step",
                    "The primary purpose of this is to apply configuration for Maximo Application Suite itself, but you can use this to deploy ANY additional resource into your cluster",
                ]
            )

            # If the user already set up BYO MongoDb or Kafka then they have already chosen to use additional configs
            if self.context.localConfigDir is None:
                if self.yesOrNo("Use additional configurations"):
                    self.selectLocalConfigDir()

        # If we've set up a local config directory then provide details about what's included in it
        # and generate the secret that will be used in the pipeline
        if self.context.localConfigDir is not None:
            # Get list of files in localConfigDir
            configFilesPath = rf"{self.context.localConfigDir}/*.yaml"
            configFiles = glob(configFilesPath)
            if len(configFiles) == 0:
                self.fatalError(
                    f"No configuration files (*.yaml) were found in {self.context.localConfigDir}"
                )

            print_formatted_text(
                "The following additional configurations will be applied:"
            )
            for cf in configFiles:
                print_formatted_text(f" - {path.basename(cf)}")

            if not self.context.noConfirm:
                if not self.yesOrNo(
                    "Are these the correct configuration files to apply"
                ):
                    print_formatted_text(
                        "Additional configuration files were not confirmed.  Aborting installation"
                    )
                    exit(0)

            # Generate the secret and apply it to the cluster
            secret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-additional-configs"},
            }
            additionalConfigsSecret = self.addFilesToSecret(
                secret, self.context.localConfigDir, "yaml"
            )
            logger.debug(additionalConfigsSecret)
            self.context.additionalConfigsSecret = additionalConfigsSecret

    def podTemplates(self) -> None:
        if self.context.isInteractiveMode and self.context.showAdvancedOptions:
            self.printH1("Configure Pod Templates")
            self.printDescription(
                [
                    "The CLI supports two pod template profiles out of the box that allow you to reconfigure MAS for either a guaranteed or best effort QoS level",
                    "For more information about the Kubernetes quality of service (QoS) levels, see <Orange><u>https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/</u></Orange>",
                    "You may also choose to use your own customized pod template definitions",
                ]
            )

            if not self.yesOrNo("Use pod templates"):
                return

            self.printDescription(
                [
                    "Make a selection from the list below:",
                    "",
                    "1. Guaranteed QoS",
                    "2. Best Effort QoS",
                    "3. Custom",
                ]
            )

            podTemplateChoice = self.promptForInt("Select pod templates profile")

            if podTemplateChoice == 1:
                self.context.setParam(
                    "mas_pod_templates_dir",
                    path.join(self.context.templatesDir, "pod-templates", "guaranteed"),
                )
            elif podTemplateChoice == 2:
                self.context.setParam(
                    "mas_pod_templates_dir",
                    path.join(
                        self.context.templatesDir, "pod-templates", "best-effort"
                    ),
                )
            elif podTemplateChoice == 3:
                self.context.setParam(
                    "mas_pod_templates_dir",
                    self.promptForDir("Pod templates directory", mustExist=True),
                )
            else:
                self.fatalError(f"Invalid selection: {podTemplateChoice}")

        if self.context.getParam("mas_pod_templates_dir") != "":
            templateFilesPath = (
                rf'{self.context.getParam("mas_pod_templates_dir")}/*.yml'
            )
            templateFiles = glob(templateFilesPath)
            if len(templateFiles) == 0:
                self.fatalError(
                    f"No pod templates (*.yml) were found in {self.context.getParam('mas_pod_templates_dir')}"
                )

            print_formatted_text("The following pod templates will be applied:")
            for tf in templateFiles:
                print_formatted_text(f" - {path.basename(tf)}")

            if not self.context.noConfirm:
                if not self.yesOrNo("Are these the correct pod templates to apply"):
                    print_formatted_text(
                        "Pod templates were not confirmed.  Aborting installation"
                    )
                    exit(0)

            # Generate the secret and apply it to the cluster
            secret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-pod-templates"},
            }
            podTemplatesSecret = self.addFilesToSecret(
                secret, self.context.getParam("mas_pod_templates_dir"), "yml"
            )
            logger.debug(podTemplatesSecret)
            self.context.podTemplatesSecret = podTemplatesSecret

    def manualCertificates(self) -> None:

        if self.context.getParam("mas_manual_cert_mgmt").lower() == "true":
            certsSecret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-certificates"},
            }

            extensions = ["key", "crt"]

            manualCertsDir = self.context.manualCertsDir
            if manualCertsDir is None:
                self.fatalError("Manual certificates directory is not set")

            apps = {
                "mas_app_channel_assist": {
                    "dir": manualCertsDir + "/assist/",
                    "keyPrefix": "assist.",
                },
                "mas_app_channel_manage": {
                    "dir": manualCertsDir + "/manage/",
                    "keyPrefix": "manage.",
                },
                "mas_app_channel_iot": {
                    "dir": manualCertsDir + "/iot/",
                    "keyPrefix": "iot.",
                },
                "mas_app_channel_monitor": {
                    "dir": manualCertsDir + "/monitor/",
                    "keyPrefix": "monitor.",
                },
                "mas_app_channel_predict": {
                    "dir": manualCertsDir + "/predict/",
                    "keyPrefix": "predict.",
                },
                "mas_app_channel_visualinspection": {
                    "dir": manualCertsDir + "/visualinspection/",
                    "keyPrefix": "visualinspection.",
                },
                "mas_app_channel_optimizer": {
                    "dir": manualCertsDir + "/optimizer/",
                    "keyPrefix": "optimizer.",
                },
                "mas_app_channel_facilities": {
                    "dir": manualCertsDir + "/facilities/",
                    "keyPrefix": "facilities.",
                },
            }

            for file in ["ca.crt", "tls.crt", "tls.key"]:
                if file not in map(path.basename, glob(f"{manualCertsDir}/core/*")):
                    self.fatalError(f"{file} is not present in {manualCertsDir}/core/")
            for ext in extensions:
                certsSecret = self.addFilesToSecret(
                    certsSecret, manualCertsDir + "/core/", ext, "core."
                )

            for app in apps:
                if self.context.getParam(app) != "":
                    for file in ["ca.crt", "tls.crt", "tls.key"]:
                        if file not in map(
                            path.basename, glob(f'{apps[app]["dir"]}/*')
                        ):
                            self.fatalError(
                                f'{file} is not present in {apps[app]["dir"]}'
                            )
                    for ext in extensions:
                        certsSecret = self.addFilesToSecret(
                            certsSecret, apps[app]["dir"], ext, apps[app]["keyPrefix"]
                        )

            self.context.certsSecret = certsSecret

    def slsLicenseFile(self) -> None:
        if self.context.slsLicenseFileLocal:
            slsLicenseFileSecret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-sls-entitlement"},
            }
            self.context.setParam(
                "sls_entitlement_file",
                f"/workspace/entitlement/{path.basename(self.context.slsLicenseFileLocal)}",
            )
            self.context.slsLicenseFileSecret = self.addFilesToSecret(
                slsLicenseFileSecret, self.context.slsLicenseFileLocal, ""
            )

    def aiserviceConfig(self) -> None:
        self.context.aiserviceConfigSecret = None

        if self.context.aiserviceTenantSchedulingConfigFileLocal:
            from typing import Any

            aiserviceConfigSecret: dict[str, Any] = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-aiservice-config"},
            }
            self.context.setParam(
                "tenant_scheduling_config_file",
                f"/workspace/aiservice/{path.basename(self.context.aiserviceTenantSchedulingConfigFileLocal)}",
            )
            self.context.aiserviceConfigSecret = self.addFilesToSecret(
                aiserviceConfigSecret,
                self.context.aiserviceTenantSchedulingConfigFileLocal,
                "yaml",
            )

    def db2LicenseFile(self) -> None:
        if self.context.db2LicenseFileLocal:
            db2LicenseFileSecret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {"name": "pipeline-db2-license"},
            }
            self.context.setParam(
                "db2_license_file",
                f"/workspace/db2/{path.basename(self.context.db2LicenseFileLocal)}",
            )
            self.context.db2LicenseFileSecret = self.addFilesToSecret(
                db2LicenseFileSecret, self.context.db2LicenseFileLocal, ""
            )
        else:
            self.context.db2LicenseFileSecret = None

    def addFilesToSecret(
        self, secretDict: dict, configPath: str, extension: str, keyPrefix: str = ""
    ) -> dict:
        """
        Add file (or files) to pipeline-additional-configs
        """
        filesToProcess = []
        if path.isdir(configPath):
            logger.debug(f"Adding all config files in directory {configPath}")
            filesToProcess = glob(f"{configPath}/*.{extension}")
        else:
            logger.debug(f"Adding config file {configPath}")
            filesToProcess = [configPath]

        for fileToProcess in filesToProcess:
            logger.debug(f" * Processing config file {fileToProcess}")
            fileName = path.basename(fileToProcess)

            # Load the file
            with open(fileToProcess, "r") as file:
                data = file.read()

            # Add/update an entry to the secret data
            if "data" not in secretDict:
                secretDict["data"] = {}
            secretDict["data"][keyPrefix + fileName] = b64encode(
                data.encode("ascii")
            ).decode("ascii")

        return secretDict
