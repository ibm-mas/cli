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

from ..cli import BaseApp
from .argParser import setupRBACArgParser
from mas.devops.tekton import prepareInstallRBAC

logger = logging.getLogger(__name__)


class SetupRBACApp(BaseApp):
    def setupRBAC(self, argv):
        """
        Create the minimal install RBAC resources for MAS installation.
        This is intended to be used in cases where the user does not have permissions to create RBAC resources in the cluster.
        The cluster admin create the necessary RBAC resources for them before they run the install command.
        """
        self.args = setupRBACArgParser().parse_args(args=argv)
        self.noConfirm = self.args.no_confirm

        self.printH1("Set Target OpensShift Cluster")
        self.connect()

        instanceId = self.args.mas_instance_id
        installUserSA = f"mas-{instanceId}-install-user"
        installPipelineSA = f"mas-{instanceId}-install-pipeline"
        pipelineNamespace = f"mas-{instanceId}-pipelines"

        self.printH1("Create RBAC resources for MAS installation")
        self.printDescription(["This will apply the minimal install RBAC bundle for the target MAS instance."
                               "",
                               "The bundle creates the fine-grained service accounts used to run 'mas install' and the install pipeline."])
        self.printSummary("Instance ID", instanceId)
        self.printSummary("Install Pipeline Namespace", pipelineNamespace)
        self.printSummary("Install User Service Account", installUserSA)
        self.printSummary("Install Pipeline Service Account", installPipelineSA)

        with Halo(text=f"Applying RBAC resources for {instanceId}...", spinner=self.spinner) as h:
            prepareInstallRBAC(
                dynClient=self.dynClient,
                namespace=pipelineNamespace,
                instanceId=instanceId,
                installRBACDir=self.installRBACDir
            )
            h.stop_and_persist(symbol=self.successIcon, text=f"Install RBAC is ready for {instanceId}")

        self.printH1("Next Steps")
        self.printDescription(["The RBAC resources for the install pipeline have been created. "
                               "Use the service accounts created by this command to run MAS install without relying on cluster-admin permissions."])
        self.printHighlight([
            f"1. Log in using the '{installUserSA}' service account token",
            f"2. Run 'mas install' with the '--service-account {installPipelineSA}' flag to use the '{installPipelineSA}' service account for the install pipeline"
        ])
