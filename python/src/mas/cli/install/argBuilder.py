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

logger = logging.getLogger(__name__)


class installArgBuilderMixin():
    def buildCommand(self) -> str:
        # MAS Catalog Selection & Entitlement
        # -----------------------------------------------------------------------------
        newline = " \\\n"
        command = "export IBM_ENTITLEMENT_KEY=x\n"
        if self.getParam('ibmcloud_apikey') != "":
            command += "export IBMCLOUD_APIKEY=x\n"
        if self.getParam('aws_access_key_id') != "":
            command += "export AWS_ACCESS_KEY_ID=x\n"
        if self.getParam('secret_access_key') != "":
            command += "export SECRET_ACCESS_KEY=x\n"
        if self.getParam('artifactory_username') != "":
            command += "export ARTIFACTORY_USERNAME=x\nexport ARTIFACTORY_TOKEN=x\n"

        if self.getParam('mas_superuser_password') != "":
            command += "export SUPERUSER_PASSWORD=x\n"

        if self.getParam('eck_remote_es_password') != "":
            command += "export ES_PASSWORD=x\n"
        if self.getParam('kafka_password') != "":
            command += "export KAFKA_PASSWORD=x\n"

        if self.getParam('mas_app_settings_customization_archive_password') != "":
            command += "export CUSTOMIZATION_PASSWORD=x\n"
        if self.getParam('mas_app_settings_crypto_key') != "":
            command += "export CRYPTO_KEY=x\n"
        if self.getParam('mas_app_settings_cryptox_key') != "":
            command += "export CRYPTOX_KEY=x\n"
        if self.getParam('mas_app_settings_old_crypto_key') != "":
            command += "export OLD_CRYPTO_KEY=x\n"
        if self.getParam('mas_app_settings_old_cryptox_key') != "":
            command += "export OLD_CRYTPOX_KEY=x\n"

        command += f"mas install --mas-catalog-version {self.getParam('mas_catalog_version')}"

        if self.getParam('mas_catalog_digest') != "":
            command += f" --mas-catalog-digest {self.getParam('mas_catalog_digest')}"

        command += f" --ibm-entitlement-key $IBM_ENTITLEMENT_KEY{newline}"

        # MAS Basic Configuration
        # -----------------------------------------------------------------------------
        command += f"  --mas-channel {self.getParam('mas_channel')}"
        command += f" --mas-instance-id {self.getParam('mas_instance_id')}"
        command += f" --mas-workspace-id {self.getParam('mas_workspace_id')}"
        command += f" --mas-workspace-name \"{self.getParam('mas_workspace_name')}\"{newline}"

        if self.getParam('mas_special_characters') == "true":
            command += f" --allow-special-chars \"{self.getParam('mas_special_characters')}\"{newline}"

        # ECK Integration
        # -----------------------------------------------------------------------------
        if self.getParam('eck_action') == "install":
            command += "--eck"
        if self.getParam('eck_enable_logstash') == "true":
            command += f"--eck-enable-logstash{newline}"
        if self.getParam('eck_remote_es_hosts') != "":
            command += f"--eck-remote-es-hosts \"{self.getParam('eck_remote_es_hosts')}\"{newline}"
        if self.getParam('eck_remote_es_username') != "":
            command += f"--eck-remote-es-username \"{self.getParam('eck_remote_es_username')}\""
        if self.getParam('eck_remote_es_password') != "":
            command += f"--eck-remote-es-password $ES_PASSWORD{newline}"

        # MAS Advanced Configuration
        # -----------------------------------------------------------------------------
        if self.getParam('mas_superuser_username') != "":
            command += f"  --mas-superuser-username \"{self.getParam('mas_superuser_username')}\""
        if self.getParam('mas_superuser_password') != "":
            command += f" --mas-superuser-password $SUPERUSER_PASSWORD{newline}"

        if self.localConfigDir is not None:
            command += f"  --additional-configs \"{self.localConfigDir}\"{newline}"
        if self.getParam('pod_templates') != "":
            command += f"  --pod-templates \"{self.getParam('pod_templates')}\"{newline}"

        if self.operationalMode == 2:
            command += f"  --non-prod{newline}"

        if self.getParam('mas_trust_default_cas') == "false":
            command += f"  --disable-ca-trust{newline}"

        if self.getParam('mas_manual_cert_mgmt') is True:
            command += f"  --manual-certificates \"{self.manualCertsDir}\"{newline}"

        if self.getParam('mas_domain') is True:
            command += f"  --domain \"{self.getParam('mas_domain')}\"{newline}"

        if self.getParam('--dns-provider') == "cis":
            command += f"  --dns-provider cis --cis-apikey \"{self.getParam('cis_apikey')}\""
            command += f" --cis-subdomain \"{self.getParam('cis_subdomain')}\""
            command += f" --cis-crn \"{self.getParam('cis_crn')}\""
            command += f" --cis-email \"{self.getParam('cis_email')}\"{newline}"

        if self.getParam('--mas-cluster-issuer') != "":
            command += f"  --mas-cluster-issuer \"{self.getParam('mas_cluster_issuer')}\"{newline}"

        if self.getParam('mas_enable_walkme') == "false":
            command += f"  --disable-walkme{newline}"

        if self.getParam('enable_ipv6') is True:
            command += f"  --enable-ipv6{newline}"

        # Storage
        # -----------------------------------------------------------------------------
        command += f"  --storage-class-rwo \"{self.getParam('storage_class_rwo')}\""
        command += f" --storage-class-rwx \"{self.getParam('storage_class_rwx')}\"{newline}"
        command += f"  --storage-pipeline \"{self.pipelineStorageClass}\""
        command += f" --storage-accessmode \"{self.pipelineStorageAccessMode}\"{newline}"

        # IBM Suite License Service
        # -----------------------------------------------------------------------------
        if self.getParam("sls_namespace") and self.getParam("sls_namespace") != "ibm-sls":
            if self.getParam("mas_instance_id") and self.getParam("sls_namespace") == f"mas-{self.getParam('mas_instance_id')}-sls":
                command += "  --dedicated-sls"
            else:
                command += f"  --sls-namespace \"{self.getParam('sls_namespace')}\""
        if self.slsLicenseFileLocal:
            command += f"  --license-file \"{self.slsLicenseFileLocal}\""
        if self.getParam("sls_namespace") and self.getParam("sls_namespace") != "ibm-sls" or self.slsLicenseFileLocal:
            command += newline

        # IBM Data Reporting Operator (DRO)
        # -----------------------------------------------------------------------------
        command += f"  --uds-email \"{self.getParam('uds_contact_email')}\""
        command += f" --uds-firstname \"{self.getParam('uds_contact_firstname')}\""
        command += f" --uds-lastname \"{self.getParam('uds_contact_lastname')}\"{newline}"
        if self.getParam('dro_namespace') != "":
            command += f"  --dro-namespace \"{self.getParam('dro_namespace')}\"{newline}"

        # MongoDb Community Operator
        # -----------------------------------------------------------------------------
        if self.getParam('mongodb_namespace') != "":
            command += f"  --mongodb-namespace \"{self.getParam('mongodb_namespace')}\"{newline}"

        # OCP Configuration
        # -----------------------------------------------------------------------------
        if self.getParam('ocp_ingress_tls_secret_name') != "":
            command += f"  --ocp-ingress-tls-secret-name \"{self.getParam('ocp_ingress_tls_secret_name')}\"{newline}"

        # MAS Applications
        # -----------------------------------------------------------------------------
        if self.installAssist:
            command += f"  --assist-channel \"{self.getParam('mas_app_channel_assist')}\"{newline}"
        if self.installIoT:
            command += f"  --iot-channel \"{self.getParam('mas_app_channel_iot')}\"{newline}"
        if self.installMonitor:
            command += f"  --monitor-channel \"{self.getParam('mas_app_channel_monitor')}\"{newline}"
        if self.installManage:
            command += f"  --manage-channel \"{self.getParam('mas_app_channel_manage')}\"{newline}"
            command += f"  --is-full-manage \"{self.getParam('is_full_manage')}\"{newline}"
        if self.installOptimizer:
            command += f"  --optimizer-channel \"{self.getParam('mas_app_channel_optimizer')}\""
            command += f" --optimizer-plan \"{self.getParam('mas_app_plan_optimizer')}\"{newline}"
        if self.installPredict:
            command += f"  --predict-channel \"{self.getParam('mas_app_channel_predict')}\"{newline}"
        if self.installInspection:
            command += f"  --visualinspection-channel \"{self.getParam('mas_app_channel_visualinspection')}\"{newline}"

        # Arcgis
        # -----------------------------------------------------------------------------
        # TODO: Add ArcGis after we have properly fixed how it's installed

        # Manage Advanced Settings
        # -----------------------------------------------------------------------------
        if self.installManage:
            command += f"  --manage-jdbc \"{self.getParam('mas_appws_bindings_jdbc_manage')}\"{newline}"
            command += f"  --manage-components \"{self.getParam('mas_appws_components')}\"{newline}"

            if self.getParam('mas_app_settings_server_bundles_size') != "":
                command += f"  --manage-server-bundle-size \"{self.getParam('mas_app_settings_server_bundles_size')}\"{newline}"
            if self.getParam('mas_app_settings_default_jms') != "":
                command += f"  --manage-jms \"{self.getParam('mas_app_settings_default_jms')}\"{newline}"
            if self.getParam('mas_app_settings_persistent_volumes_flag') == "true":
                command += f"  --manage-persistent-volumes{newline}"
            if self.getParam('mas_app_settings_demodata') == "true":
                command += f"  --manage-demodata{newline}"

            if self.getParam('mas_app_settings_customization_archive_name') != "":
                command += f"  --manage-customization-archive-name \"{self.getParam('mas_app_settings_customization_archive_name')}\"{newline}"
            if self.getParam('mas_app_settings_customization_archive_url') != "":
                command += f"  --manage-customization-archive-url \"{self.getParam('mas_app_settings_customization_archive_url')}\"{newline}"
            if self.getParam('mas_app_settings_customization_archive_username') != "":
                command += f"  --manage-customization-archive-username \"{self.getParam('mas_app_settings_customization_archive_username')}\"{newline}"
            if self.getParam('mas_app_settings_customization_archive_password') != "":
                command += f"  --manage-customization-archive-password $CUSTOMIZATION_PASSWORD{newline}"

            if self.getParam('mas_app_settings_tablespace') != "":
                command += f"  --manage-db-tablespace \"{self.getParam('mas_app_settings_tablespace')}\"{newline}"
            if self.getParam('mas_app_settings_indexspace') != "":
                command += f"  --manage-db-indexspace \"{self.getParam('mas_app_settings_indexspace')}\"{newline}"
            if self.getParam('mas_app_settings_db2_schema') != "":
                command += f"  --manage-db-schema \"{self.getParam('mas_app_settings_db2_schema')}\"{newline}"

            if self.getParam('mas_app_settings_crypto_key') != "":
                command += f"  --manage-crypto-key $CRYPTO_KEY{newline}"
            if self.getParam('mas_app_settings_cryptox_key') != "":
                command += f"  --manage-cryptox-key $CRYPTOX_KEY{newline}"
            if self.getParam('mas_app_settings_old_crypto_key') != "":
                command += f"  --manage-old-crypto-key $OLD_CRYPTO_KEY{newline}"
            if self.getParam('mas_app_settings_old_cryptox_key') != "":
                command += f"  --manage-old-cryptox-key $OLD_CRYPTOX_KEY{newline}"
            if self.getParam('mas_app_settings_override_encryption_secrets_flag') == "true":
                command += f"  --manage-override-encryption-secrets \"{newline}"

            if self.getParam('mas_app_settings_base_lang') != "":
                command += f"  --manage-base-language \"{self.getParam('mas_app_settings_base_lang')}\"{newline}"
            if self.getParam('mas_app_settings_secondary_langs') != "":
                command += f"  --manage-secondary-languages \"{self.getParam('mas_app_settings_secondary_langs')}\"{newline}"

            if self.getParam('mas_app_settings_server_timezone') != "":
                command += f"  --manage-server-timezone \"{self.getParam('mas_app_settings_server_timezone')}\"{newline}"

            if self.getParam('mas_manage_attachments_provider') != "":
                command += f"  --manage-attachments-provider \"{self.getParam('mas_manage_attachments_provider')}\"{newline}"

            if self.getParam('mas_manage_attachment_configuration_mode') != "":
                command += f"  --manage-attachments-mode \"{self.getParam('mas_manage_attachment_configuration_mode')}\"{newline}"

            if self.getParam('mas_appws_bindings_health_wsl_flag') == "true":
                command += f"  --manage-health-wsl{newline}"

        # IBM Cloud Pak for Data
        # -----------------------------------------------------------------------------
        if self.getParam('cpd_product_version') != "":
            command += f"  --cp4d-version \"{self.getParam('cpd_product_version')}\""
            if self.getParam('cpd_install_spss') == "install":
                command += " --cp4d-install-spss"
            if self.getParam('cpd_install_cognos') == "install":
                command += " --cp4d-install-cognos"
            if self.getParam('cpd_install_ws') == "install":
                command += " --cp4d-install-ws"
            if self.getParam('cpd_install_wml') == "install":
                command += " --cp4d-install-wml"
            if self.getParam('cpd_install_ae') == "install":
                command += " --cp4d-install-ae"
            command += newline

        # IBM Db2 Universal Operator
        # -----------------------------------------------------------------------------
        if self.getParam('db2_action_system') == "install" or self.getParam('db2_action_manage') == "install":
            if self.getParam('db2_action_system') == "install":
                command += f"  --db2-system{newline}"
            if self.getParam('db2_action_manage') == "install":
                command += f"  --db2-manage{newline}"

            if self.getParam('db2_channel') != "":
                command += f"  --db2-channel \"{self.getParam('db2_channel')}\"{newline}"
            if self.getParam('db2_namespace') != "":
                command += f"  --db2-namespace \"{self.getParam('db2_namespace')}\"{newline}"

            if self.getParam('db2_type') != "":
                command += f"  --db2-type \"{self.getParam('db2_type')}\"{newline}"
            if self.getParam('db2_timezone') != "":
                command += f"  --db2-timezone \"{self.getParam('db2_timezone')}\"{newline}"

            if self.getParam('db2_affinity_key') != "":
                command += f"  --db2-affinity-key \"{self.getParam('db2_affinity_key')}\"{newline}"
            if self.getParam('db2_affinity_value') != "":
                command += f"  --db2-affinity_value \"{self.getParam('db2_affinity_value')}\"{newline}"

            if self.getParam('db2_tolerate_key') != "":
                command += f"  --db2-tolerate-key \"{self.getParam('db2_tolerate_key')}\"{newline}"
            if self.getParam('db2_tolerate_value') != "":
                command += f"  --db2-tolerate-value \"{self.getParam('db2_tolerate_value')}\"{newline}"
            if self.getParam('db2_tolerate_effect') != "":
                command += f"  --db2-tolerate-effect \"{self.getParam('db2_tolerate_effect')}\"{newline}"

            if self.getParam('db2_cpu_requests') != "":
                command += f"  --db2-cpu-requests \"{self.getParam('db2_cpu_requests')}\"{newline}"
            if self.getParam('db2_cpu_limits') != "":
                command += f"  --db2-cpu-limits \"{self.getParam('db2_cpu_limits')}\"{newline}"

            if self.getParam('db2_memory_requests') != "":
                command += f"  --db2-memory-requests \"{self.getParam('db2_memory_requests')}\"{newline}"
            if self.getParam('db2_memory_limits') != "":
                command += f"  --db2-memory-limits \"{self.getParam('db2_memory_limits')}\"{newline}"

            if self.getParam('db2_backup_storage_size') != "":
                command += f"  --db2-backup-storage \"{self.getParam('db2_backup_storage_size')}\"{newline}"
            if self.getParam('db2_data_storage_size') != "":
                command += f"  --db2-data-storage \"{self.getParam('db2_data_storage_size')}\"{newline}"
            if self.getParam('db2_logs_storage_size') != "":
                command += f"  --db2-logs-storage \"{self.getParam('db2_logs_storage_size')}\"{newline}"
            if self.getParam('db2_meta_storage_size') != "":
                command += f"  --db2-meta-storage \"{self.getParam('db2_meta_storage_size')}\"{newline}"
            if self.getParam('db2_temp_storage_size') != "":
                command += f"  --db2-temp-storage \"{self.getParam('db2_temp_storage_size')}\"{newline}"

        # Kafka - Common
        # -----------------------------------------------------------------------------
        if self.getParam('kafka_provider') != "":
            command += f"  --kafka-provider \"{self.getParam('kafka_provider')}\"{newline}"

            if self.getParam('kafka_username') != "":
                command += f"  --kafka-username \"{self.getParam('kafka_username')}\"{newline}"
            if self.getParam('kafka_password') != "":
                command += f"  --kafka-password $KAFKA_PASSWORD{newline}"

            # Kafka - Strimzi & AMQ Streams
            # -----------------------------------------------------------------------------
            if self.getParam('kafka_namespace') != "":
                command += f"  --kafka-namespace \"{self.getParam('kafka_namespace')}\"{newline}"
            if self.getParam('kafka_version') != "":
                command += f"  --kafka-version \"{self.getParam('kafka_version')}\"{newline}"

            # Kafka - MSK
            # -----------------------------------------------------------------------------
            if self.getParam('aws_msk_instance_type') != "":
                command += f"  --msk-instance-type \"{self.getParam('aws_msk_instance_type')}\""
                command += f" --msk-instance-nodes \"{self.getParam('aws_msk_instance_nodes')}\""
                command += f" --msk-instance-volume-size \"{self.getParam('aws_msk_instance_volume_size')}\"{newline}"

                command += f"  --msk-cidr-az1 \"{self.getParam('aws_msk_cidr_az1')}\""
                command += f" --msk-cidr-az2 \"{self.getParam('aws_msk_cidr_az1')}\""
                command += f" --msk-cidr-az3 \"{self.getParam('aws_msk_cidr_az1')}\"{newline}"

                command += f"  --msk-cidr-egress \"{self.getParam('aws_msk_egress_cidr')}\""
                command += f" --msk-cidr-ingress \"{self.getParam('aws_msk_ingress_cidr')}\"{newline}"

            # Kafka - Event Streams
            # -----------------------------------------------------------------------------
            if self.getParam('eventstreams_instance_name') != "":
                command += f"  --eventstreams-resource-group \"{self.getParam('eventstreams_resourcegroup')}\""
                command += f" --eventstreams-instance-name \"{self.getParam('eventstreams_name')}\""
                command += f" --eventstreams-instance-location \"{self.getParam('eventstreams_location')}\"{newline}"

        # COS
        # -----------------------------------------------------------------------------
        if self.getParam('cos_type') != "":
            command += f"  --cos \"{self.getParam('cos_type')}\""
            if self.getParam('cos_resourcegroup') != "":
                command += f" --cos-resourcegroup \"{self.getParam('cos_resourcegroup')}\""
            if self.getParam('cos_apikey') != "":
                command += f" --cos-apikey \"{self.getParam('cos_apikey')}\""
            if self.getParam('cos_instance_name') != "":
                command += f" --cos-instance-name \"{self.getParam('cos_instance_name')}\""
            if self.getParam('cos_bucket_name') != "":
                command += f" --cos-bucket-name \"{self.getParam('cos_bucket_name')}\"{newline}"
            command += newline

        # Turbonomic Integration
        # -----------------------------------------------------------------------------
        if self.getParam('turbonomic_target_name') != "":
            command += f"  --turbonomic-name \"{self.getParam('turbonomic_target_name')}\""
            command += f"  --turbonomic-url \"{self.getParam('turbonomic_server_url')}\""
            command += f"  --turbonomic-version \"{self.getParam('turbonomic_server_version')}\""
            command += f"  --turbonomic-username \"{self.getParam('turbonomic_username')}\""
            command += f"  --turbonomic-password \"{self.getParam('turbonomic_password')}\"{newline}"

        # Cloud Providers
        # -----------------------------------------------------------------------------
        if self.getParam('ibmcloud_apikey') != "":
            command += f"  --ibmcloud-apikey $IBMCLOUD_APIKEY{newline}"

        if self.getParam('aws_access_key_id') != "":
            command += f"  --aws-access-key-id $AWS_ACCESS_KEY_ID{newline}"
        if self.getParam('secret_access_key') != "":
            command += f"  --secret-access-key $SECRET_ACCESS_KEY{newline}"
            command += f"  --aws-region \"{self.getParam('aws_region')}\""
            command += f"  --aws-vpc-id \"{self.getParam('aws_vpc_id')}\""

        # Development Mode
        # -----------------------------------------------------------------------------
        if self.getParam('artifactory_username') != "":
            command += f"  --artifactory-username $ARTIFACTORY_USERNAME --artifactory-token $ARTIFACTORY_TOKEN{newline}"

        # Approvals
        # -----------------------------------------------------------------------------
        if self.getParam('approval_core') != "":
            command += f"  --approval-core \"{self.getParam('approval_core')}\"{newline}"
        if self.getParam('approval_assist') != "":
            command += f"  --approval-assist \"{self.getParam('approval_assist')}\"{newline}"
        if self.getParam('approval_iot') != "":
            command += f"  --approval-iot \"{self.getParam('approval_iot')}\"{newline}"
        if self.getParam('approval_manage') != "":
            command += f"  --approval-manage \"{self.getParam('approval_manage')}\"{newline}"
        if self.getParam('approval_monitor') != "":
            command += f"  --approval-monitor \"{self.getParam('approval_monitor')}\"{newline}"
        if self.getParam('approval_optimizer') != "":
            command += f"  --approval-optimizer \"{self.getParam('approval_optimizer')}\"{newline}"
        if self.getParam('approval_predict') != "":
            command += f"  --approval-predict \"{self.getParam('approval_predict')}\"{newline}"
        if self.getParam('approval_visualinspection') != "":
            command += f"  --approval-visualinspection \"{self.getParam('approval_visualinspection')}\"{newline}"

        # More Options
        # -----------------------------------------------------------------------------
        if self.devMode:
            command += f"  --dev-mode{newline}"
        if not self.waitForPVC:
            command += f"  --no-wait-for-pvc{newline}"
        if self.getParam('skip_pre_check') is True:
            command += f"  --skip-pre-check{newline}"
        if self.getParam('skip_grafana_install') is True:
            command += f"  --skip-grafana-install{newline}"
        if self.getParam('image_pull_policy') != "":
            command += f"  --image-pull-policy {self.getParam('image_pull_policy')}{newline}"
        if self.getParam('service_account_name') != "":
            command += f"  --service-account {self.getParam('service_account_name')}{newline}"

        command += "  --accept-license --no-confirm"
        return command
