# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
import yaml
from prompt_toolkit import print_formatted_text, HTML
from mas.devops.ocp import getConsoleURL

logger = logging.getLogger(__name__)


class aiServiceInstallSummarizerMixin():
    def ocpSummary(self) -> None:
        self.printH2("Pipeline Configuration")
        self.printParamSummary("Service Account", "service_account_name")
        self.printParamSummary("Image Pull Policy", "image_pull_policy")
        self.printSummary("Skip Pre-Install Healthcheck", "Yes" if self.getParam('skip_pre_check') == "true" else "No")

        self.printH2("OpenShift Container Platform")
        self.printSummary("Worker Node Architecture", self.architecture)
        self.printSummary("Storage Class Provider", self.storageClassProvider)
        self.printParamSummary("ReadWriteOnce Storage Class", "storage_class_rwo")
        self.printParamSummary("ReadWriteMany Storage Class", "storage_class_rwx")

        self.printParamSummary("Certificate Manager", "cert_manager_provider")
        self.printParamSummary("Cluster Ingress Certificate Secret", "ocp_ingress_tls_secret_name")

    def masSummary(self) -> None:

        self.printH2("IBM Maximo Application Suite")

        print()
        self.printParamSummary("Catalog Version", "mas_catalog_version")
        # We only list the digest if it's specified (primary use case is when running development builds in airgap environments)
        if self.getParam("mas_catalog_digest" != ""):
            self.printParamSummary("Catalog Digest", "mas_catalog_digest")
        self.printParamSummary("Subscription Channel", "mas_channel")

        print()
        self.printParamSummary("IBM Entitled Registry", "mas_icr_cp")
        self.printParamSummary("IBM Open Registry", "mas_icr_cpopen")

        print()
        if self.localConfigDir is not None:
            self.printSummary("Additional Config", self.localConfigDir)
        else:
            self.printSummary("Additional Config", "Not Configured")

    def aibrokerSummary(self) -> None:
        if self.installAiBroker:
            self.printSummary("AI Broker", self.params["mas_app_channel_aibroker"])
            print_formatted_text(HTML("  <SkyBlue>+ Maximo AI Broker Settings</SkyBlue>"))
            self.printParamSummary("  + Aibroker Instance Id", "aibroker_instance_id")
            self.printParamSummary("  + Storage provider", "mas_aibroker_storage_provider")
            if self.getParam("mas_aibroker_storage_provider") == "minio":
                self.printParamSummary("  + minio root username", "minio_root_user")
            if self.getParam("mas_app_channel_aibroker") != "9.0.x":
                self.printParamSummary("  + Mariadb username", "mariadb_user")
                self.printParamSummary("  + Mariadb password", "mariadb_password")
            self.printParamSummary("  + Storage access key", "mas_aibroker_storage_accesskey")
            self.printParamSummary("  + Storage host", "mas_aibroker_storage_host")
            self.printParamSummary("  + Storage port", "mas_aibroker_storage_port")
            self.printParamSummary("  + Storage ssl", "mas_aibroker_storage_ssl")
            self.printParamSummary("  + Storage region", "mas_aibroker_storage_region")
            self.printParamSummary("  + Storage pipelines bucket", "mas_aibroker_storage_pipelines_bucket")
            self.printParamSummary("  + Storage tenants bucket", "mas_aibroker_storage_tenants_bucket")
            self.printParamSummary("  + Storage templates bucket", "mas_aibroker_storage_templates_bucket")
            self.printParamSummary("  + Watsonxai machine learning url", "mas_aibroker_watsonxai_url")
            self.printParamSummary("  + Watsonxai project id", "mas_aibroker_watsonxai_project_id")
            self.printParamSummary("  + Database host", "mas_aibroker_db_host")
            self.printParamSummary("  + Database port", "mas_aibroker_db_port")
            self.printParamSummary("  + Database user", "mas_aibroker_db_user")
            self.printParamSummary("  + Database name", "mas_aibroker_db_database")
            if self.getParam("mas_app_channel_aibroker") != "9.0.x":
                self.printParamSummary("  + Tenant entitlement type", "tenant_entitlement_type")
                self.printParamSummary("  + Tenant start date", "tenant_entitlement_start_date")
                self.printParamSummary("  + Tenant end date", "tenant_entitlement_end_date")
                self.printParamSummary("  + S3 bucket prefix", "mas_aibroker_s3_bucket_prefix")
                self.printParamSummary("  + S3 endpoint url", "mas_aibroker_s3_endpoint_url")
                self.printParamSummary("  + S3 bucket prefix (tenant level)", "mas_aibroker_tenant_s3_bucket_prefix")
                self.printParamSummary("  + S3 region (tenant level)", "mas_aibroker_tenant_s3_region")
                self.printParamSummary("  + S3 endpoint url (tenant level)", "mas_aibroker_tenant_s3_endpoint_url")
                self.printParamSummary("  + RSL url", "rsl_url")
                self.printParamSummary("  + ORG Id of RSL", "rsl_org_id")
                self.printParamSummary("  + Token for RSL", "rsl_token")
                self.printParamSummary("  + Install minio", "install_minio_aiservice")
                self.printParamSummary("  + Install SLS", "install_sls_aiservice")
                if self.getParam("install_sls_aiservice") != "true":
                    self.printParamSummary("  + SLS secret name", "mas_aibroker_sls_secret_name")
                    self.printParamSummary("  + SLS registration key", "mas_aibroker_sls_registration_key")
                    self.printParamSummary("  + SLS URL", "mas_aibroker_sls_url")
                self.printParamSummary("  + Install DRO", "install_dro_aiservice")
                if self.getParam("install_dro_aiservice") != "true":
                    self.printParamSummary("  + DRO secret name", "mas_aibroker_dro_secret_name")
                    self.printParamSummary("  + DRO API key", "mas_aibroker_dro_api_key")
                    self.printParamSummary("  + DRO URL", "mas_aibroker_dro_url")
                self.printParamSummary("  + Install DB2", "install_db2_aiservice")
                if self.getParam("install_db2_aiservice") != "true":
                    self.printParamSummary("  + DB2 username", "mas_aibroker_db2_username")
                    self.printParamSummary("  + DB2 JDBC URL", "mas_aibroker_db2_jdbc_url")
                    self.printParamSummary("  + DB2 SSL enabled", "mas_aibroker_db2_ssl_enabled")
                self.printParamSummary("  + Environment type", "environment_type")

        else:
            self.printSummary("AI Broker", "Do Not Install")

    def db2Summary(self) -> None:
        if self.getParam("db2_action_system") == "install" or self.getParam("db2_action_manage") == "install":
            self.printH2("IBM Db2 Univeral Operator Configuration")
            self.printSummary("System Instance", "Install" if self.getParam("db2_action_system") == "install" else "Do Not Install")
            self.printSummary("Dedicated Manage Instance", "Install" if self.getParam("db2_action_manage") == "install" else "Do Not Install")
            self.printParamSummary(" - Type", "db2_type")
            self.printParamSummary(" - Timezone", "db2_timezone")
            print()
            self.printParamSummary("Install Namespace", "db2_namespace")
            self.printParamSummary("Subscription Channel", "db2_channel")
            print()
            self.printParamSummary("CPU Request", "db2_cpu_requests")
            self.printParamSummary("CPU Limit", "db2_cpu_limits")
            self.printParamSummary("Memory Request", "db2_memory_requests")
            self.printParamSummary("Memory Limit ", "db2_memory_limits")
            print()
            self.printParamSummary("Meta Storage", "db2_meta_storage_size")
            self.printParamSummary("Data Storage", "db2_data_storage_size")
            self.printParamSummary("Backup Storage", "db2_backup_storage_size")
            self.printParamSummary("Temp Storage", "db2_temp_storage_size")
            self.printParamSummary("Transaction Logs Storage", "db2_logs_storage_size")
            print()
            if self.getParam('db2_affinity_key') != "":
                self.printSummary("Node Affinity", f"{self.getParam('db2_affinity_key')}={self.getParam('db2_affinity_value')}")
            else:
                self.printSummary("Node Affinity", "None")

            if self.getParam('db2_tolerate_key') != "":
                self.printSummary("Node Tolerations", f"{self.getParam('db2_tolerate_key')}={self.getParam('db2_tolerate_value')} @ {self.getParam('db2_tolerate_effect')}")
            else:
                self.printSummary("Node Tolerations", "None")

    def droSummary(self) -> None:
        self.printH2("IBM Data Reporter Operator (DRO) Configuration")
        self.printParamSummary("Contact e-mail", "uds_contact_email")
        self.printParamSummary("First name", "uds_contact_firstname")
        self.printParamSummary("Last name", "uds_contact_lastname")
        self.printParamSummary("Install Namespace", "dro_namespace")

    def slsSummary(self) -> None:
        self.printH2("IBM Suite License Service")
        self.printParamSummary("Namespace", "sls_namespace")
        if self.getParam("sls_action") == "install":
            self.printSummary("Subscription Channel", "3.x")
            self.printParamSummary("IBM Open Registry", "sls_icr_cpopen")
            if self.slsLicenseFileLocal:
                self.printSummary("License File", self.slsLicenseFileLocal)

    def mongoSummary(self) -> None:
        self.printH2("MongoDb")
        if self.getParam("mongodb_action") == "install":
            self.printSummary("Type", "MongoCE Operator")
            self.printParamSummary("Install Namespace", "mongodb_namespace")
        elif self.getParam("mongodb_action") == "byo":
            self.printSummary("Type", "BYO (mongodb-system.yaml)")
        else:
            self.fatalError(f"Unexpected value for mongodb_action parameter: {self.getParam('mongodb_action')}")

    def displayInstallSummary(self) -> None:
        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        logger.debug("PipelineRun parameters:")
        logger.debug(yaml.dump(self.params, default_flow_style=False))

        # Cluster Config & Dependencies
        self.ocpSummary()
        self.droSummary()
        self.slsSummary()
        self.masSummary()
        self.printH2("IBM Maximo Application Suite Application - Aiservice")
        self.aibrokerSummary()

        # Application Dependencies
        self.mongoSummary()
        self.db2Summary()
