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
    def configDb2(self) -> None:
        self.printH1("Configure Databases")
        # The channel used for Db2 used has not changed since the January 2024 catalog update
        self.params["db2_channel"] = "v110509.0"

        if not self.installIoT and not self.installManage:
            print_formatted_text("No applications have been selected that require a Db2 installation")
            self.setParam("db2_action_system", "none")
            self.setParam("db2_action_manage", "none")
            return

        self.printDescription([
            "The installer can setup one or more IBM Db2 instances in your OpenShift cluster for the use of applications that require a JDBC datasource (IoT, Manage, Monitor, &amp; Predict) or you may choose to configure MAS to use an existing database"
        ])

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

            # Also reduce the CPU requests
            self.params["db2_cpu_requests"] = "300m"
        else:
            self.setParam("db2_meta_storage_size", "20Gi")
            self.setParam("db2_backup_storage_size", "100Gi")
            self.setParam("db2_logs_storage_size", "100Gi")
            self.setParam("db2_temp_storage_size", "100Gi")
            self.setParam("db2_data_storage_size", "100Gi")

        instanceId = self.getParam('mas_instance_id')
        # Do we need to set up an IoT database?
        if self.installIoT:
            self.printH2("Database Configuration for Maximo IoT")
            self.printDescription([
                "Maximo IoT requires a shared system-scope Db2 instance because others application in the suite require access to the same database source",
                " - Only IBM Db2 is supported for this database"
            ])
            if self.yesOrNo("Create system Db2 instance using the IBM Db2 Universal Operator"):
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
            self.printH2("Database Configuration for Maximo Manage")
            self.printDescription([
                "Maximo Manage can be configured to share the system Db2 instance or use it's own dedicated database:",
                " - Use of a shared instance has a significant footprint reduction but is only recommended for development/test/demo installs",
                " - In most production systems you will want to use a dedicated database",
                " - IBM Db2, Oracle Database, &amp; Microsoft SQL Server are all supported database options"
            ])
            # Determine whether to use the system or a dedicated database
            if self.installIoT and self.yesOrNo("Re-use System Db2 instance for Manage application"):
                # We are going to bind Manage to the system database, which has already been set up in the previous step
                self.setParam("mas_appws_bindings_jdbc_manage", "system")
                self.setParam("db2_action_manage", "none")
            else:
                self.setParam("mas_appws_bindings_jdbc_manage", "workspace-application")
                if self.yesOrNo("Create manage dedicated Db2 instance using the IBM Db2 Universal Operator"):
                    self.setParam("db2_action_manage", "install")
                    self.printDescription([
                        "Available Db2 instance types for Manage:",
                        "  1. DB2 Warehouse (Default option)",
                        "  2. DB2 Online Transactional Processing (OLTP)"
                    ])
                    self.promptForListSelect(message="Select the Manage dedicated DB2 instance type", options=["db2wh", "db2oltp"], param="db2_type", default="1")
                else:
                    workspaceId = self.getParam("mas_workspace_id")
                    self.setParam("db2_action_manage", "byo")

                    self.selectLocalConfigDir()

                    # Check if a configuration already exists before creating a new one
                    jdbcCfgFile = path.join(self.localConfigDir, f"jdbc-{instanceId}-manage.yaml")
                    print_formatted_text(f"Searching for Manage database configuration file in {jdbcCfgFile} ...")
                    if path.exists(jdbcCfgFile):
                        if self.yesOrNo(f"Manage database configuration file 'jdbc-{instanceId}-manage.yaml' already exists.  Do you want to generate a new one"):
                            self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
                    else:
                        print_formatted_text(f"Expected file ({jdbcCfgFile}) was not found, generating a valid Manage database configuration file now ...")
                        self.generateJDBCCfg(instanceId=instanceId, scope="workspace-application", workspaceId=workspaceId, appId="manage", destination=jdbcCfgFile)
        else:
            self.setParam("db2_action_manage", "none")


        # Do we need to configure Db2u?
        if self.getParam("db2_action_system")  == "install" or self.getParam("db2_action_manage") == "install":
            self.printH2("Installation Namespace")
            self.promptForString("Install namespace", "db2_namespace", default="db2u")

            # Node Affinity & Tolerations
            # -------------------------------------------------------------------------
            self.printH2("Node Affinity and Tolerations")
            self.printDescription([
                "Note that the same settings are applied to both the IoT and Manage Db2 instances",
                "Use existing node labels and taints to control scheduling of the Db2 workload in your cluster",
                "For more information refer to the Red Hat documentation:",
                " - <u>https://docs.openshift.com/container-platform/4.12/nodes/scheduling/nodes-scheduler-node-affinity.html</u>",
                " - <u>https://docs.openshift.com/container-platform/4.12/nodes/scheduling/nodes-scheduler-taints-tolerations.html</u>"
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
                "Note that the same settings are applied to both the IoT and Manage Db2 instances"
            ])

            if self.yesOrNo("Customize CPU and memory request/limit"):
                self.promptForString(" + CPU Request", "db2_cpu_requests", default=self.getParam("db2_cpu_requests"))
                self.promptForString(" + CPU Limit", "db2_cpu_limits", default=self.getParam("db2_cpu_limits"))
                self.promptForString(" + Memory Request", "db2_memory_requests", default=self.getParam("db2_memory_requests"))
                self.promptForString(" + Memory Limit", "db2_memory_limits", default=self.getParam("db2_memory_limits"))

            self.printH2("Database Storage Capacity")
            self.printDescription([
                "Note that the same settings are applied to both the IoT and Manage Db2 instances"
            ])

            if self.yesOrNo("Customize storage capacity"):
                self.promptForString(" + Data Volume", "db2_data_storage_size", default=self.getParam("db2_data_storage_size"))
                self.promptForString(" + Temporary Volume", "db2_temp_storage_size", default=self.getParam("db2_temp_storage_size"))
                self.promptForString(" + Metadata Volume", "db2_meta_storage_size", default=self.getParam("db2_meta_storage_size"))
                self.promptForString(" + Transaction Logs Volume", "db2_logs_storage_size", default=self.getParam("db2_logs_storage_size"))
                self.promptForString(" + Backup Volume", "db2_backup_storage_size", default=self.getParam("db2_backup_storage_size"))
