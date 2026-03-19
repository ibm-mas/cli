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
from typing import List

logger = logging.getLogger(__name__)


class GitOpsInstallAppsSettingsMixin():
    """
    Mixin class for managing MAS application configuration settings.

    This class provides methods for configuring MAS applications:
    - Maximo Manage
    - Maximo Health
    - Maximo Predict
    - Maximo Monitor
    - Maximo Visual Inspection
    - Maximo Assist
    - IoT
    - Optimizer
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def printH2(self, message: str) -> None:
        ...  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        ...  # type: ignore

    def yesOrNo(self, message: str, param: str = None) -> bool:
        ...  # type: ignore

    def getParam(self, param: str) -> str:
        ...  # type: ignore

    def setParam(self, param: str, value: str) -> None:
        ...  # type: ignore

    def promptForString(self, message: str, param: str = None, default: str = "", isPassword: bool = False) -> str:
        ...  # type: ignore

    def promptForInt(self, message: str, param: str = None, default: int = None, min: int = None, max: int = None) -> int:
        ...  # type: ignore

    selectedApps: List[str]  # type: ignore
    showAdvancedOptions: bool  # type: ignore

    def configApplications(self) -> None:
        """
        Configure which MAS applications to install.

        Prompts user to select applications and collects configuration
        for each selected application.
        """
        logger.debug("Configuring MAS applications")

        self.printH2("Application Selection")
        self.printDescription([
            "Select which MAS applications to install.",
            "You will be prompted for configuration details for each selected application."
        ])

        # Initialize applications list
        self.selectedApps = []

        # IoT
        if self.yesOrNo("Install Maximo IoT"):
            self.selectedApps.append("iot")
            self.configApplicationDatabase("iot")
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for IoT"):
                    self.configApplicationAdvancedFiles("iot")

        # Monitor
        if self.yesOrNo("Install Maximo Monitor"):
            self.selectedApps.append("monitor")
            self.configApplicationDatabase("monitor")
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Monitor"):
                    self.configApplicationAdvancedFiles("monitor")

        # Manage
        if self.yesOrNo("Install Maximo Manage"):
            self.selectedApps.append("manage")
            self.configApplicationDatabase("manage")
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Manage"):
                    self.configApplicationAdvancedFiles("manage")

        # Health (requires Manage and Predict)
        if "manage" in self.selectedApps:
            if self.yesOrNo("Install Maximo Health"):
                # Health requires both Manage and Predict
                if "predict" not in self.selectedApps:
                    logger.warning("Health requires both Manage and Predict applications. Predict will be installed automatically.")
                    self.selectedApps.append("predict")
                self.selectedApps.append("health")
                # Health uses Manage's database

        # Predict
        if self.yesOrNo("Install Maximo Predict"):
            self.selectedApps.append("predict")
            # Predict requires Watson Studio/CP4D
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Predict"):
                    self.configApplicationAdvancedFiles("predict")

        # Visual Inspection
        if self.yesOrNo("Install Maximo Visual Inspection"):
            self.selectedApps.append("visualinspection")
            # Visual Inspection requires GPU
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Visual Inspection"):
                    self.configApplicationAdvancedFiles("visualinspection")

        # Assist
        if self.yesOrNo("Install Maximo Assist"):
            self.selectedApps.append("assist")
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Assist"):
                    self.configApplicationAdvancedFiles("assist")

        # Optimizer
        if self.yesOrNo("Install Maximo Optimizer"):
            self.selectedApps.append("optimizer")
            # Advanced configuration files (advanced mode only)
            if self.showAdvancedOptions:
                if self.yesOrNo("Configure advanced files for Optimizer"):
                    self.configApplicationAdvancedFiles("optimizer")

        # Store selected applications
        self.setParam("mas_applications", ",".join(self.selectedApps))

        logger.info(f"Selected applications: {self.selectedApps}")

    def configApplicationDatabase(self, app_name: str) -> None:
        """
        Configure database settings for a specific application.

        Args:
            app_name: Name of the application (e.g., 'manage', 'monitor', 'iot')

        Collects:
        - Database type (db2, postgres, oracle)
        - Database connection details
        - Schema configuration
        """
        logger.debug(f"Configuring database for {app_name}")

        self.printH2(f"{app_name.capitalize()} Database Configuration")
        self.printDescription([
            f"Configure the database for Maximo {app_name.capitalize()}.",
            "You can use an existing database or deploy a new one."
        ])

        # Database action: install new or use existing
        db_action_param = f"{app_name}_db_action"
        if not self.getParam(db_action_param):
            if self.yesOrNo(f"Deploy new database for {app_name}"):
                self.setParam(db_action_param, "install")

                # Database type
                db_type_param = f"{app_name}_db_type"
                if not self.getParam(db_type_param):
                    self.printDescription([
                        "Database type:",
                        "  1. DB2 (recommended)",
                        "  2. PostgreSQL",
                        "  3. Oracle"
                    ])
                    db_type_choice = self.promptForInt("Database type", default=1)
                    if db_type_choice == 1:
                        self.setParam(db_type_param, "db2")
                    elif db_type_choice == 2:
                        self.setParam(db_type_param, "postgres")
                    else:
                        self.setParam(db_type_param, "oracle")
            else:
                self.setParam(db_action_param, "existing")

                # Collect existing database connection details
                self.promptForString(f"{app_name} database host", f"{app_name}_db_host")
                self.promptForString(f"{app_name} database port", f"{app_name}_db_port")
                self.promptForString(f"{app_name} database name", f"{app_name}_db_name")
                self.promptForString(f"{app_name} database username", f"{app_name}_db_username")
                self.promptForString(f"{app_name} database password", f"{app_name}_db_password",
                                     isPassword=True)

                # Validate that all required fields are provided
                required_fields = [
                    (f"{app_name}_db_host", "database host"),
                    (f"{app_name}_db_port", "database port"),
                    (f"{app_name}_db_name", "database name"),
                    (f"{app_name}_db_username", "database username"),
                    (f"{app_name}_db_password", "database password")
                ]
                missing_fields = []
                for field_param, field_name in required_fields:
                    if not self.getParam(field_param):
                        missing_fields.append(field_name)

                if missing_fields:
                    raise ValueError(
                        f"Missing required database connection details for {app_name}: "
                        f"{', '.join(missing_fields)}"
                    )

    def configApplicationAdvancedFiles(self, app_name: str) -> None:
        """
        Configure advanced GitOps configuration files for a specific application.

        This method prompts for app-specific configuration files that will be included
        in the pipeline-gitops-configs secret for the apps pipeline.

        Args:
            app_name: Name of the application (e.g., 'manage', 'iot', 'assist')

        Collects:
        - DB2 configuration files (for manage, iot, facilities)
        - MAS app spec and workspace spec files (for all apps)
        - Manage-specific files (server bundles, global secrets)
        - JDBC certificate files
        """
        logger.debug(f"Configuring advanced files for {app_name}")

        self.printH2(f"{app_name.capitalize()} Advanced Configuration Files")
        self.printDescription([
            f"Configure optional advanced configuration files for {app_name.capitalize()}.",
            "These files will be included in the pipeline secrets for customization.",
            "Leave blank to skip any optional file."
        ])

        # DB2 configuration files (for manage, iot, facilities)
        if app_name in ['manage', 'iot', 'facilities']:
            if not self.getParam(f'db2_instance_registry_{app_name}_file'):
                self.promptForString(f"DB2 instance registry file for {app_name} (optional)",
                                     f'db2_instance_registry_{app_name}_file', default="")

            if not self.getParam(f'db2_database_db_config_{app_name}_file'):
                self.promptForString(f"DB2 database config file for {app_name} (optional)",
                                     f'db2_database_db_config_{app_name}_file', default="")

            if not self.getParam(f'db2_addons_audit_config_{app_name}_file'):
                self.promptForString(f"DB2 audit config file for {app_name} (optional)",
                                     f'db2_addons_audit_config_{app_name}_file', default="")

            if not self.getParam(f'db2_instance_dbm_config_{app_name}_file'):
                self.promptForString(f"DB2 instance DBM config file for {app_name} (optional)",
                                     f'db2_instance_dbm_config_{app_name}_file', default="")

            # JDBC certificate
            if not self.getParam(f'{app_name}_jdbc_certificate_file'):
                self.promptForString(f"JDBC certificate file for {app_name} (optional)",
                                     f'{app_name}_jdbc_certificate_file', default="")

        # MAS app workspace spec file (for all apps)
        if not self.getParam(f'mas_appws_spec_{app_name}_file'):
            self.promptForString(f"MAS app workspace spec file for {app_name} (optional)",
                                 f'mas_appws_spec_{app_name}_file', default="")

        # MAS app spec file (for all apps)
        if not self.getParam(f'mas_app_spec_{app_name}_file'):
            self.promptForString(f"MAS app spec file for {app_name} (optional)",
                                 f'mas_app_spec_{app_name}_file', default="")

        # Manage-specific files
        if app_name == 'manage':
            if not self.getParam('mas_app_server_bundles_manage_file'):
                self.promptForString("MAS app server bundles config file for manage (optional)",
                                     'mas_app_server_bundles_manage_file', default="")

            if not self.getParam('mas_app_global_secrets_manage_file'):
                self.promptForString("MAS app global secrets file for manage (optional)",
                                     'mas_app_global_secrets_manage_file', default="")

    def validateAppsSettings(self) -> tuple[bool, list[str]]:
        """
        Validate application configuration settings.

        Checks:
        - Application channels are valid
        - Required dependencies are configured
        - Application-specific settings are correct
        - Workspace assignments are valid

        Returns:
            tuple: (is_valid, list of error messages)
        """
        # TODO: Implement apps settings validation in Phase 3
        logger.info("Validating apps settings (stub)")
        return True, []
