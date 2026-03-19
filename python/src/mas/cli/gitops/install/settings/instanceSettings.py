# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class GitOpsInstallInstanceSettingsMixin():
    """
    Mixin class for managing MAS instance-level configuration settings.

    This class provides methods for configuring instance-specific resources:
    - MAS Suite installation
    - Workspace settings
    - Domain and DNS configuration
    - SMTP and LDAP (optional)
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def printH2(self, message: str) -> None:
        ...  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        ...  # type: ignore

    def getParam(self, param: str) -> str:
        ...  # type: ignore

    def setParam(self, param: str, value: str) -> None:
        ...  # type: ignore

    def promptForString(self, message: str, param: str = None, default: str = "", isPassword: bool = False) -> str:
        ...  # type: ignore

    def promptForInt(self, message: str, param: str = None, default: int = None, min: int = None, max: int = None) -> int:
        ...  # type: ignore

    def configMASInstance(self) -> None:
        """
        Configure MAS Suite instance settings.

        Collects:
        - mas_instance_id: Instance identifier (3-12 chars)
        - mas_channel: MAS release channel (e.g., 9.0.x, 9.1.x)
        - mas_domain: Domain for MAS routes
        - operational_mode: production or non-production
        """
        logger.debug("Configuring MAS instance")

        self.printH2("MAS Instance")
        self.printDescription([
            "Instance ID restrictions:",
            " - Must be 3-12 characters long",
            " - Must only use lowercase letters, numbers, and hyphen (-) symbol",
            " - Must start with a lowercase letter",
            " - Must end with a lowercase letter or a number"
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("mas_instance_id"):
            self.promptForString("Instance ID", "mas_instance_id")

        # Validate instance ID format
        mas_instance_id = self.getParam("mas_instance_id")
        if mas_instance_id:
            # Must be 3-12 characters, start with lowercase letter, end with lowercase letter or number
            # Only lowercase letters, numbers, and hyphens allowed
            if not re.match(r'^[a-z][a-z0-9-]{1,10}[a-z0-9]$', mas_instance_id):
                raise ValueError(
                    f"Invalid instance ID '{mas_instance_id}'. "
                    "Must be 3-12 characters, start with a lowercase letter, "
                    "end with a lowercase letter or number, and only contain "
                    "lowercase letters, numbers, and hyphens."
                )

        if not self.getParam("mas_channel"):
            self.promptForString("MAS channel", "mas_channel", default="9.0.x")

        if not self.getParam("mas_domain"):
            self.promptForString("MAS domain", "mas_domain")

        # If mas_domain is blank/empty, set dns_provider to blank
        mas_domain = self.getParam("mas_domain")
        if not mas_domain or mas_domain.strip() == "":
            self.setParam("dns_provider", "")
            logger.debug("mas_domain is blank, setting dns_provider to blank")
        else:
            # Only prompt for dns_provider if mas_domain is set
            if not self.getParam("dns_provider"):
                self.promptForString("DNS provider (optional)", "dns_provider", default="")

        # Operational mode
        if not self.getParam("operational_mode"):
            self.printDescription([
                "",
                "Operational Mode:",
                "  1. Production",
                "  2. Non-Production (for development and testing)"
            ])
            mode = self.promptForInt("Operational Mode", default=1)
            if mode == 1:
                self.setParam("operational_mode", "production")
            else:
                self.setParam("operational_mode", "non-production")

    def configMASWorkspace(self) -> None:
        """
        Configure MAS workspace settings.

        Collects:
        - mas_workspace_id: Workspace identifier
        - mas_workspace_name: Human-readable workspace name
        """
        logger.debug("Configuring MAS workspace")

        self.printH2("MAS Workspace")
        self.printDescription([
            "Configure the default workspace for this MAS instance."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("mas_workspace_id"):
            self.promptForString("Workspace ID", "mas_workspace_id", default="main")

        if not self.getParam("mas_workspace_name"):
            self.promptForString("Workspace name", "mas_workspace_name",
                                 default=self.getParam("mas_workspace_id"))

    def configSMTP(self) -> None:
        """
        Configure SMTP settings for email notifications.

        Collects:
        - smtp_host: SMTP server hostname
        - smtp_port: SMTP server port
        - smtp_username: SMTP authentication username
        - smtp_password: SMTP authentication password
        - smtp_from: From email address
        """
        logger.debug("Configuring SMTP")

        self.printH2("SMTP Configuration")
        self.printDescription([
            "Configure SMTP for email notifications from MAS."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("smtp_host"):
            self.promptForString("SMTP host", "smtp_host")

        if not self.getParam("smtp_port"):
            self.promptForString("SMTP port", "smtp_port", default="587")

        if not self.getParam("smtp_username"):
            self.promptForString("SMTP username", "smtp_username")

        if not self.getParam("smtp_password"):
            self.promptForString("SMTP password", "smtp_password", isPassword=True)

        if not self.getParam("smtp_from"):
            self.promptForString("From email address", "smtp_from")

    def configLDAP(self) -> None:
        """
        Configure LDAP settings for user authentication.

        Collects:
        - ldap_url: LDAP server URL
        - ldap_bind_dn: Bind DN for LDAP authentication
        - ldap_bind_password: Bind password
        - ldap_user_base_dn: Base DN for user searches
        - ldap_group_base_dn: Base DN for group searches
        """
        logger.debug("Configuring LDAP")

        self.printH2("LDAP Configuration")
        self.printDescription([
            "Configure LDAP for user authentication in MAS."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("ldap_url"):
            self.promptForString("LDAP URL", "ldap_url")

        if not self.getParam("ldap_bind_dn"):
            self.promptForString("LDAP bind DN", "ldap_bind_dn")

        if not self.getParam("ldap_bind_password"):
            self.promptForString("LDAP bind password", "ldap_bind_password", isPassword=True)

        if not self.getParam("ldap_user_base_dn"):
            self.promptForString("LDAP user base DN", "ldap_user_base_dn")

        if not self.getParam("ldap_group_base_dn"):
            self.promptForString("LDAP group base DN", "ldap_group_base_dn")

    def configAdvancedGitOpsFiles(self) -> None:
        """
        Configure advanced GitOps configuration files for pipeline secrets.

        These files are used to populate the pipeline-gitops-configs and
        pipeline-additional-configs secrets that are consumed by Tekton pipelines.

        Collects file paths for:
        - DRO CA certificate
        - Manual certificates YAML
        - Pod template files (MAS, BAS, SLS, SMTP, App configs)
        - Suite spec additional properties
        - SMTP CA certificate
        """
        logger.debug("Configuring advanced GitOps files")

        self.printH2("Advanced GitOps Configuration Files")
        self.printDescription([
            "Configure optional advanced configuration files for GitOps pipelines.",
            "These files will be included in the pipeline secrets for customization.",
            "Leave blank to skip any optional file."
        ])

        # DRO CA Certificate
        if not self.getParam("dro_ca_certificate_file"):
            self.promptForString("DRO CA certificate file path (optional)", "dro_ca_certificate_file", default="")

        # Manual certificates YAML
        if not self.getParam("mas_manual_certs_yaml"):
            self.promptForString("Manual certificates YAML file path (optional)", "mas_manual_certs_yaml", default="")

        # MAS Pod Templates
        if not self.getParam("mas_pod_template_file"):
            self.promptForString("MAS pod template YAML file path (optional)", "mas_pod_template_file", default="")

        if not self.getParam("mas_bascfg_pod_template_file"):
            self.promptForString("MAS BAS config pod template YAML file path (optional)", "mas_bascfg_pod_template_file", default="")

        if not self.getParam("mas_slscfg_pod_template_file"):
            self.promptForString("MAS SLS config pod template YAML file path (optional)", "mas_slscfg_pod_template_file", default="")

        if not self.getParam("mas_smtpcfg_pod_template_file"):
            self.promptForString("MAS SMTP config pod template YAML file path (optional)", "mas_smtpcfg_pod_template_file", default="")

        if not self.getParam("mas_appcfg_pod_template_file"):
            self.promptForString("MAS app config pod template YAML file path (optional)", "mas_appcfg_pod_template_file", default="")

        # Suite spec additional properties
        if not self.getParam("suite_spec_additional_properties_yaml"):
            self.promptForString("Suite spec additional properties YAML file path (optional)", "suite_spec_additional_properties_yaml", default="")

        if not self.getParam("suite_spec_settings_additional_properties_yaml"):
            self.promptForString("Suite spec settings additional properties YAML file path (optional)", "suite_spec_settings_additional_properties_yaml", default="")

        # SMTP CA Certificate
        if not self.getParam("smtp_config_ca_certificate_file"):
            self.promptForString("SMTP CA certificate file path (optional)", "smtp_config_ca_certificate_file", default="")

        # LDAP certificate (if LDAP is configured)
        if self.getParam("ldap_url") and not self.getParam("ldap_certificate_file"):
            self.promptForString("LDAP certificate file path (optional)", "ldap_certificate_file", default="")

    def configSLSEntitlementFile(self) -> None:
        """
        Configure SLS entitlement license file.

        This file is used to populate the pipeline-sls-entitlement secret
        that is consumed by Tekton pipelines for SLS licensing.

        Collects:
        - sls_entitlement_file: Path to the SLS entitlement.lic file
        """
        logger.debug("Configuring SLS entitlement file")

        self.printH2("SLS Entitlement License")
        self.printDescription([
            "Provide the path to your SLS entitlement license file (entitlement.lic).",
            "This file is required for Suite License Service configuration."
        ])

        if not self.getParam("sls_entitlement_file"):
            self.promptForString("SLS entitlement file path", "sls_entitlement_file")

    def validateInstanceSettings(self) -> tuple[bool, list[str]]:
        """
        Validate instance configuration settings.

        Checks:
        - Instance ID format is valid
        - Domain settings are valid
        - Workspace configurations are complete

        Returns:
            tuple: (is_valid, list of error messages)
        """
        # TODO: Implement instance settings validation in Phase 3
        logger.info("Validating instance settings (stub)")
        return True, []
