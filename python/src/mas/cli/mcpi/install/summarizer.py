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
import yaml
from mas.devops.ocp import getConsoleURL

logger = logging.getLogger(__name__)


class McpiInstallSummarizerMixin:
    """Mixin that renders the pre-launch settings review."""

    def ocpSummary(self) -> None:
        """Print OpenShift platform and pipeline configuration summary."""
        self.printH2("Pipeline Configuration")
        self.printParamSummary("Service Account", "service_account_name")
        self.printParamSummary("Image Pull Policy", "image_pull_policy")
        self.printSummary("Skip Pre-Install Healthcheck", "Yes" if self.getParam("skip_pre_check") == "true" else "No")

        self.printH2("OpenShift Container Platform")
        self.printSummary("Worker Node Architecture", self.architecture)
        self.printSummary("Storage Class Provider", self.storageClassProvider)
        self.printParamSummary("ReadWriteOnce Storage Class", "storage_class_rwo")
        self.printParamSummary("ReadWriteMany Storage Class", "storage_class_rwx")
        self.printParamSummary("Certificate Manager", "cert_manager_provider")

    def mcpiSummary(self) -> None:
        """Print MCPI operator configuration summary."""
        self.printH2("Maximo Operator Catalog")
        self.printParamSummary("Catalog Version", "mas_catalog_version")
        if self.getParam("mas_catalog_digest") != "":
            self.printParamSummary("Catalog Digest", "mas_catalog_digest")

        self.printH2("Maximo Cluster Performance Insights (MCPI)")
        self.printParamSummary("MAS Instance ID", "mas_instance_id")
        self.printParamSummary("Subscription Channel", "mcpi_channel")
        if self.getParam("routing_mode") != "":
            self.printParamSummary("Routing Mode", "routing_mode")
        if self.getParam("manual_route_mgmt") != "":
            self.printParamSummary("Manual Route Management", "manual_route_mgmt")

    def droSummary(self) -> None:
        """Print DRO configuration summary."""
        self.printH2("IBM Data Reporter Operator (DRO) Configuration")
        self.printParamSummary("Contact e-mail", "dro_contact_email")
        self.printParamSummary("First name", "dro_contact_firstname")
        self.printParamSummary("Last name", "dro_contact_lastname")
        self.printParamSummary("Install Namespace", "dro_namespace")

    def slsSummary(self) -> None:
        """Print SLS configuration summary."""
        self.printH2("IBM Suite License Service")
        self.printParamSummary("Namespace", "sls_namespace")
        if self.getParam("sls_action") == "install":
            self.printSummary("Subscription Channel", "3.x")
            if self.slsLicenseFileLocal:
                self.printSummary("License File", self.slsLicenseFileLocal)

    def slackSummary(self) -> None:
        """Print Slack integration summary."""
        self.printH2("Slack Integration")
        if self.getParam("slack_channel") != "":
            self.printParamSummary("Slack Channel", "slack_channel")
        else:
            self.printSummary("Slack Channel", "Not Configured")

    def displayInstallSummary(self) -> None:
        """Render the full pre-launch settings review."""
        self.printH1("Review Settings")
        self.printDescription(["Connected to:", f" - <u>{getConsoleURL(self.dynamicClient)}</u>"])

        logger.debug("PipelineRun parameters:")
        logger.debug(yaml.dump(self.params, default_flow_style=False))

        self.ocpSummary()
        self.mcpiSummary()
        self.droSummary()
        self.slsSummary()
        self.slackSummary()
