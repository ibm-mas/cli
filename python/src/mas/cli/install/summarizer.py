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
import yaml
from typing import TYPE_CHECKING
from prompt_toolkit import print_formatted_text, HTML
from mas.devops.ocp import getConsoleURL

if TYPE_CHECKING:
    from typing import Dict

logger = logging.getLogger(__name__)


class InstallSummarizerMixin:
    if TYPE_CHECKING:
        from typing import List, NoReturn
        from openshift.dynamic import DynamicClient

        # Attributes from BaseApp and other mixins
        params: Dict[str, str]
        enableKafkaImageProcessor: bool
        architecture: str
        storageClassProvider: str
        operationalMode: int
        manualCertsDir: str | None
        localConfigDir: str | None
        slsLicenseFileLocal: str | None
        aiserviceTenantSchedulingConfigFileLocal: str | None
        deployCP4D: bool
        installAssist: bool
        installIoT: bool
        installMonitor: bool
        installManage: bool
        installPredict: bool
        installInspection: bool
        installOptimizer: bool
        installFacilities: bool
        installAIService: bool
        installArcgis: bool
        dynamicClient: DynamicClient
        applyPreInstallMASRBAC: bool

        # Methods from BaseApp
        def getParam(self, param: str) -> str: ...

        def isSNO(self) -> bool: ...

        def isAirgap(self) -> bool: ...

        def fatalError(self, message: str, exception: Exception | None = None) -> NoReturn: ...

        # Methods from PrintMixin
        def printH1(self, message: str) -> None: ...

        def printH2(self, message: str) -> None: ...

        def printDescription(self, content: List[str]) -> None: ...

        def printSummary(self, label: str, value: str | None) -> None: ...

        def printParamSummary(self, label: str, param: str) -> None: ...

    def ocpSummary(self) -> None:
        self.printH2("Pipeline Configuration")
        self.printParamSummary("Service Account", "service_account_name")
        self.printParamSummary("Image Pull Policy", "image_pull_policy")
        if self.useCliDigest:
            if self.cliDigest:
                self.printSummary("Use CLI Digest", self.cliDigest)
            else:
                self.printParamSummary("Use CLI Digest", "Yes (auto-lookup)")

        self.printSummary(
            "Skip Pre-Install Healthcheck",
            "Yes" if self.getParam("skip_pre_check") == "true" else "No",
        )

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
        if self.mas_admin_mode != "":
            self.printSummary("MAS Admin Mode", self.mas_admin_mode)
            self.printSummary(
                "Apply Pre-Install MAS RBAC",
                "Yes" if self.applyPreInstallMASRBAC else "No",
            )
        if self.getParam("mas_issuer_kind") != "":
            self.printParamSummary("Mas Certificate Issuer Kind", "mas_issuer_kind")
        if self.isAirgap():
            self.printSummary("Install Mode", "Disconnected Install")
        else:
            self.printSummary("Install Mode", "Connected Install")

        if "mas_domain" in self.params:
            print()
            self.printParamSummary("Domain Name", "mas_domain")
            self.printParamSummary("DNS Provider", "dns_provider")
            self.printParamSummary("Certificate Issuer", "mas_cluster_issuer")

            if self.getParam("ocp_ingress") != "":
                self.printParamSummary("OCP Ingress", "ocp_ingress")
            if self.getParam("dns_provider") == "cloudflare":
                self.printParamSummary("CloudFlare e-mail", "cloudflare_email")
                self.printParamSummary("CloudFlare API token", "cloudflare_apitoken")
                self.printParamSummary("CloudFlare zone", "cloudflare_zone")
                self.printParamSummary("CloudFlare subdomain", "cloudflare_subdomain")
            elif self.getParam("dns_provider") == "cis":
                self.printParamSummary("CIS e-mail", "cis_email")
                self.printParamSummary("CIS API Key", "cis_apikey")
                self.printParamSummary("CIS CRN", "cis_crn")
                self.printParamSummary("CIS subdomain", "cis_subdomain")
            elif self.getParam("dns_provider") == "route53":
                pass
            elif self.getParam("dns_provider") == "":
                pass

        print()
        self.printParamSummary("Network Routing Mode", "mas_routing_mode")
        if self.getParam("mas_routing_mode") == "path":
            self.printParamSummary("IngressController Name", "mas_ingress_controller_name")
            self.printParamSummary("Configure IngressController", "mas_configure_ingress")

        if self.getParam("mas_manual_route_mgmt") == "true":
            self.printParamSummary("Manual Routes", "mas_manual_route_mgmt")

        self.printParamSummary("Use Service Mesh", "mas_use_service_mesh")

        print()
        self.printParamSummary("Configure Suite to run in IPV6", "enable_ipv6")

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
        if self.getParam("mas_catalog_digest") != "":
            self.printParamSummary("Catalog Digest", "mas_catalog_digest")
        self.printParamSummary("Subscription Channel", "mas_channel")

        print()
        self.printParamSummary("IBM Entitled Registry", "mas_icr_cp")
        self.printParamSummary("IBM Open Registry", "mas_icr_cpopen")

        print()
        self.printParamSummary("Enable feature adoption metrics", "mas_feature_usage")

        print()
        self.printParamSummary("Enable deployment progression metrics", "mas_deployment_progression")

        print()
        self.printParamSummary("Enable usability metrics", "mas_usability_metrics")

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
            self.printSummary(
                "+ MQTT Broker Storage Class",
                self.params["mas_app_settings_iot_mqttbroker_pvc_storage_class"],
            )
            self.printSummary(
                "+ FPL Storage Class",
                self.params["mas_app_settings_iot_fpl_pvc_storage_class"],
            )
        else:
            self.printSummary("IoT", "Do Not Install")

    def monitorSummary(self) -> None:
        if self.installMonitor:
            self.printSummary("Monitor", self.params["mas_app_channel_monitor"])
        else:
            self.printSummary("Monitor", "Do Not Install")

    def arcgisSummary(self) -> None:
        if self.installArcgis:
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

    def manageSummary(self) -> None:
        if self.installManage:
            self.printSummary(
                f"{'Manage foundation' if self.getParam('mas_appws_components') == '' else 'Manage'}",
                self.params["mas_app_channel_manage"],
            )
            if self.getParam("mas_appws_components") != "":
                print_formatted_text(HTML("  <SkyBlue>+ Components</SkyBlue>"))

                # Define components with their display names and component IDs
                components = [
                    ("ACM", "acm"),
                    ("Aviation", "aviation"),
                    ("Civil Infrastructure", "civil"),
                    ("Envizi", "envizi"),
                    ("Health", "health"),
                    ("HSE", "hse"),
                    ("Maximo IT", "icd"),
                    ("Nuclear", "nuclear"),
                    ("Oil & Gas", "oilandgas"),
                    ("Connector for Oracle", "oracleadapter"),
                    ("Connector for SAP", "sapadapter"),
                    ("Service Provider", "serviceprovider"),
                    ("Spatial", "spatial"),
                    ("Strategize", "strategize"),
                    ("Transportation", "transportation"),
                    ("Tririga", "tririga"),
                    ("Utilities", "utilities"),
                    ("Workday Applications", "workday"),
                    ("AIP", "aip"),
                    ("Vegetation Management", "vegm"),
                ]

                componentsStr = self.getParam("mas_appws_components")
                for displayName, componentId in components:
                    isEnabled = f"{componentId}=" in componentsStr
                    self.printSummary(f"  + {displayName}", "Enabled" if isEnabled else "Disabled")

                    # Special handling for Civil Infrastructure Kafka Image Processor
                    if componentId == "civil" and isEnabled:
                        self.printSummary("    + Kafka Image Processor", "Enabled" if self.enableKafkaImageProcessor else "Disabled")
                        if self.enableKafkaImageProcessor:
                            self.printParamSummary("    + Kafka Binding", "mas_appws_bindings_kafka_manage")

                self.printParamSummary("+ Upgrade Type", "mas_appws_upgrade_type")

                self.printParamSummary("+ Server bundle size", "mas_app_settings_server_bundles_size")
                self.printParamSummary("+ Enable JMS queues", "mas_app_settings_default_jms")
                self.printParamSummary("+ Server Timezone", "mas_app_settings_server_timezone")
                self.printParamSummary("+ Base Language", "mas_app_settings_base_lang")
                self.printParamSummary("+ Additional Languages", "mas_app_settings_secondary_langs")

                print_formatted_text(HTML("  <SkyBlue>+ Database Settings</SkyBlue>"))
                self.printParamSummary("  + Schema", "mas_app_settings_db2_schema")
                self.printParamSummary("  + Tablespace", "mas_app_settings_tablespace")
                self.printParamSummary("  + Indexspace", "mas_app_settings_indexspace")

            if self.getParam("manage_bind_aiservice_tenant_id") != "":
                print_formatted_text(HTML("  <SkyBlue>+ AI Service Binding (for Manage)</SkyBlue>"))
                self.printParamSummary(
                    "  + Bound AI Service Instance ID",
                    "manage_bind_aiservice_instance_id",
                )
                self.printParamSummary("  + Bound AI Service Tenant ID", "manage_bind_aiservice_tenant_id")
        else:
            self.printSummary("Manage", "Do Not Install")

    def facilitiesSummary(self) -> None:
        # TODO: Fix type for storage sizes and max conn pool size
        if self.installFacilities:
            self.printSummary("Facilities", self.params["mas_app_channel_facilities"])
            print_formatted_text(HTML("  <SkyBlue>+ Maximo Real Estate and Facilities Settings</SkyBlue>"))
            self.printParamSummary("  + Size", "mas_ws_facilities_size")
            self.printParamSummary(
                "  + Application Object Migration",
                "mas_ws_facilities_app_om_upgrade_mode",
            )
            self.printParamSummary("  + Routes Timeout", "mas_ws_facilities_routes_timeout")
            self.printParamSummary("  + XML Extension", "mas_ws_facilities_liberty_extension_XML")
            self.printParamSummary("  + AES vault secret name", "mas_ws_facilities_vault_secret")
            # self.printParamSummary("  + Dedicated Workflow Agents", "mas_ws_facilities_dwfagents")
            # self.printParamSummary("  + Maximum pool size connection ", "mas_ws_facilities_db_maxconnpoolsize")
            self.printParamSummary("  + Log Storage Class ", "mas_ws_facilities_storage_log_class")
            self.printParamSummary("  + Log Storage Mode", "mas_ws_facilities_storage_log_mode")
            # self.printParamSummary("  + Log Storage Size", "mas_ws_facilities_storage_log_size")
            self.printParamSummary(
                "  + Userfiles Storage Class ",
                "mas_ws_facilities_storage_userfiles_class",
            )
            self.printParamSummary(
                "  + User files Storage Mode",
                "mas_ws_facilities_storage_userfiles_mode",
            )
            # self.printParamSummary("  + User files Storage Size", "mas_ws_facilities_storage_userfiles_size")
            self.printParamSummary("  + Custom FACILITIES.properties", "mas_ws_facilities_custom_properties")
            self.printParamSummary("  + Custom FACILITIES.properties File path", "mas_ws_facilities_properties_file_local")
            self.printParamSummary("  + Custom FACILITIES.properties Secret Name", "mas_ws_facilities_properties_secret_name")
            if self.getParam("db2_action_facilities") == "none":
                self.printParamSummary("  + Dedicated DB2 Database", "No")
            else:
                self.printParamSummary("  + Dedicated DB2 Database", "db2_action_facilities")
        else:
            self.printSummary("Facilities", "Do Not Install")

    def aiServiceSummary(self) -> None:
        if self.installAIService:
            self.printH2("AI Service")
            self.printParamSummary("Release", "aiservice_channel")
            self.printParamSummary("Instance ID", "aiservice_instance_id")
            self.printParamSummary("Environment Type", "environment_type")

            if "aiservice_certificate_issuer" in self.params:
                self.printParamSummary("Certificate Issuer", "aiservice_certificate_issuer")

            self.printH2("AI Service Tenant Configuration")
            self.printParamSummary("Entitlement Type", "tenant_entitlement_type")
            self.printParamSummary("Start Date", "tenant_entitlement_start_date")
            self.printParamSummary("End Date", "tenant_entitlement_end_date")
            if self.aiserviceTenantSchedulingConfigFileLocal:
                self.printSummary(
                    "Scheduling configuration file",
                    self.aiserviceTenantSchedulingConfigFileLocal,
                )

            self.printH2("S3 Configuration")
            # self.printParamSummary("Storage provider", "aiservice_s3_provider")
            if self.getParam("minio_root_user") is not None and self.getParam("minio_root_user") != "":
                self.printParamSummary("Minio Root Username", "minio_root_user")
            print()
            self.printParamSummary("Host", "aiservice_s3_host")
            self.printParamSummary("Port", "aiservice_s3_port")
            self.printParamSummary("SSL Enabled", "aiservice_s3_ssl")
            self.printParamSummary("Region", "aiservice_s3_region")
            self.printParamSummary("Bucket Prefix", "aiservice_s3_bucket_prefix")
            self.printParamSummary("Templates Bucket Name", "aiservice_s3_templates_bucket")
            self.printParamSummary("Tenants Bucket Name", "aiservice_s3_tenants_bucket")

            self.printH2("IBM WatsonX")
            self.printParamSummary("URL", "aiservice_watsonxai_url")
            self.printParamSummary("Project ID", "aiservice_watsonxai_project_id")

    def db2Summary(self) -> None:
        if self.getParam("db2_action_system") == "install" or self.getParam("db2_action_manage") == "install":
            self.printH2("IBM Db2 Univeral Operator Configuration")
            self.printSummary(
                "System Instance",
                ("Install" if self.getParam("db2_action_system") == "install" else "Do Not Install"),
            )
            self.printSummary(
                "Dedicated Manage Instance",
                ("Install" if self.getParam("db2_action_manage") == "install" else "Do Not Install"),
            )
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
            if self.getParam("db2_affinity_key") != "":
                self.printSummary(
                    "Node Affinity",
                    f"{self.getParam('db2_affinity_key')}={self.getParam('db2_affinity_value')}",
                )
            else:
                self.printSummary("Node Affinity", "None")

            if self.getParam("db2_tolerate_key") != "":
                self.printSummary(
                    "Node Tolerations",
                    f"{self.getParam('db2_tolerate_key')}={self.getParam('db2_tolerate_value')} @ {self.getParam('db2_tolerate_effect')}",
                )
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
                self.printSummary(
                    "Watson Studio Local",
                    ("Install" if self.getParam("cpd_install_ws") == "true" else "Do Not Install"),
                )
                self.printSummary(
                    "Watson Machine Learning",
                    ("Install" if self.getParam("cpd_install_wml") == "true" else "Do Not Install"),
                )
                self.printSummary(
                    "Analytics Engine",
                    ("Install" if self.getParam("cpd_install_ae") == "true" else "Do Not Install"),
                )

            self.printSummary(
                "Cognos Analytics",
                ("Install" if self.getParam("cpd_install_cognos") == "true" else "Do Not Install"),
            )

    def droSummary(self) -> None:
        self.printH2("IBM Data Reporter Operator (DRO) Configuration")
        self.printParamSummary("Contact e-mail", "dro_contact_email")
        self.printParamSummary("First name", "dro_contact_firstname")
        self.printParamSummary("Last name", "dro_contact_lastname")
        self.printParamSummary("Install Namespace", "dro_namespace")

    def slsSummary(self) -> None:
        self.printH2("IBM Suite License Service")
        self.printParamSummary("Namespace", "sls_namespace")
        if self.getParam("sls_action") == "install":
            if self.getParam("sls_channel") != "":
                self.printSummary("Subscription Channel", self.getParam("sls_channel"))
            else:
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
        if self.getParam("grafana_action") == "install":
            self.printSummary("Install Grafana", "Install")
            self.printParamSummary("Grafana namespace", "grafana_v5_namespace")
            self.printParamSummary("Grafana storage size", "grafana_instance_storage_size")
        else:
            self.printSummary("Install Grafana", "Do Not Install")

    def slackSummary(self) -> None:
        self.printH2("Slack Integration")
        if self.getParam("slack_channel") != "":
            self.printParamSummary("Slack Channel", "slack_channel")
        else:
            self.printSummary("Slack Channel", "Not Configured")

    def installSummary(self) -> None:
        pass
        # self.printH2("Install Process")

    def displayInstallSummary(self) -> None:
        self.printH1("Review Settings")
        self.printDescription(["Connected to:", f" - <u>{getConsoleURL(self.dynamicClient)}</u>"])

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
        self.facilitiesSummary()
        self.aiServiceSummary()

        # Application Dependencies
        self.mongoSummary()
        self.db2Summary()
        self.cosSummary()
        self.kafkaSummary()
        self.cp4dSummary()
        self.grafanaSummary()

        # Notification Integration
        self.slackSummary()

        # Install options
        self.installSummary()
