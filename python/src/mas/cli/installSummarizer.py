import logging
import yaml
from prompt_toolkit import print_formatted_text, HTML
from mas.devops.mas import isAirgapInstall
from mas.devops.ocp import getConsoleURL

logger = logging.getLogger(__name__)

class InstallSummarizerMixin():
    def ocpSummary(self) -> None:
        self.printH2("OpenShift Container Platform")
        self.printSummary("Storage Class Provider", self.storageClassProvider)
        self.printParamSummary("ReadWriteOnce Storage Class", "storage_class_rwo")
        self.printParamSummary("ReadWriteMany Storage Class", "storage_class_rwx")
        self.printSummary("Certificate Manager", self.params["cert_manager_provider"])

        if self.isSNO():
            self.printSummary("Single Node OpenShift", "Yes")
        else:
            self.printSummary("Single Node OpenShift", "No")

    def icrSummary(self) -> None:
        self.printH2("IBM Container Registry Credentials")
        self.printSummary("IBM Entitlement Key", f"{self.params['ibm_entitlement_key'][0:8]}&lt;snip&gt;")
        if self.args.dev_mode:
            self.printSummary("Artifactory Username", self.params['artifactory_username'])
            self.printSummary("Artifactory Token", f"{self.params['artifactory_token'][0:8]}&lt;snip&gt;")

    def masSummary(self) -> None:
        operationalModeNames=["", "Production", "Non-Production"]

        self.printH2("IBM Maximo Application Suite")
        self.printSummary("Instance ID", self.params['mas_instance_id'])
        self.printSummary("Workspace ID", self.params['mas_workspace_id'])
        self.printSummary("Workspace Name", self.params['mas_workspace_name'])
        self.printSummary(f"Operational Mode", operationalModeNames[self.operationalMode])
        if isAirgapInstall(self.dynamicClient):
            self.printSummary("Install Mode", "Disconnected Install")
        else:
            self.printSummary("Install Mode", "Connected Install")

        if "mas_domain" in self.params:
            self.printSummary("Domain Name", self.params['mas_domain'])
            self.printSummary("DNS Provider", self.params['dns_provider'])
            self.printSummary("Certificate Issuer", self.params['mas_cluster_issuer'])

            if self.params['dns_provider'] == "cloudflare":
                self.printSummary("CloudFlare e-mail", self.params["cloudflare_email"])
                self.printSummary("CloudFlare API token", self.params["cloudflare_apitoken"])
                self.printSummary("CloudFlare zone", self.params["cloudflare_zone"])
                self.printSummary("CloudFlare subdomain", self.params["cloudflare_subdomain"])
            elif self.params['dns_provider'] == "cis":
                pass
            elif self.params['dns_provider'] == "route53":
                pass
            elif self.params['dns_provider'] == "":
                pass

        self.printSummary("Catalog Version", self.params['mas_catalog_version'])
        self.printSummary("Subscription Channel", self.params['mas_channel'])
        self.printSummary("IBM Entitled Registry", self.params['mas_icr_cp'])
        self.printSummary("IBM Open Registry", self.params['mas_icr_cpopen'])

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
            self.printSummary("Manage", self.params["mas_app_channel_manage"])
            print_formatted_text(HTML(f"  <SkyBlue>+ Components</SkyBlue>"))
            self.printSummary("  + ACM", "Enabled" if "acm=" in self.getParam("mas_appws_components") else "Disabled")
            self.printSummary("  + Aviation", "Enabled" if "aviation=" in self.getParam("mas_appws_components") else "Disabled")
            self.printSummary("  + Civil Infrastructure", "Enabled" if "acm=" in self.getParam("mas_appws_components") else "Disabled")
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

            print_formatted_text(HTML(f"  <SkyBlue>+ Database Settings</SkyBlue>"))
            self.printParamSummary("  + Schema", "mas_app_settings_indexspace")
            self.printParamSummary("  + Username", "mas_app_settings_db2_schema")
            self.printParamSummary("  + Tablespace", "mas_app_settings_tablespace")
            self.printParamSummary("  + Indexspace", "mas_app_settings_indexspace")

        else:
            self.printSummary("Manage", "Do Not Install")

    def db2Summary(self) -> None:
        if self.getParam("db2_action_system") == "install" or self.getParam("db2_action_manage") == "install":
            self.printH2("IBM Db2 Univeral Operator Configuration")
            self.printParamSummary("Install Namespace", "db2_namespace")
            self.printParamSummary("Subscription Channel", "db2_channel")
            print()
            self.printParamSummary("System Instance", "db2_action_system")
            self.printParamSummary("Dedicated Manage Instance", "db2_action_manage")
            self.printParamSummary(" - Type", "db2_type")
            self.printParamSummary(" - Timezone", "db2_timezone")
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
            if self.getParam('db2_affinity_key') is not "":
                self.printSummary("Node Affinity", f"{self.getParam('db2_affinity_key')}={self.getParam('db2_affinity_value')}")
            else:
                self.printSummary("Node Affinity", "none")

            if self.getParam('db2_tolerate_key') is not "":
                self.printSummary("Node Tolerations", f"{self.getParam('db2_tolerate_key')}={self.getParam('db2_tolerate_value')} @ {self.getParam('db2_tolerate_effect')}")
            else:
                self.printSummary("Node Tolerations", "none")

    def cp4dSummary(self) -> None:
        if self.deployCP4D:
            self.printH2("IBM Cloud Pak for Data Configuration")
            self.printParamSummary("Version", "cpd_product_version")
            if self.installPredict:
                self.printSummary("Watson Studio Local", "Install (Required by Maximo Predict)")
                self.printSummary("Watson Machine Learning", "Install (Required by Maximo Predict)")
                self.printSummary("Analytics Engine", "Install (Required by Maximo Predict)")
            self.printSummary("Watson Openscale", "Install" if self.getParam("cpd_install_openscale") == "true" else "Do Not Install")
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
        self.printSummary("License File", self.slsLicenseFileLocal)
        self.printParamSummary("IBM Open Registry", "sls_icr_cpopen")

    def mongoSummary(self) -> None:
        self.printH2("MongoDb")
        self.printParamSummary("Install Namespace", "mongodb_namespace")


    # if [[ "$KAFKA_ACTION_SYSTEM" == "install" && ("$KAFKA_PROVIDER" == "strimzi" || "$KAFKA_PROVIDER" == "redhat") ]]; then
    #   reset_colors
    #   echo "${TEXT_DIM}"
    #   echo_h4 "Kafka" "    "
    #   echo_reset_dim "Install Namespace ......... ${COLOR_MAGENTA}${KAFKA_NAMESPACE:-<default>}"
    #   echo_reset_dim "Kafka Provider ............ ${COLOR_MAGENTA}${KAFKA_PROVIDER}"
    #   echo_reset_dim "Kafka Version ............. ${COLOR_MAGENTA}${KAFKA_VERSION}"
    # fi

    # if [[ "$KAFKA_ACTION_SYSTEM" == "install" && "$KAFKA_PROVIDER" == "ibm" ]]; then
    #   reset_colors
    #   echo "${TEXT_DIM}"
    #   echo_h4 "Kafka - IBM Cloud Event Streams" "    "
    #   echo_reset_dim "Resource group ............ ${COLOR_MAGENTA}${EVENTSTREAMS_RESOURCEGROUP}"
    #   echo_reset_dim "Instance name ............. ${COLOR_MAGENTA}${EVENTSTREAMS_NAME}"
    #   echo_reset_dim "Instance location ......... ${COLOR_MAGENTA}${EVENTSTREAMS_LOCATION}"
    # fi

    # if [[ "$KAFKA_ACTION_SYSTEM" == "install" && "$KAFKA_PROVIDER" == "aws" ]]; then
    #   reset_colors
    #   echo "${TEXT_DIM}"
    #   echo_h4 "Kafka - AWS MSK" "    "
    #   echo_reset_dim "VPC ID .................... ${COLOR_MAGENTA}${VPC_ID}"
    #   echo_reset_dim "Instance region ........... ${COLOR_MAGENTA}${AWS_REGION}"
    #   echo_reset_dim "Instance username ......... ${COLOR_MAGENTA}${AWS_KAFKA_USER_NAME}"
    #   echo_reset_dim "Instance type ............. ${COLOR_MAGENTA}${AWS_MSK_INSTANCE_TYPE}"
    #   echo_reset_dim "Number of broker nodes .... ${COLOR_MAGENTA}${AWS_MSK_INSTANCE_NUMBER}"
    #   echo_reset_dim "Storage size (GB) ......... ${COLOR_MAGENTA}${AWS_MSK_VOLUME_SIZE}"
    #   echo_reset_dim "Availability Zone 1 CIDR .. ${COLOR_MAGENTA}${AWS_MSK_CIDR_AZ1}"
    #   echo_reset_dim "Availability Zone 2 CIDR .. ${COLOR_MAGENTA}${AWS_MSK_CIDR_AZ2}"
    #   echo_reset_dim "Availability Zone 3 CIDR .. ${COLOR_MAGENTA}${AWS_MSK_CIDR_AZ3}"
    #   echo_reset_dim "Ingress CIDR .............. ${COLOR_MAGENTA}${AWS_MSK_INGRESS_CIDR}"
    #   echo_reset_dim "Egress CIDR ............... ${COLOR_MAGENTA}${AWS_MSK_EGRESS_CIDR}"
    # fi

    # reset_colors
    # echo "${TEXT_DIM}"
    # echo_h4 "Grafana" "    "
    # if [[ "${GRAFANA_ACTION}" == 'install' ]]
    #   then echo_reset_dim "Include Grafana ........... ${COLOR_MAGENTA}Yes"
    #   else echo_reset_dim "Include Grafana ........... ${COLOR_RED}Package not available"
    # fi



    # reset_colors
    # echo "${TEXT_DIM}"
    # echo_h4 "Workload Scale Configuration" "    "
    # if [[ -n "${MAS_WORKLOAD_SCALE_PROFILE}" ]]; then
    #   if [[ "$MAS_WORKLOAD_SCALE_PROFILE" == "Custom" ]]; then
    #     echo_reset_dim "Workload Scale Profile .... ${COLOR_MAGENTA}${MAS_WORKLOAD_SCALE_PROFILE}"
    #     echo_reset_dim "Configuration(s) .......... ${COLOR_MAGENTA}${MAS_POD_TEMPLATES_DIR}"
    #   else
    #     echo_reset_dim "Workload Scale Profile .... ${COLOR_MAGENTA}${MAS_WORKLOAD_SCALE_PROFILE}"
    #   fi
    # else
    #   echo_reset_dim "Workload Scale Profile .... ${COLOR_MAGENTA}Burstable"
    # fi

    # reset_colors
    # echo "${TEXT_DIM}"
    # echo_h4 "Cluster Ingress Configuration" "    "
    # echo_reset_dim "Certificate Secret ........ ${COLOR_MAGENTA}${OCP_INGRESS_TLS_SECRET_NAME:-<default>}"

    def displayInstallSummary(self) -> None:
        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        logger.debug("PipelineRun parameters:")
        logger.debug(yaml.dump(self.params, default_flow_style = False))

        # Cluster Config & Dependencies
        self.ocpSummary()
        self.icrSummary()
        self.droSummary()
        self.slsSummary()
        self.masSummary()

        self.printH2("IBM Maximo Application Suite Applications")
        self.iotSummary()
        self.monitorSummary()
        self.manageSummary()
        self.predictSummary()
        self.optimizerSummary()
        self.assistSummary()
        self.inspectionSummary()

        # Application Dependencies
        self.mongoSummary()
        self.db2Summary()
        self.cp4dSummary()
