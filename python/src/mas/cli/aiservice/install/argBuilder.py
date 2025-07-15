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

logger = logging.getLogger(__name__)


class aiServiceInstallArgBuilderMixin():
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

        command += f"mas aiservice-install --mas-catalog-version {self.getParam('mas_catalog_version')}"

        if self.getParam('mas_catalog_digest') != "":
            command += f" --mas-catalog-digest {self.getParam('mas_catalog_digest')}"

        command += f" --ibm-entitlement-key $IBM_ENTITLEMENT_KEY{newline}"

        # Aibroker Instance Id
        command += f"  --aibroker-instance-id  \"{self.getParam('aibroker_instance_id')}\"{newline}"

        # MAS Advanced Configuration
        # -----------------------------------------------------------------------------

        if self.localConfigDir is not None:
            command += f"  --additional-configs \"{self.localConfigDir}\"{newline}"

        # Storage
        # -----------------------------------------------------------------------------
        command += f"  --storage-class-rwo \"{self.getParam('storage_class_rwo')}\""
        command += f" --storage-class-rwx \"{self.getParam('storage_class_rwx')}\"{newline}"
        command += f"  --storage-pipeline \"{self.pipelineStorageClass}\""
        command += f" --storage-accessmode \"{self.pipelineStorageAccessMode}\"{newline}"

        # IBM Suite License Service
        # -----------------------------------------------------------------------------
        if self.getParam("sls_namespace") and self.getParam("sls_namespace") != "ibm-sls":
            if self.getParam("aibroker_instance_id") and self.getParam("sls_namespace") == f"mas-{self.getParam('mas_instance_id')}-sls":
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

        # Aibroker Channel
        # -----------------------------------------------------------------------------
        if self.installAiBroker:
            command += f"  --aibroker-channel \"{self.getParam('mas_app_channel_aibroker')}\"{newline}"

        # IBM Db2 Universal Operator
        # -----------------------------------------------------------------------------
        if self.getParam('db2_action_system') == "install" or self.getParam('db2_action_manage') == "install" or self.getParam('db2_action_facilities') == "install":
            if self.getParam('db2_action_system') == "install":
                command += f"  --db2-system{newline}"
            if self.getParam('db2_action_manage') == "install":
                command += f"  --db2-manage{newline}"
            if self.getParam('db2_action_facilities') == "install":
                command += f"  --db2-facilities{newline}"

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

        # Development Mode
        # -----------------------------------------------------------------------------
        if self.getParam('artifactory_username') != "":
            command += f"  --artifactory-username $ARTIFACTORY_USERNAME --artifactory-token $ARTIFACTORY_TOKEN{newline}"

        # Approvals
        # -----------------------------------------------------------------------------
        if self.getParam('approval_aibroker') != "":
            command += f"  --approval-aibroker \"{self.getParam('approval_aibroker')}\"{newline}"

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

        # Aibroker Advanced Settings
        # -----------------------------------------------------------------------------
        if self.getParam('mas_aibroker_storage_provider') != "":
            command += f"  --mas-aibroker-storage-provider \"{self.getParam('mas_aibroker_storage_provider')}\"{newline}"
        if self.getParam('mas_aibroker_storage_accesskey') != "":
            command += f"  --mas-aibroker-storage-accesskey \"{self.getParam('mas_aibroker_storage_accesskey')}\"{newline}"
        if self.getParam('mas_aibroker_storage_secretkey') != "":
            command += f"  --mas-aibroker-storage-secretkey \"{self.getParam('mas_aibroker_storage_secretkey')}\"{newline}"
        if self.getParam('mas_aibroker_storage_host') != "":
            command += f"  --mas-aibroker-storage-host \"{self.getParam('mas_aibroker_storage_host')}\"{newline}"
        if self.getParam('mas_aibroker_storage_port') != "":
            command += f"  --mas-aibroker-storage-port \"{self.getParam('mas_aibroker_storage_port')}\"{newline}"
        if self.getParam('mas_aibroker_storage_ssl') != "":
            command += f"  --mas-aibroker-storage-ssl \"{self.getParam('mas_aibroker_storage_ssl')}\"{newline}"
        if self.getParam('mas_aibroker_storage_region') != "":
            command += f"  --mas-aibroker-storage-region \"{self.getParam('mas_aibroker_storage_region')}\"{newline}"
        if self.getParam('mas_aibroker_storage_pipelines_bucket') != "":
            command += f"  --mas-aibroker-storage-pipelines-bucket \"{self.getParam('mas_aibroker_storage_pipelines_bucket')}\"{newline}"
        if self.getParam('mas_aibroker_storage_tenants_bucket') != "":
            command += f"  --mas-aibroker-storage-tenants-bucket \"{self.getParam('mas_aibroker_storage_tenants_bucket')}\"{newline}"
        if self.getParam('mas_aibroker_storage_templates_bucket') != "":
            command += f"  --mas-aibroker-storage-templates-bucket \"{self.getParam('mas_aibroker_storage_templates_bucket')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_name') != "":
            command += f"  --mas-aibroker-tenant-name \"{self.getParam('mas_aibroker_tenant_name')}\"{newline}"
        if self.getParam('mas_aibroker_watsonxai_apikey') != "":
            command += f"  --mas-aibroker-watsonxai-apikey \"{self.getParam('mas_aibroker_watsonxai_apikey')}\"{newline}"
        if self.getParam('mas_aibroker_watsonxai_url') != "":
            command += f"  --mas-aibroker-watsonxai-url \"{self.getParam('mas_aibroker_watsonxai_url')}\"{newline}"
        if self.getParam('mas_aibroker_watsonxai_project_id') != "":
            command += f"  --mas-aibroker-watsonxai-project-id \"{self.getParam('mas_aibroker_watsonxai_project_id')}\"{newline}"
        if self.getParam('mas_aibroker_watsonx_action') != "":
            command += f"  --mas-aibroker-watsonx-action \"{self.getParam('mas_aibroker_watsonx_action')}\"{newline}"
        if self.getParam('mas_aibroker_db_host') != "":
            command += f"  --mas-aibroker-db-host \"{self.getParam('mas_aibroker_db_host')}\"{newline}"
        if self.getParam('mas_aibroker_db_port') != "":
            command += f"  --mas-aibroker-db-port \"{self.getParam('mas_aibroker_db_port')}\"{newline}"
        if self.getParam('mas_aibroker_db_user') != "":
            command += f"  --mas-aibroker-db-user \"{self.getParam('mas_aibroker_db_user')}\"{newline}"
        if self.getParam('mas_aibroker_db_database') != "":
            command += f"  --mas-aibroker-db-database \"{self.getParam('mas_aibroker_db_database')}\"{newline}"
        if self.getParam('mas_aibroker_db_secret_name') != "":
            command += f"  --mas-aibroker-db-secret-name \"{self.getParam('mas_aibroker_db_secret_name')}\"{newline}"
        if self.getParam('mas_aibroker_db_secret_key') != "":
            command += f"  --mas-aibroker-db-secret-key \"{self.getParam('mas_aibroker_db_secret_key')}\"{newline}"
        if self.getParam('mas_aibroker_db_secret_value') != "":
            command += f"  --mas-aibroker-db-secret-value \"{self.getParam('mas_aibroker_db_secret_value')}\"{newline}"
        if self.getParam('mariadb_user') != "":
            command += f"  --mariadb-user \"{self.getParam('mariadb_user')}\"{newline}"
        if self.getParam('mariadb_password') != "":
            command += f"  --mariadb-password \"{self.getParam('mariadb_password')}\"{newline}"
        if self.getParam('minio_root_user') != "":
            command += f"  --minio-root-user \"{self.getParam('minio_root_user')}\"{newline}"
        if self.getParam('minio_root_password') != "":
            command += f"  --minio-root-password \"{self.getParam('minio_root_password')}\"{newline}"
        if self.getParam('tenant_entitlement_type') != "":
            command += f"  --tenant-entitlement-type \"{self.getParam('tenant_entitlement_type')}\"{newline}"
        if self.getParam('tenant_entitlement_start_date') != "":
            command += f"  --tenant-entitlement-start-date \"{self.getParam('tenant_entitlement_start_date')}\"{newline}"
        if self.getParam('tenant_entitlement_end_date') != "":
            command += f"  --tenant-entitlement-end-date \"{self.getParam('tenant_entitlement_end_date')}\"{newline}"
        if self.getParam('mas_aibroker_s3_bucket_prefix') != "":
            command += f"  --mas-aibroker-s3-bucket-prefix \"{self.getParam('mas_aibroker_s3_bucket_prefix')}\"{newline}"
        if self.getParam('mas_aibroker_s3_endpoint_url') != "":
            command += f"  --mas-aibroker-s3-endpoint-url \"{self.getParam('mas_aibroker_s3_endpoint_url')}\"{newline}"
        if self.getParam('mas_aibroker_s3_region') != "":
            command += f"  --mas-aibroker-s3-region \"{self.getParam('mas_aibroker_s3_region')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_s3_bucket_prefix') != "":
            command += f"  --mas-aibroker-tenant-s3-bucket-prefix \"{self.getParam('mas_aibroker_tenant_s3_bucket_prefix')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_s3_region') != "":
            command += f"  --mas-aibroker-tenant-s3-region \"{self.getParam('mas_aibroker_tenant_s3_region')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_s3_endpoint_url') != "":
            command += f"  --mas-aibroker-tenant-s3-endpoint-url \"{self.getParam('mas_aibroker_tenant_s3_endpoint_url')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_s3_access_key') != "":
            command += f"  --mas-aibroker-tenant-s3-access-key \"{self.getParam('mas_aibroker_tenant_s3_access_key')}\"{newline}"
        if self.getParam('mas_aibroker_tenant_s3_secret_key') != "":
            command += f"  --mas-aibroker-tenant-s3-secret-key \"{self.getParam('mas_aibroker_tenant_s3_secret_key')}\"{newline}"
        if self.getParam('rsl_url') != "":
            command += f"  --rsl-url \"{self.getParam('rsl_url')}\"{newline}"
        if self.getParam('rsl_org_id') != "":
            command += f"  --rsl-org-id \"{self.getParam('rsl_org_id')}\"{newline}"
        if self.getParam('rsl_token') != "":
            command += f"  --rsl-token \"{self.getParam('rsl_token')}\"{newline}"

        command += "  --accept-license --no-confirm"
        return command
