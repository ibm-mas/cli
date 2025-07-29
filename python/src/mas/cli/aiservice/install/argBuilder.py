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
        command += f"  --aiservice-instance-id  \"{self.getParam('aiservice_instance_id')}\"{newline}"

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
            if self.getParam("aiservice_instance_id") and self.getParam("sls_namespace") == f"mas-{self.getParam('mas_instance_id')}-sls":
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
        command += f"  --aiservice-channel \"{self.getParam('aiservice_channel')}\"{newline}"

        # IBM Db2 Universal Operator
        # -----------------------------------------------------------------------------
        command += f"  --db2-aiservice{newline}"

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
        if self.getParam('image_pull_policy') != "":
            command += f"  --image-pull-policy {self.getParam('image_pull_policy')}{newline}"
        if self.getParam('service_account_name') != "":
            command += f"  --service-account {self.getParam('service_account_name')}{newline}"

        # Aibroker Advanced Settings
        # -----------------------------------------------------------------------------
        if self.getParam('aiservice_storage_provider') != "":
            command += f"  --aiservice-storage-provider \"{self.getParam('aiservice_storage_provider')}\"{newline}"
        if self.getParam('aiservice_storage_accesskey') != "":
            command += f"  --aiservice-storage-accesskey \"{self.getParam('aiservice_storage_accesskey')}\"{newline}"
        if self.getParam('aiservice_storage_secretkey') != "":
            command += f"  --aiservice-storage-secretkey \"{self.getParam('aiservice_storage_secretkey')}\"{newline}"
        if self.getParam('aiservice_storage_host') != "":
            command += f"  --aiservice-storage-host \"{self.getParam('aiservice_storage_host')}\"{newline}"
        if self.getParam('aiservice_storage_port') != "":
            command += f"  --aiservice-storage-port \"{self.getParam('aiservice_storage_port')}\"{newline}"
        if self.getParam('aiservice_storage_ssl') != "":
            command += f"  --aiservice-storage-ssl \"{self.getParam('aiservice_storage_ssl')}\"{newline}"
        if self.getParam('aiservice_storage_region') != "":
            command += f"  --aiservice-storage-region \"{self.getParam('aiservice_storage_region')}\"{newline}"
        if self.getParam('aiservice_storage_pipelines_bucket') != "":
            command += f"  --aiservice-storage-pipelines-bucket \"{self.getParam('aiservice_storage_pipelines_bucket')}\"{newline}"
        if self.getParam('aiservice_storage_tenants_bucket') != "":
            command += f"  --aiservice-storage-tenants-bucket \"{self.getParam('aiservice_storage_tenants_bucket')}\"{newline}"
        if self.getParam('aiservice_storage_templates_bucket') != "":
            command += f"  --aiservice-storage-templates-bucket \"{self.getParam('aiservice_storage_templates_bucket')}\"{newline}"

        if self.getParam('aiservice_watsonxai_apikey') != "":
            command += f"  --aiservice-watsonxai-apikey \"{self.getParam('aiservice_watsonxai_apikey')}\"{newline}"
        if self.getParam('aiservice_watsonxai_url') != "":
            command += f"  --aiservice-watsonxai-url \"{self.getParam('aiservice_watsonxai_url')}\"{newline}"
        if self.getParam('aiservice_watsonxai_project_id') != "":
            command += f"  --aiservice-watsonxai-project-id \"{self.getParam('aiservice_watsonxai_project_id')}\"{newline}"
        if self.getParam('aiservice_watsonx_action') != "":
            command += f"  --aiservice-watsonx-action \"{self.getParam('aiservice_watsonx_action')}\"{newline}"

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

        if self.getParam('aiservice_s3_bucket_prefix') != "":
            command += f"  --aiservice-s3-bucket-prefix \"{self.getParam('aiservice_s3_bucket_prefix')}\"{newline}"
        if self.getParam('aiservice_s3_endpoint_url') != "":
            command += f"  --aiservice-s3-endpoint-url \"{self.getParam('aiservice_s3_endpoint_url')}\"{newline}"
        if self.getParam('aiservice_s3_region') != "":
            command += f"  --aiservice-s3-region \"{self.getParam('aiservice_s3_region')}\"{newline}"

        if self.getParam('aiservice_tenant_s3_bucket_prefix') != "":
            command += f"  --aiservice-tenant-s3-bucket-prefix \"{self.getParam('aiservice_tenant_s3_bucket_prefix')}\"{newline}"
        if self.getParam('aiservice_tenant_s3_region') != "":
            command += f"  --aiservice-tenant-s3-region \"{self.getParam('aiservice_tenant_s3_region')}\"{newline}"
        if self.getParam('aiservice_tenant_s3_endpoint_url') != "":
            command += f"  --aiservice-tenant-s3-endpoint-url \"{self.getParam('aiservice_tenant_s3_endpoint_url')}\"{newline}"
        if self.getParam('aiservice_tenant_s3_access_key') != "":
            command += f"  --aiservice-tenant-s3-access-key \"{self.getParam('aiservice_tenant_s3_access_key')}\"{newline}"
        if self.getParam('aiservice_tenant_s3_secret_key') != "":
            command += f"  --aiservice-tenant-s3-secret-key \"{self.getParam('aiservice_tenant_s3_secret_key')}\"{newline}"

        if self.getParam('rsl_url') != "":
            command += f"  --rsl-url \"{self.getParam('rsl_url')}\"{newline}"
        if self.getParam('rsl_org_id') != "":
            command += f"  --rsl-org-id \"{self.getParam('rsl_org_id')}\"{newline}"
        if self.getParam('rsl_token') != "":
            command += f"  --rsl-token \"{self.getParam('rsl_token')}\"{newline}"

        command += "  --accept-license --no-confirm"
        return command
