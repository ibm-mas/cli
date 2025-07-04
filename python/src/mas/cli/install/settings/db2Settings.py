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
from prompt_toolkit import print_formatted_text


class Db2SettingsMixin():
    # In silentMode, no prompts will show up for "happy path" DB2 configuration scenarios. Prompts will still show up when an input is absolutely required
    # Settings under showAdvancedOptions are always prompted
    def configDb2(self, silentMode=False) -> None:
        if not silentMode:
            self.printH1("Configure Databases")
        # The channel used for Db2 used has not changed since the January 2024 catalog update
        self.params["db2_channel"] = "v110509.0"

        # If neither Iot, Manage or Facilities is being installed, we have nothing to do
        if not self.installIoT and not self.installManage and not self.installFacilities:
            print_formatted_text("No applications have been selected that require a Db2 installation")
            self.setParam("db2_action_system", "none")
            self.setParam("db2_action_manage", "none")
            self.setParam("db2_action_facilities", "none")
            return

        # For now we are limiting users to bring your own database for Manage on s390x & ppc64le
        # Eventually we will be able to remove this clause and allow the standard logic to work for s390x, ppc64le and amd64
        if (self.architecture == "s390x" or self.architecture == "ppc64le") and self.installManage:
            # silentMode does not apply for s390x/ppc64le because it requires interaction when selecting local config directory
            self.printDescription([
                "Installation of a Db2 instance using the IBM Db2 Universal Operator is not currently supported on s390x /ppc64le, please provide configuration details for the database you wish to use.",
            ])
            instanceId = self.getParam('mas_instance_id')
            workspaceId = self.getParam("mas_workspace_id")

            self.setParam("mas_appws_bindings_jdbc_manage", "workspace-application")
            self.setParam("db2_action_manage", "byo")
            self.selectLocalConfigDir()

            # Check if a configuration already exists before creating a new one
            jdbcCfgFile = path.join(self.localConfigDir, f"jdbc-{instanceId}-manage.yaml")
            print_formatted_text(f"Searching for {self.manageAppName} database configuration file in {jdbcCfgFile} ...")
            if path.exists(jdbcCfgFile):
                if self.yesOrNo(f"{self.manageAppName} database configuration file 'jdbc-{instanceId}-manage.yaml' already exists.  Do you want to generate a new one"):
                    self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
            else:
                print_formatted_text(f"Expected file ({jdbcCfgFile}) was not found, generating a valid {self.manageAppName} database configuration file now ...")
                self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
            return

        # Proceed as normal
        # We know we are installing either IoT, Manage or Facilities, and on amd64 target architecture
        if not silentMode:
            self.printDescription([
                f"The installer can setup one or more IBM Db2 instances in your OpenShift cluster for the use of applications that require a JDBC datasource (IoT, {self.manageAppName}, Monitor, &amp; Predict, Real Estate and Facilities) or you may choose to configure MAS to use an existing database"
            ])

        self.setDB2DefaultSettings()

        instanceId = self.getParam('mas_instance_id')
        # Do we need to set up an IoT database?
        if self.installIoT:
            if not silentMode:
                self.printH2("Database Configuration for Maximo IoT")
                self.printDescription([
                    "Maximo IoT requires a shared system-scope Db2 instance because others application in the suite require access to the same database source",
                    " - Only IBM Db2 is supported for this database"
                ])
            createSystemDb2UsingUniversalOperator = True
            if not silentMode:
                createSystemDb2UsingUniversalOperator = self.yesOrNo("Create system Db2 instance using the IBM Db2 Universal Operator")
            if createSystemDb2UsingUniversalOperator:
                self.setParam("db2_action_system", "install")
            else:
                self.setParam("db2_action_system", "byo")

                self.selectLocalConfigDir()

                # Check if a configuration already exists before creating a new one
                jdbcCfgFile = path.join(self.localConfigDir, f"jdbc-{instanceId}-system.yaml")
                print_formatted_text(f"Searching for system database configuration file in {jdbcCfgFile} ...")
                if path.exists(jdbcCfgFile):
                    if self.yesOrNo(f"System database configuration file 'jdbc-{instanceId}-system.yaml' already exists.  Do you want to generate a new one"):
                        self.generateJDBCCfg(instanceId=instanceId, scope="system", destination=jdbcCfgFile)
                else:
                    print_formatted_text(f"Expected file ({jdbcCfgFile}) was not found, generating a valid system database configuration file now ...")
                    self.generateJDBCCfg(instanceId=instanceId, scope="system", destination=jdbcCfgFile)
        else:
            self.setParam("db2_action_system", "none")

        if self.installManage:
            if not silentMode:
                self.printH2(f"Database Configuration for Maximo {self.manageAppName}")
                self.printDescription([
                    f"Maximo {self.manageAppName} can be configured to share the system Db2 instance or use it's own dedicated database:",
                    " - Use of a shared instance has a significant footprint reduction but is only recommended for development/test/demo installs",
                    " - In most production systems you will want to use a dedicated database",
                    " - IBM Db2, Oracle Database, &amp; Microsoft SQL Server are all supported database options"
                ])
            # Determine whether to use the system or a dedicated database
            reuseSystemDb2 = False
            if self.installIoT:
                if not silentMode:
                    reuseSystemDb2 = self.yesOrNo(f"Re-use System Db2 instance for {self.manageAppName} application")
            if reuseSystemDb2:
                # We are going to bind Manage to the system database, which has already been set up in the previous step
                self.setParam("mas_appws_bindings_jdbc_manage", "system")
                self.setParam("db2_action_manage", "none")
            else:
                self.setParam("mas_appws_bindings_jdbc_manage", "workspace-application")
                createSystemDb2UsingUniversalOperator = True
                if not silentMode:
                    createSystemDb2UsingUniversalOperator = self.yesOrNo(f"Create {self.manageAppName} dedicated Db2 instance using the IBM Db2 Universal Operator")
                if createSystemDb2UsingUniversalOperator:
                    self.setParam("db2_action_manage", "install")
                    if not silentMode:
                        self.printDescription([
                            f"Available Db2 instance types for {self.manageAppName}:",
                            "  1. DB2 Warehouse (Default option)",
                            "  2. DB2 Online Transactional Processing (OLTP)"
                        ])
                        self.promptForListSelect(message=f"Select the {self.manageAppName} dedicated DB2 instance type", options=["db2wh", "db2oltp"], param="db2_type", default="1")
                    else:
                        self.setParam("db2_type", "db2wh")
                else:
                    workspaceId = self.getParam("mas_workspace_id")
                    self.setParam("db2_action_manage", "byo")

                    self.selectLocalConfigDir()

                    # Check if a configuration already exists before creating a new one
                    jdbcCfgFile = path.join(self.localConfigDir, f"jdbc-{instanceId}-manage.yaml")
                    print_formatted_text(f"Searching for {self.manageAppName} database configuration file in {jdbcCfgFile} ...")
                    if path.exists(jdbcCfgFile):
                        if self.yesOrNo(f"{self.manageAppName} database configuration file 'jdbc-{instanceId}-manage.yaml' already exists.  Do you want to generate a new one"):
                            self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
                    else:
                        print_formatted_text(f"Expected file ({jdbcCfgFile}) was not found, generating a valid {self.manageAppName} database configuration file now ...")
                        self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
        else:
            self.setParam("db2_action_manage", "none")

        # Do we need to create and configure a Db2 for Facilities ?
        if self.installFacilities:
            self.printH2("Database Configuration for Maximo Real Estate and Facilities")
            if self.yesOrNo("Create Real Estate and Facilities dedicated Db2 instance using the IBM Db2 Universal Operator"):
                self.setParam("db2_action_facilities", "install")
            else:
                self.setParam("db2_action_facilities", "none")
                instanceId = self.getParam('mas_instance_id')
                workspaceId = self.getParam("mas_workspace_id")
                self.selectLocalConfigDir()

                # Check if a configuration already exists before creating a new one
                jdbcCfgFile = path.join(self.localConfigDir, f"jdbc-{instanceId}-facilities.yaml")
                print_formatted_text(f"Searching for Real Estate and Facilities database configuration file in {jdbcCfgFile} ...")
                if path.exists(jdbcCfgFile):
                    if self.yesOrNo(f"Real Estate and Facilities database configuration file 'jdbc-{instanceId}-facilities.yaml' already exists.  Do you want to generate a new one"):
                        self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="facilities", destination=jdbcCfgFile)
                else:
                    print_formatted_text(f"Expected file ({jdbcCfgFile}) was not found, generating a valid Real Estate and Facilities database configuration file now ...")
                    self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="facilities", destination=jdbcCfgFile)
        else:
            self.setParam("db2_action_facilities", "none")

        # Do we need to configure Db2u?
        if self.getParam("db2_action_system") == "install" or self.getParam("db2_action_manage") == "install" or self.getParam("db2_action_facilities") == "install":
            if self.showAdvancedOptions:
                self.printH2("Installation Namespace")
                self.promptForString("Install namespace", "db2_namespace", default="db2u")

                # Node Affinity & Tolerations
                # -------------------------------------------------------------------------
                self.printH2("Node Affinity and Tolerations")
                self.printDescription([
                    f"Note that the same settings are applied to both the IoT and {self.manageAppName} Db2 instances",
                    "Use existing node labels and taints to control scheduling of the Db2 workload in your cluster",
                    "For more information refer to the Red Hat documentation:",
                    " - <Orange><u>https://docs.openshift.com/container-platform/4.18/nodes/scheduling/nodes-scheduler-node-affinity.html</u></Orange>",
                    " - <Orange><u>https://docs.openshift.com/container-platform/4.18/nodes/scheduling/nodes-scheduler-taints-tolerations.html</u></Orange>",
                    " - <Orange><u>https://docs.openshift.com/container-platform/4.17/nodes/scheduling/nodes-scheduler-node-affinity.html</u></Orange>",
                    " - <Orange><u>https://docs.openshift.com/container-platform/4.17/nodes/scheduling/nodes-scheduler-taints-tolerations.html</u></Orange>"
                ])

                if self.yesOrNo("Configure node affinity"):
                    self.promptForString(" + Key", "db2_affinity_key")
                    self.promptForString(" + Value", "db2_affinity_value")

                if self.yesOrNo("Configure node tolerations"):
                    self.promptForString(" + Key", "db2_tolerate_key")
                    self.promptForString(" + Value", "db2_tolerate_value")
                    self.promptForString(" + Effect", "db2_tolerate_effect")

                self.printH2("Database CPU & Memory")
                self.printDescription([
                    f"Note that the same settings are applied to both the IoT and {self.manageAppName} Db2 instances"
                ])

                if self.yesOrNo("Customize CPU and memory request/limit"):
                    self.promptForString(" + CPU Request", "db2_cpu_requests", default=self.getParam("db2_cpu_requests"))
                    self.promptForString(" + CPU Limit", "db2_cpu_limits", default=self.getParam("db2_cpu_limits"))
                    self.promptForString(" + Memory Request", "db2_memory_requests", default=self.getParam("db2_memory_requests"))
                    self.promptForString(" + Memory Limit", "db2_memory_limits", default=self.getParam("db2_memory_limits"))

                self.printH2("Database Storage Capacity")
                self.printDescription([
                    f"Note that the same settings are applied to both the IoT and {self.manageAppName} Db2 instances"
                ])

                if self.yesOrNo("Customize storage capacity"):
                    self.promptForString(" + Data Volume", "db2_data_storage_size", default=self.getParam("db2_data_storage_size"))
                    self.promptForString(" + Temporary Volume", "db2_temp_storage_size", default=self.getParam("db2_temp_storage_size"))
                    self.promptForString(" + Metadata Volume", "db2_meta_storage_size", default=self.getParam("db2_meta_storage_size"))
                    self.promptForString(" + Transaction Logs Volume", "db2_logs_storage_size", default=self.getParam("db2_logs_storage_size"))
                    self.promptForString(" + Backup Volume", "db2_backup_storage_size", default=self.getParam("db2_backup_storage_size"))
            else:
                self.setParam("db2_namespace", "db2u")

    def setDB2DefaultSettings(self) -> None:

        self.setParam("db2_cpu_requests", "4000m")
        self.setParam("db2_cpu_limits", "6000m")
        self.setParam("db2_memory_requests", "8Gi")
        self.setParam("db2_memory_limits", "12Gi")

        if self.isSNO():
            # Set smaller defaults for SNO deployments
            self.setParam("db2_meta_storage_size", "10Gi")
            self.setParam("db2_backup_storage_size", "10Gi")
            self.setParam("db2_logs_storage_size", "10Gi")
            self.setParam("db2_temp_storage_size", "10Gi")
            self.setParam("db2_data_storage_size", "20Gi")

            # Configure the access mode to RWO
            self.params["db2_meta_storage_accessmode"] = "ReadWriteOnce"
            self.params["db2_backup_storage_accessmode"] = "ReadWriteOnce"
            self.params["db2_logs_storage_accessmode"] = "ReadWriteOnce"
            self.params["db2_data_storage_accessmode"] = "ReadWriteOnce"
            self.params["db2_cpu_requests"] = "300m"

        else:
            self.setParam("db2_meta_storage_size", "20Gi")
            self.setParam("db2_backup_storage_size", "100Gi")
            self.setParam("db2_logs_storage_size", "100Gi")
            self.setParam("db2_temp_storage_size", "100Gi")
            self.setParam("db2_data_storage_size", "100Gi")
