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

logger = logging.getLogger(__name__)


class McpiInstallArgBuilderMixin:
    """Mixin that builds the equivalent non-interactive CLI command string."""

    def buildCommand(self) -> str:
        """Build a re-runnable mas mcpi-install shell command from current params.

        Returns:
            str: Shell command string that reproduces the current configuration.
        """
        newline = " \\\n"
        command = "export IBM_ENTITLEMENT_KEY=x\n"
        if self.getParam("artifactory_username") != "":
            command += "export ARTIFACTORY_USERNAME=x\nexport ARTIFACTORY_TOKEN=x\n"

        command += f"mas mcpi-install --mas-catalog-version {self.getParam('mas_catalog_version')}"

        if self.getParam("mas_catalog_digest") != "":
            command += f" --mas-catalog-digest {self.getParam('mas_catalog_digest')}"

        command += f" --ibm-entitlement-key $IBM_ENTITLEMENT_KEY{newline}"

        # MAS Instance ID
        command += f"  --mas-instance-id \"{self.getParam('mas_instance_id')}\"{newline}"

        # MCPI channel & routing
        command += f"  --mcpi-channel \"{self.getParam('mcpi_channel')}\"{newline}"
        if self.getParam("routing_mode") != "":
            command += f"  --routing-mode \"{self.getParam('routing_mode')}\"{newline}"
        if self.getParam("manual_route_mgmt") != "":
            command += f"  --manual-route-mgmt \"{self.getParam('manual_route_mgmt')}\"{newline}"

        # MAS Advanced Configuration
        if self.localConfigDir is not None:
            command += f'  --additional-configs "{self.localConfigDir}"{newline}'

        # Storage
        command += f"  --storage-class-rwo \"{self.getParam('storage_class_rwo')}\""
        command += f" --storage-class-rwx \"{self.getParam('storage_class_rwx')}\"{newline}"
        command += f'  --storage-pipeline "{self.pipelineStorageClass}"'
        command += f' --storage-accessmode "{self.pipelineStorageAccessMode}"{newline}'

        # IBM Suite License Service
        if self.getParam("sls_namespace") and self.getParam("sls_namespace") != "ibm-sls":
            if self.getParam("sls_namespace") == f"mas-{self.getParam('mas_instance_id')}-sls":
                command += "  --dedicated-sls"
            else:
                command += f"  --sls-namespace \"{self.getParam('sls_namespace')}\""
        if self.slsLicenseFileLocal:
            command += f'  --license-file "{self.slsLicenseFileLocal}"'
        if (self.getParam("sls_namespace") and self.getParam("sls_namespace") != "ibm-sls") or self.slsLicenseFileLocal:
            command += newline

        # IBM Data Reporting Operator (DRO)
        command += f"  --contact-email \"{self.getParam('dro_contact_email')}\""
        command += f" --contact-firstname \"{self.getParam('dro_contact_firstname')}\""
        command += f" --contact-lastname \"{self.getParam('dro_contact_lastname')}\"{newline}"
        if self.getParam("dro_namespace") != "":
            command += f"  --dro-namespace \"{self.getParam('dro_namespace')}\"{newline}"

        # Development Mode
        if self.getParam("artifactory_username") != "":
            command += f"  --artifactory-username $ARTIFACTORY_USERNAME --artifactory-token $ARTIFACTORY_TOKEN{newline}"

        # More Options
        if self.devMode:
            command += f"  --dev-mode{newline}"
        if self.getParam("skip_pre_check") is True:
            command += f"  --skip-pre-check{newline}"
        if self.getParam("image_pull_policy") != "":
            command += f"  --image-pull-policy {self.getParam('image_pull_policy')}{newline}"
        if self.getParam("service_account_name") != "":
            command += f"  --service-account {self.getParam('service_account_name')}{newline}"

        command += "  --accept-license --no-confirm"
        return command
