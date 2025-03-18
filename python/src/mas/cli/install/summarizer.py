# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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


class InstallSummarizerMixin():
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

        if self.isSNO():
            self.printSummary("Single Node OpenShift", "Yes")
        else:
            self.printSummary("Single Node OpenShift", "No")

    def masSummary(self) -> None:
        operationalModeNames = ["", "Production", "Non-Production"]

        self.printH2("IBM Maximo Application Suite")
        self.printParamSummary("Instance ID", "mas_instance_id")
        self.printParamSummary("Workspace ID", "mas_workspace_id")
        self.printParamSummary("Workspace Name", "mas_workspace_name")

        print()
        self.printSummary("Operational Mode", operationalModeNames[self.operationalMode])
        if self.isAirgap():
            self.printSummary("Install Mode", "Disconnected Install")
        else:
            self.printSummary("Install Mode", "Connected Install")

        if "mas_domain" in self.params:
            print()
            self.printParamSummary("Domain Name", "mas_domain")
            self.printParamSummary("DNS Provider", "dns_provider")
            self.printParamSummary("Certificate Issuer", "mas_cluster_issuer")

            if self.getParam('dns_provider') == "cloudflare":
                self.printParamSummary("CloudFlare e-mail", "cloudflare_email")
                self.printParamSummary("CloudFlare API token", "cloudflare_apitoken")
                self.printParamSummary("CloudFlare zone", "cloudflare_zone")
                self.printParamSummary("CloudFlare subdomain", "cloudflare_subdomain")
            elif self.getParam('dns_provider') == "cis":
                pass
            elif self.getParam('dns_provider') == "route53":
                pass
            elif self.getParam('dns_provider') == "":
                pass

        if self.getParam("mas_manual_cert_mgmt") != "":
            print()
            self.printSummary("Manual Certificates", self.manualCertsDir)
        else:
            print()
            self.printSummary("Manual Certificates", "Not Configured")

        print()
        self.printParamSummary("Enable Guided Tour", "mas_enable_walkme")

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
        self.printParamSummary("Trust Default Cert Authorities", "mas_trust_default_cas")

        print()
        if self.localConfigDir is not None:
            self.printSummary("Additional Config", self.localConfigDir)
        else:
            self.printSummary("Additional Config", "Not Configured")
        if "mas_pod_templates_dir" in self.params:
            self.printParamSummary("Pod Templates", "mas_pod_templates_dir")
        else:
            self.printSummary("Pod Templates", "Not Configured")

    def iotSummary(self) -> None:
        if self.installIoT:
            self.printSummary("IoT", self.params["mas_app_channel_iot"])
            self.printSummary("+ MQTT Broker Storage Class", self.params["mas_app_settings_iot_mqttbroker_pvc_storage_class"])
            self.printSummary("+ FPL Storage Class", self.params["mas_app_settings_iot_fpl_pvc_storage_class"])
        else:
            self.printSummary("IoT", "Do Not Install")

    def monitorSummary(self) -> None:
        if self.installMonitor:
            self.printSummary("Monitor", self.params["mas_app_channel_monitor"])
        else:
            self.printSummary("Monitor", "Do Not Install")

    def arcgisSummary(self) -> None:
        if self.getParam("install_arcgis") != "":
            self.printSummary("Loc Srv Esri (arcgis)", self.params["mas_arcgis_channel"])
        else:
            self.printSummary("Loc Srv Esri (arcgis)", "Do Not Install")

    def predictSummary(self) -> None:
        if self.installPredict:
            self.printSummary("Predict", self.params["mas_app_channel_predict"])
        else:
            self.printSummary("Predict", "Do Not Install")

    def optimizerSummary(self) -> None:
        if self.installOptimizer:
            self.printSummary("Optimizer", self.params["mas_app_channel_optimizer"])
            self.printSummary(" + Plan", self.params["mas_app_plan_optimizer"])
        else:
            self.printSummary("Optimizer", "Do Not Install")

    def assistSummary(self) -> None:
        if self.installAssist:
            self.printSummary("Assist", self.params["mas_app_channel_assist"])
        else:
            self.printSummary("Assist", "Do Not Install")

    def inspectionSummary(self) -> None:
        if self.installInspection:
            self.printSummary("Visual Inspection", self.params["mas_app_channel_visualinspection"])
            self.printSummary(" + Storage Class", self.params["storage_class_rwx"])
        else:
            self.printSummary("Visual Inspection", "Do Not Install")

    def aibrokerSummary(self) -> None:
        if self.installAiBroker:
            self.printSummary("AI Broker", self.params["mas_app_channel_aibroker"])
            print_formatted_text(HTML("  <SkyBlue>+ Maximo AI Broker Settings</SkyBlue>"))
            self.printParamSummary("  + Storage provider", "mas_aibroker_storage_provider")
            self.printParamSummary("  + Storage access key", "mas_aibroker_storage_accesskey")
            self.printParamSummary("  + Storage secret key", "mas_aibroker_storage_secretkey")
            self.printParamSummary("  + Storage host", "mas_aibroker_storage_host")
            self.printParamSummary("  + Storage port", "mas_aibroker_storage_port")
            self.printParamSummary("  + Storage ssl", "mas_aibroker_storage_ssl")
            self.printParamSummary("  + Storage region", "mas_aibroker_storage_region")
            self.printParamSummary("  + Storage pipelines bucket", "mas_aibroker_storage_pipelines_bucket")
            self.printParamSummary("  + Storage tenants bucket", "mas_aibroker_storage_tenants_bucket")
            self.printParamSummary("  + Storage templates bucket", "mas_aibroker_storage_templates_bucket")
            self.printParamSummary("  + Watsonxai api key", "mas_aibroker_watsonxai_apikey")
            self.printParamSummary("  + Watsonxai machine learning url", "mas_aibroker_watsonxai_url")
            self.printParamSummary("  + Watsonxai project id", "mas_aibroker_watsonxai_project_id")
            self.printParamSummary("  + Database host", "mas_aibroker_db_host")
            self.printParamSummary("  + Database port", "mas_aibroker_db_port")
            self.printParamSummary("  + Database user", "mas_aibroker_db_user")
            self.printParamSummary("  + Database name", "mas_aibroker_db_database")
            self.printParamSummary("  + Database Secretname", "mas_aibroker_db_secret_name")
            self.printParamSummary("  + Database password", "mas_aibroker_db_secret_value")
        else:
            self.printSummary("AI Broker", "Do Not Install")

    def manageSummary(self) -> None:
        if self.installManage:
            self.printSummary(f"{'Manage foundation' if self.getParam('is_full_manage') == 'false' else 'Manage'}", self.params["mas_app_channel_manage"])
            if self.getParam("is_full_manage") != "false":
                print_formatted_text(HTML("  <SkyBlue>+ Components</SkyBlue>"))
                self.printSummary("  + ACM", "Enabled" if "acm=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Aviation", "Enabled" if "aviation=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Civil Infrastructure", "Enabled" if "civil=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Envizi", "Enabled" if "envizi=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Health", "Enabled" if "health=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + HSE", "Enabled" if "hse=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Maximo IT", "Enabled" if "icd=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Nuclear", "Enabled" if "nuclear=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Oil & Gas", "Enabled" if "oilandgas=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Connector for Oracle", "Enabled" if "oracleadapter=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Connector for SAP", "Enabled" if "sapadapter=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Service Provider", "Enabled" if "serviceprovider=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Spatial", "Enabled" if "spatial=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Strategize", "Enabled" if "strategize=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Transportation", "Enabled" if "transportation=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Tririga", "Enabled" if "tririga=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Utilities", "Enabled" if "utilities=" in self.getParam("mas_appws_components") else "Disabled")
                self.printSummary("  + Workday Applications", "Enabled" if "workday=" in self.getParam("mas_appws_components") else "Disabled")

                self.printParamSummary("+ Server bundle size", "mas_app_settings_server_bundles_size")
                self.printParamSummary("+ Enable JMS queues", "mas_app_settings_default_jms")
                self.printParamSummary("+ Server Timezone", "mas_app_settings_server_timezone")
                self.printParamSummary("+ Base Language", "mas_app_settings_base_lang")
                self.printParamSummary("+ Additional Languages", "mas_app_settings_secondary_langs")

                print_formatted_text(HTML("  <SkyBlue>+ Database Settings</SkyBlue>"))
                self.printParamSummary("  + Schema", "mas_app_settings_indexspace")
                self.printParamSummary("  + Username", "mas_app_settings_db2_schema")
                self.printParamSummary("  + Tablespace", "mas_app_settings_tablespace")
                self.printParamSummary("  + Indexspace", "mas_app_settings_indexspace")
        else:
            self.printSummary("Manage", "Do Not Install")

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

    def cp4dSummary(self) -> None:
        if self.deployCP4D:
            self.printH2("IBM Cloud Pak for Data Configuration")
            self.printParamSummary("Version", "cpd_product_version")
            if self.installPredict:
                self.printSummary("Watson Studio Local", "Install (Required by Maximo Predict)")
                self.printSummary("Watson Machine Learning", "Install (Required by Maximo Predict)")
                self.printSummary("Analytics Engine", "Install (Required by Maximo Predict)")
            else:
                self.printSummary("Watson Studio Local", "Install" if self.getParam("cpd_install_ws") == "true" else "Do Not Install")
                self.printSummary("Watson Machine Learning", "Install" if self.getParam("cpd_install_wml") == "true" else "Do Not Install")
                self.printSummary("Analytics Engine", "Install" if self.getParam("cpd_install_ae") == "true" else "Do Not Install")

            self.printSummary("SPSS Modeler", "Install" if self.getParam("cpd_install_spss") == "true" else "Do Not Install")
            self.printSummary("Cognos Analytics", "Install" if self.getParam("cpd_install_cognos") == "true" else "Do Not Install")

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

    def cosSummary(self) -> None:
        self.printH2("Cloud Object Storage")
        if self.getParam("cos_type") != "":
            self.printParamSummary("Type", "cos_type")
            if self.getParam("cos_resourcegroup") != "":
                self.printParamSummary("Resource Group", "cos_resourcegroup")
        else:
            self.printSummary("Type", "None")

    def eckSummary(self) -> None:
        self.printH2("Elastic Cloud on Kubernetes")
        if self.getParam("eck_action") == "install":
            self.printSummary("ECK Integration", "Enabled")
            self.printParamSummary("Logstash", "eck_enable_logstash")
            self.printParamSummary("Remote Elasticsearch hosts", "eck_remote_es_hosts")
            self.printParamSummary("Remote Elasticsearch username", "eck_remote_es_username")
        else:
            self.printSummary("ECK Integration", "Disabled")

    def turbonomicSummary(self) -> None:
        self.printH2("Turbonomic")
        if self.getParam("turbonomic_server_url") != "":
            self.printSummary("Turbonomic Integration", "Enabled")
            self.printParamSummary("Server URL", "turbonomic_server_url")
            self.printParamSummary("Server version", "turbonomic_server_version")
            self.printParamSummary("Target name", "turbonomic_target_name")
            self.printParamSummary("Username", "turbonomic_username")
            self.printSummary("Password", f"{self.getParam('turbonomic_password')[0:8]}&lt;snip&gt;")
        else:
            self.printSummary("Turbonomic Integration", "Disabled")

    def mongoSummary(self) -> None:
        self.printH2("MongoDb")
        if self.getParam("mongodb_action") == "install":
            self.printSummary("Type", "MongoCE Operator")
            self.printParamSummary("Install Namespace", "mongodb_namespace")
        elif self.getParam("mongodb_action") == "byo":
            self.printSummary("Type", "BYO (mongodb-system.yaml)")
        else:
            self.fatalError(f"Unexpected value for mongodb_action parameter: {self.getParam('mongodb_action')}")

    def kafkaSummary(self) -> None:
        if self.getParam("kafka_action_system") != "":
            self.printH2("Kafka")

            if self.getParam("kafka_provider") in ["strimzi", "redhat"]:
                self.printParamSummary("Provider", "kafka_provider")
                self.printParamSummary("Version", "kafka_version")
                self.printParamSummary("Install Namespace", "kafka_namespace")

            elif self.getParam("kafka_provider") == "ibm":
                self.printParamSummary("Resource group", "eventstreams_resourcegroup")
                self.printParamSummary("Instance name", "eventstreams_name")
                self.printParamSummary("Instance location", "eventstreams_location")

            elif self.getParam("kafka_provider") == "aws":
                self.printParamSummary("VPC ID", "vpc_id")
                self.printParamSummary("Instance region", "aws_region")
                self.printParamSummary("Instance username", "aws_kafka_user_name")
                self.printParamSummary("Instance type", "aws_msk_instance_type")
                self.printParamSummary("Number of broker nodes", "aws_msk_instance_number")
                self.printParamSummary("Storage size (GB)", "aws_msk_volume_size")
                self.printParamSummary("Availability Zone 1 CIDR", "aws_msk_cidr_az1")
                self.printParamSummary("Availability Zone 2 CIDR", "aws_msk_cidr_az2")
                self.printParamSummary("Availability Zone 3 CIDR", "aws_msk_cidr_az3")
                self.printParamSummary("Ingress CIDR", "aws_msk_ingress_cidr")
                self.printParamSummary("Egress CIDR", "aws_msk_egress_cidr")

    def grafanaSummary(self) -> None:
        self.printH2("Grafana")
        self.printSummary("Install Grafana", "Install" if self.getParam("grafana_action") == "install" else "Do Not Install")

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

        self.printH2("IBM Maximo Application Suite Applications")
        self.iotSummary()
        self.monitorSummary()
        self.manageSummary()
        self.arcgisSummary()
        self.predictSummary()
        self.optimizerSummary()
        self.assistSummary()
        self.inspectionSummary()
        self.aibrokerSummary()

        # Application Dependencies
        self.mongoSummary()
        self.db2Summary()
        self.cosSummary()
        self.kafkaSummary()
        self.cp4dSummary()
        self.grafanaSummary()
        self.turbonomicSummary()
