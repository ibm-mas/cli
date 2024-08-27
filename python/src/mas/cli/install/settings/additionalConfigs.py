# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from os import path
from base64 import b64encode
from glob import glob
from prompt_toolkit import print_formatted_text

import logging
logger = logging.getLogger(__name__)

class AdditionalConfigsMixin():
    def additionalConfigs(self) -> None:
        if self.interactiveMode:
            self.printH1("Additional Configuration")
            self.printDescription([
                "Additional resource definitions can be applied to the OpenShift Cluster during the MAS configuration step",
                "The primary purpose of this is to apply configuration for Maximo Application Suite itself, but you can use this to deploy ANY additional resource into your cluster"
            ])

            # If the user already set up BYO MongoDb or Kafka then they have already chosen to use additional configs
            if self.localConfigDir is None:
                if self.yesOrNo("Use additional configurations"):
                    self.selectLocalConfigDir()

        # If we've set up a local config directory then provide details about what's included in it
        # and generate the secret that will be used in the pipeline
        if self.localConfigDir is not None:
            # Get list of files in localConfigDir
            configFilesPath = rf'{self.localConfigDir}/*.yaml'
            configFiles = glob(configFilesPath)
            if len(configFiles) == 0:
                self.fatalError(f"No configuration files (*.yaml) were found in {self.localConfigDir}")

            print_formatted_text("The following additional configurations will be applied:")
            for cf in configFiles:
                print_formatted_text(f" - {path.basename(cf)}")

            if not self.noConfirm:
                if not self.yesOrNo("Are these the correct configuration files to apply"):
                    print_formatted_text("Additional configuration files were not confirmed.  Aborting installation")
                    exit(0)

            # Generate the secret and apply it to the cluster
            secret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {
                    "name": "pipeline-additional-configs"
                }
            }
            additionalConfigsSecret = self.addFilesToSecret(secret, self.localConfigDir, "yaml")
            logger.debug(additionalConfigsSecret)
            self.additionalConfigsSecret = additionalConfigsSecret

    def podTemplates(self) -> None:
        if self.interactiveMode:
            self.printH1("Configure Pod Templates")
            self.printDescription([
                "The CLI supports two pod template profiles out of the box that allow you to reconfigure MAS for either a guaranteed or best effort QoS level",
                "For more information about the Kubernetes quality of service (QoS) levels, see https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/",
                "You may also choose to use your own customized pod template definitions"
            ])

            if not self.yesOrNo("Use pod templates"):
                return

            self.printDescription([
                "Make a selection from the list below:",
                "",
                "1. Guaranteed QoS",
                "2. Best Effort QoS",
                "3. Custom"
            ])

            podTemplateChoice = self.promptForInt("Select pod templates profile")

            if podTemplateChoice == 1:
                self.setParam("mas_pod_templates_dir", path.join(self.templatesDir, "pod-templates", "guaranteed"))
            elif podTemplateChoice == 2:
                self.setParam("mas_pod_templates_dir", path.join(self.templatesDir, "pod-templates", "best-effort"))
            elif podTemplateChoice == 3:
                self.promptForDir("Pod templates directory", "mas_pod_templates_dir", mustExist=True)
            else:
                self.fatalError(f"Invalid selection: {podTemplateChoice}")

        if self.getParam("mas_pod_templates_dir") != "":
            templateFilesPath = rf'{self.getParam("mas_pod_templates_dir")}/*.yml'
            templateFiles = glob(templateFilesPath)
            if len(templateFiles) == 0:
                self.fatalError(f"No pod templates (*.yml) were found in {self.getParam('mas_pod_templates_dir')}")

            print_formatted_text("The following pod templates will be applied:")
            for tf in templateFiles:
                print_formatted_text(f" - {path.basename(tf)}")

            if not self.noConfirm:
                if not self.yesOrNo("Are these the correct pod templates to apply"):
                    print_formatted_text("Pod templates were not confirmed.  Aborting installation")
                    exit(0)

            # Generate the secret and apply it to the cluster
            secret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {
                    "name": "pipeline-pod-templates"
                }
            }
            podTemplatesSecret = self.addFilesToSecret(secret, self.getParam("mas_pod_templates_dir"), "yml")
            logger.debug(podTemplatesSecret)
            self.podTemplatesSecret = podTemplatesSecret

    def manualCertificates(self) -> None:

        if self.getParam("mas_manual_cert_mgmt"):
            certsSecret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "type": "Opaque",
                "metadata": {
                    "name": "pipeline-certificates"
                }
            }

            extensions = ["key", "crt"]

            apps = {
                "mas_app_channel_assist": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/assist/",
                        "keyPrefix": "assist."
                    },
                "mas_app_channel_manage": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/manage/",
                        "keyPrefix": "manage."
                    },
                "mas_app_channel_iot": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/iot/",
                        "keyPrefix": "iot."
                    },
                "mas_app_channel_monitor": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/monitor/",
                        "keyPrefix": "monitor."
                    },
                "mas_app_channel_predict": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/predict/",
                        "keyPrefix": "predict."
                    },
                "mas_app_channel_visualinspection": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/visualinspection/",
                        "keyPrefix": "visualinspection."
                    },
                "mas_app_channel_optimizer": {
                        "dir": self.getParam("mas_manual_cert_dir") + "/optimizer/",
                        "keyPrefix": "optimizer."
                    }
                }

            for file in ["ca.crt", "tls.crt", "tls.key"]:
                if file not in map(path.basename, glob(f'{self.getParam("mas_manual_cert_dir")}/core/*')):
                    self.fatalError(f'{file} is not present in {self.getParam("mas_manual_cert_dir")}/core/')
            for ext in extensions:
                certsSecret = self.addFilesToSecret(certsSecret, self.getParam("mas_manual_cert_dir")+'/core/', ext, "core.")

            for app in apps:
                if self.getParam(app) != "":
                    for file in ["ca.crt", "tls.crt", "tls.key"]:
                        if file not in map(path.basename, glob(f'{apps[app]["dir"]}/*')):
                            self.fatalError(f'{file} is not present in {apps[app]["dir"]}')
                    for ext in extensions:
                        certsSecret = self.addFilesToSecret(certsSecret, apps[app]["dir"], ext, apps[app]["keyPrefix"])

            self.certsSecret = certsSecret

    def addFilesToSecret(self, secretDict: dict, configPath: str, extension: str, keyPrefix: str='') -> dict:
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
            with open(fileToProcess, 'r') as file:
                data = file.read()

            # Add/update an entry to the secret data
            if "data" not in secretDict:
                secretDict["data"] = {}
            secretDict["data"][keyPrefix + fileName] = b64encode(data.encode('ascii')).decode("ascii")

        return secretDict