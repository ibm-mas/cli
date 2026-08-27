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

from sys import exit
from prompt_toolkit import print_formatted_text, HTML
from halo import Halo

from ...cli import BaseApp
from ...gencfg import ConfigGeneratorMixin
from .argBuilder import McpiInstallArgBuilderMixin
from .argParser import mcpiInstallArgParser
from .summarizer import McpiInstallSummarizerMixin
from .params import requiredParams, optionalParams

from ...install.settings import InstallSettingsMixin

from mas.devops.ocp import createNamespace
from mas.devops.tekton import (
    installOpenShiftPipelines,
    updateTektonDefinitions,
    prepareMcpiPipelinesNamespace,
    prepareInstallSecrets,
    testCLI,
    launchMcpiInstallPipeline,
)

logger = logging.getLogger(__name__)


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> McpiInstallApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< McpiInstallApp.{func.__name__}")
        return result

    return wrapper


class McpiInstallApp(BaseApp, McpiInstallArgBuilderMixin, McpiInstallSummarizerMixin, InstallSettingsMixin, ConfigGeneratorMixin):
    """CLI App for installing Maximo Cluster Performance Insights (MCPI)."""

    @logMethodCall
    def configMcpi(self) -> None:
        """Prompt for MCPI-specific settings in interactive mode."""
        self.printH1("MCPI Configuration")
        self.promptForString("MAS instance ID", "mas_instance_id")
        self.promptForString("MCPI subscription channel", "mcpi_channel")

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        """Process all CLI arguments for non-interactive install.

        Raises:
            SystemExit: If a required parameter is missing or invalid.
        """
        self.isInteractiveMode = False
        self.storageClassProvider = "custom"
        self.slsLicenseFileLocal = None

        for key, value in vars(self.args).items():
            if key in requiredParams:
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.setParam(key, value)

            elif key in optionalParams:
                if value is not None:
                    self.setParam(key, value)

            elif key == "license_file":
                if value is not None and value != "":
                    self.slsLicenseFileLocal = value
                    self.setParam("sls_action", "install")

            elif key == "dedicated_sls":
                if value:
                    self.setParam("sls_namespace", f"mas-{self.args.mas_instance_id}-sls")

            elif key == "storage_accessmode":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageAccessMode = value

            elif key == "storage_pipeline":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageClass = value

            elif key == "additional_configs":
                self.localConfigDir = value

            elif key == "mongodb_namespace":
                if value is not None and value != "":
                    self.setParam(key, value)
                    self.setParam("sls_mongodb_cfg_file", f"/workspace/configs/mongo-{value}.yml")

            elif key in [
                "accept_license",
                "dev_mode",
                "skip_pre_check",
                "no_confirm",
                "help",
                "advanced",
                "simplified",
            ]:
                pass

            else:
                self.fatalError(f"Unknown option: {key} {value}")

        if self.slsLicenseFileLocal is None:
            self.fatalError("--license-file must be set for new SLS install")

    @logMethodCall
    def install(self, argv) -> int:
        """Install Maximo Cluster Performance Insights.

        Args:
            argv (list): Command-line arguments to parse.

        Returns:
            int: Exit code (0 on success).
        """
        args = mcpiInstallArgParser.parse_args(args=argv)

        instanceId = args.mas_instance_id
        self.noConfirm = args.no_confirm
        self.licenseAccepted = args.accept_license
        self.devMode = args.dev_mode

        if args.image_pull_policy and args.image_pull_policy != "":
            self.setParam("image_pull_policy", args.image_pull_policy)

        if args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        self.args = args

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            self.connect()
        else:
            logger.debug("MAS instance ID is set, assuming already connected to the desired OCP cluster")
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: Not successfully connected to a Kubernetes cluster.  See log file for details</Red>"))
            exit(1)

        self.isAirgap()

        self.setParam("dro_action", "install")

        if instanceId is None:
            self.interactiveMode(simplified=args.simplified, advanced=args.advanced)
        else:
            self.nonInteractiveMode()

        self.slsLicenseFile()

        self.printH1("Non-Interactive Install Command")
        self.printDescription(
            ["Save and re-use the following script to re-run this install without needing to answer the interactive prompts again", "", self.buildCommand()]
        )

        self.displayInstallSummary()

        if not self.noConfirm:
            print()
            self.printDescription(["Please carefully review your choices above, correcting mistakes now is much easier than after the install has begun"])
            continueWithInstall = self.yesOrNo("Proceed with these settings")

        if self.noConfirm or continueWithInstall:
            self.createTektonFileWithDigest()

            self.printH1("Launch Install")
            pipelinesNamespace = f"mcpi-{self.getParam('mas_instance_id')}-pipelines"

            with Halo(text="Validating OpenShift Pipelines installation", spinner=self.spinner) as h:
                if installOpenShiftPipelines(self.dynamicClient, self.getParam("storage_class_rwx")):
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")
                else:
                    h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator installation failed")
                    self.fatalError("Installation failed")

            with Halo(text=f"Preparing namespace ({pipelinesNamespace})", spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                prepareMcpiPipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("mas_instance_id"),
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                    configureRBAC=(self.getParam("service_account_name") == ""),
                )
                prepareInstallSecrets(
                    dynClient=self.dynamicClient,
                    namespace=pipelinesNamespace,
                    slsLicenseFile=self.slsLicenseFileSecret,
                    additionalConfigs=self.additionalConfigsSecret,
                    podTemplates=self.podTemplatesSecret,
                    certs=self.certsSecret,
                    slack_token=self.getParam("slack_token"),
                    slack_channel=self.getParam("slack_channel"),
                )
                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text="Testing availability of MAS CLI image in cluster", spinner=self.spinner) as h:
                testCLI()
                h.stop_and_persist(symbol=self.successIcon, text="MAS CLI image deployment test completed")

            with Halo(text=f"Installing latest Tekton definitions (v{self.version})", spinner=self.spinner) as h:
                updateTektonDefinitions(self.dynamicClient, pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text=f"Submitting PipelineRun for {self.getParam('mas_instance_id')} MCPI install", spinner=self.spinner) as h:
                pipelineURL = launchMcpiInstallPipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {self.getParam('mas_instance_id')} install submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(
                        symbol=self.failureIcon,
                        text=f"Failed to submit PipelineRun for {self.getParam('mas_instance_id')} install, see log file for details",
                    )
                    print()

        return 0
