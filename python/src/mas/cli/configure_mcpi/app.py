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
from typing import Any, Dict, List
from halo import Halo
from kubernetes.dynamic.exceptions import NotFoundError

from ..cli import BaseApp
from ..validators import InstanceIDFormatValidator
from .argParser import configureMcpiArgParser
from mas.devops.mas import getMasChannel
from mas.devops.utils import isVersionEqualOrAfter

logger = logging.getLogger(__name__)


def buildMcpiCr(instanceId: str) -> Dict[str, Any]:
    """Build the McpiCfg CustomResource definition for an instance.

    Args:
        instanceId (str): The MAS instance ID

    Returns:
        dict: The McpiCfg custom resource dictionary
    """
    return {
        "apiVersion": "config.mas.ibm.com/v1",
        "kind": "McpiCfg",
        "metadata": {
            "name": f"{instanceId}-mcpi-system",
            "namespace": f"mas-{instanceId}-core",
            "labels": {
                "mas.ibm.com/configScope": "system",
                "mas.ibm.com/instanceId": instanceId,
            },
        },
        "spec": {
            "displayName": "Maximo Cluster Performance Insights",
            "config": {
                "enabled": True,
            },
        },
    }


class ConfigureMcpiApp(BaseApp):
    """CLI application to configure MCPI on an existing MAS instance."""

    def configureMcpi(self, argv: List[str]) -> None:
        """Configure Maximo Cluster Performance Insights on an existing MAS instance.

        Args:
            argv (list[str]): Command line arguments
        """
        self.args = configureMcpiArgParser.parse_args(args=argv)
        self.noConfirm = self.args.no_confirm

        self.printH1("Set Target OpenShift Cluster")
        self.connect()

        instanceId = self.args.mas_instance_id
        if instanceId is None or instanceId.strip() == "":
            self.printH2("MAS Instance")
            instanceId = self.promptForString("MAS Instance ID", validator=InstanceIDFormatValidator())

        instanceId = instanceId.strip()
        coreNamespace = f"mas-{instanceId}-core"

        self.printH1("Configure Maximo Cluster Performance Insights (MCPI)")
        self.printDescription(
            [
                "This will apply the McpiCfg resource to enable Maximo Cluster Performance Insights",
                f"for MAS instance '{instanceId}' in namespace '{coreNamespace}'.",
            ]
        )
        self.printSummary("MAS Instance ID", instanceId)
        self.printSummary("Target Namespace", coreNamespace)

        # Validate that the target namespace exists
        try:
            nsApi = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
            nsApi.get(name=coreNamespace)
        except NotFoundError:
            self.fatalError(f"Target namespace '{coreNamespace}' does not exist on this cluster. Verify the MAS instance ID.")

        # Validate MAS version (MCPI requires MAS 9.2+)
        channel = getMasChannel(self.dynamicClient, instanceId)
        if not channel:
            self.fatalError(f"Could not determine MAS channel for instance '{instanceId}'. Ensure MAS core is installed.")

        if not isVersionEqualOrAfter("9.2.0", channel):
            self.fatalError(f"MCPI requires MAS 9.2 or later (detected channel: {channel} for instance '{instanceId}').")

        self.printSummary("MAS Channel", channel)

        if not self.noConfirm:
            if not self.yesOrNo(f"Proceed with configuring MCPI for instance '{instanceId}'"):
                self.printDescription(["Configuration aborted by user."])
                return

        cr = buildMcpiCr(instanceId)
        crName = cr["metadata"]["name"]

        with Halo(text=f"Applying McpiCfg resource '{crName}' in '{coreNamespace}'...", spinner=self.spinner) as h:
            mcpiApi = self.dynamicClient.resources.get(api_version="config.mas.ibm.com/v1", kind="McpiCfg")
            try:
                mcpiApi.get(name=crName, namespace=coreNamespace)
                mcpiApi.patch(body=cr, name=crName, namespace=coreNamespace, content_type="application/merge-patch+json")
            except NotFoundError:
                mcpiApi.create(body=cr, namespace=coreNamespace)

            h.stop_and_persist(symbol=self.successIcon, text=f"McpiCfg resource '{crName}' applied successfully")

        self.printH1("Next Steps")
        self.printDescription(
            [
                f"The McpiCfg custom resource has been applied to {coreNamespace}.",
                "The MAS entity manager will reconcile the resource and deploy MCPI components.",
                f"You can verify the MCPI configuration with: oc get mcpicfg -n {coreNamespace}",
            ]
        )
