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
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    # Type stubs for methods provided by BaseApp
    def printH1(self, message: str) -> None:
        ...

    def printH2(self, message: str) -> None:
        ...

    def printDescription(self, content: List[str]) -> None:
        ...

    def printSummary(self, title: str, value: str) -> None:
        ...

    def printParamSummary(self, message: str, param: str) -> None:
        ...

    def getParam(self, param: str) -> str:
        ...

    def setParam(self, param: str, value: str) -> None:
        ...

logger = logging.getLogger(__name__)


class GitOpsInstallSummarizerMixin():
    """
    Mixin class for displaying installation summaries.

    This class provides methods to format and display comprehensive summaries
    of the GitOps installation configuration before execution. This helps users
    review and confirm their choices before proceeding with the installation.

    Note: This mixin expects to be used with BaseApp which provides:
    - printH1, printH2, printDescription, printTable methods
    - getParam, setParam methods
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def printH1(self, message: str) -> None:
        ...  # type: ignore

    def printH2(self, message: str) -> None:
        ...  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        ...  # type: ignore

    def printSummary(self, title: str, value: str) -> None:
        ...  # type: ignore

    def printParamSummary(self, message: str, param: str) -> None:
        ...  # type: ignore

    def getParam(self, param: str) -> str:
        ...  # type: ignore

    def setParam(self, param: str, value: str) -> None:
        ...  # type: ignore

    def reviewConfiguration(self) -> None:
        """
        Display comprehensive configuration review before installation.

        Shows:
        - GitOps Configuration (repository, cluster, secrets)
        - Cluster Configuration (catalog, operators)
        - Instance Configuration (MAS, workspace, SMTP/LDAP)
        - Applications Configuration (selected apps, databases)
        """
        logger.debug("Reviewing configuration")

        self.printH2("Configuration Review")  # type: ignore
        self.printDescription([  # type: ignore
            "Please review your configuration before proceeding with the installation."
        ])

        # GitOps Configuration
        self.displayGitOpsConfiguration()

        # Cluster Configuration
        self.displayClusterConfiguration()

        # Instance Configuration
        self.displayInstanceConfiguration()

        # Applications Configuration
        if self.getParam('mas_app_ids'):  # type: ignore
            self.displayApplicationsConfiguration()

    def displayGitOpsConfiguration(self) -> None:
        """
        Display GitOps repository and cluster configuration.
        """
        self.printH2("GitOps Configuration")  # type: ignore

        github_host = self.getParam('github_host') or 'Not configured'  # type: ignore
        github_org = self.getParam('github_org') or 'Not configured'
        github_repo = self.getParam('github_repo') or 'Not configured'
        git_branch = self.getParam('git_branch') or 'main'

        self.printSummary("Repository", f"{github_host}/{github_org}/{github_repo}")  # type: ignore
        self.printSummary("Branch", git_branch)  # type: ignore
        self.printSummary("Cluster ID", self.getParam('cluster_id') or 'Not configured')  # type: ignore
        self.printSummary("Account/Region", f"{self.getParam('account_id') or 'N/A'}/{self.getParam('region_id') or 'default'}")  # type: ignore
        self.printSummary("Secrets Path", self.getParam('secrets_path') or 'Not configured')  # type: ignore
        self.printSummary("AWS Region", self.getParam('avp_aws_secret_region') or 'us-east-1')  # type: ignore

    def displayClusterConfiguration(self) -> None:
        """
        Display cluster-level configuration.
        """
        self.printH2("Cluster Configuration")  # type: ignore
        self.printParamSummary("MAS Catalog", "mas_catalog_version")  # type: ignore
        self.printSummary("DRO", "Enabled" if self.getParam('install_dro') == 'true' else "Disabled")  # type: ignore

        # Add DRO contact information if DRO is enabled
        if self.getParam('install_dro') == 'true':  # type: ignore
            if self.getParam('dro_contact_email'):  # type: ignore
                self.printParamSummary("+ Contact Email", "dro_contact_email")  # type: ignore
            if self.getParam('dro_contact_firstname'):  # type: ignore
                self.printParamSummary("+ Contact First Name", "dro_contact_firstname")  # type: ignore
            if self.getParam('dro_contact_lastname'):  # type: ignore
                self.printParamSummary("+ Contact Last Name", "dro_contact_lastname")  # type: ignore

        self.printSummary("GPU Operator", "Enabled" if self.getParam('install_gpu') == 'true' else "Disabled")  # type: ignore
        self.printSummary("Cert Manager", "Enabled" if self.getParam('install_cert_manager') == 'true' else "Disabled")  # type: ignore
        self.printSummary("NFD", "Enabled" if self.getParam('install_nfd') == 'true' else "Disabled")  # type: ignore

        # Add storage classes if configured
        storage_rwo = self.getParam('storage_class_rwo')  # type: ignore
        storage_rwx = self.getParam('storage_class_rwx')  # type: ignore
        if storage_rwo:
            self.printSummary("Storage Class (RWO)", storage_rwo)  # type: ignore
        if storage_rwx:
            self.printSummary("Storage Class (RWX)", storage_rwx)  # type: ignore

    def displayInstanceConfiguration(self) -> None:
        """
        Display MAS instance configuration.
        """
        self.printH2("Instance Configuration")  # type: ignore
        self.printParamSummary("Instance ID", "mas_instance_id")  # type: ignore
        self.printParamSummary("Channel", "mas_channel")  # type: ignore
        self.printParamSummary("Domain", "mas_domain")  # type: ignore
        self.printParamSummary("Workspace ID", "mas_workspace_id")  # type: ignore
        self.printParamSummary("Workspace Name", "mas_workspace_name")  # type: ignore
        self.printSummary("Operational Mode", self.getParam('operational_mode') or 'production')  # type: ignore

        print()
        # Add SLS if configured
        sls_channel = self.getParam('sls_channel')  # type: ignore
        if sls_channel:
            self.printSummary("SLS Channel", sls_channel)  # type: ignore

        # Add SLS Entitlement File if configured
        sls_entitlement_file = self.getParam('sls_entitlement_file')  # type: ignore
        if sls_entitlement_file:
            self.printSummary("SLS Entitlement File", sls_entitlement_file)  # type: ignore

        # Add MongoDB if configured
        mongo_provider = self.getParam('mongo_provider')  # type: ignore
        if mongo_provider:
            self.printSummary("MongoDB Provider", mongo_provider)  # type: ignore

        # Add SMTP if configured
        smtp_host = self.getParam('smtp_host')  # type: ignore
        if smtp_host:
            smtp_port = self.getParam('smtp_port') or '587'  # type: ignore
            self.printSummary("SMTP", f"{smtp_host}:{smtp_port}")  # type: ignore

        # Add LDAP if configured
        ldap_url = self.getParam('ldap_url')  # type: ignore
        if ldap_url:
            self.printSummary("LDAP", ldap_url)  # type: ignore

    def displayApplicationsConfiguration(self) -> None:
        """
        Display MAS applications configuration.
        """
        self.printH2("Applications Configuration")  # type: ignore

        mas_app_ids = self.getParam('mas_app_ids') or ''  # type: ignore
        if not mas_app_ids:
            self.printDescription(["No applications selected"])  # type: ignore
            return

        app_ids = [app.strip() for app in mas_app_ids.split(',') if app.strip()]

        for app_id in app_ids:
            channel = self.getParam(f'{app_id}_channel') or 'Not configured'  # type: ignore
            db_action = self.getParam(f'{app_id}_db_action') or 'install'  # type: ignore
            db_type = self.getParam(f'{app_id}_db_type') or 'db2'  # type: ignore

            db_info = f"{db_action} ({db_type})"
            if db_action == 'existing':
                db_host = self.getParam(f'{app_id}_db_host') or 'N/A'  # type: ignore
                db_info = f"existing ({db_type} @ {db_host})"

            self.printSummary(app_id.upper(), channel)  # type: ignore
            self.printSummary("+ Database", db_info)  # type: ignore
            print()

    def displayInstallSummary(self) -> None:
        """
        Display a comprehensive summary of the installation configuration.

        This method presents all configured parameters in an organized format,
        similar to the standard install summarizer but focused on GitOps-specific
        configuration.
        """
        logger.debug("Displaying installation summary")

        self.printH1("Installation Summary")
        self.printDescription([
            "Review the configuration below before proceeding with the GitOps installation."
        ])

        # Execution Mode
        self.printH2("Execution Mode")
        execution_mode = "Tekton Pipelines" if self.executionMode == "tekton" else "Direct Execution"  # type: ignore
        self.printDescription([f"Mode: {execution_mode}"])

        # Display all configuration sections
        self.displayGitOpsConfiguration()
        self.displayClusterConfiguration()
        self.displayInstanceConfiguration()

        if self.getParam('mas_app_ids'):
            self.displayApplicationsConfiguration()

    def displayClusterSummary(self) -> None:
        """
        Display cluster-level configuration summary.

        Shows cluster prerequisites and operator configurations that will
        be deployed at the cluster level.
        """
        self.displayClusterConfiguration()

    def displayInstanceSummary(self) -> None:
        """
        Display MAS instance configuration summary.

        Shows the MAS instance settings including workspace configuration,
        database connections, and instance-specific settings.
        """
        self.displayInstanceConfiguration()

    def displayAppsSummary(self) -> None:
        """
        Display MAS applications configuration summary.

        Shows which MAS applications will be installed and their
        configuration settings.
        """
        self.displayApplicationsConfiguration()
