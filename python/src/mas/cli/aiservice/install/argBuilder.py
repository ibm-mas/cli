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
        command += f"  --contact-email \"{self.getParam('dro_contact_email')}\""
        command += f" --contact-firstname \"{self.getParam('dro_contact_firstname')}\""
        command += f" --contact-lastname \"{self.getParam('dro_contact_lastname')}\"{newline}"
        if self.getParam('dro_namespace') != "":
            command += f"  --dro-namespace \"{self.getParam('dro_namespace')}\"{newline}"

        # MongoDb Community Operator
        # -----------------------------------------------------------------------------
        if self.getParam('mongodb_namespace') != "":
            command += f"  --mongodb-namespace \"{self.getParam('mongodb_namespace')}\"{newline}"

        # Aibroker Channel
        # -----------------------------------------------------------------------------
        command += f"  --aiservice-channel \"{self.getParam('aiservice_channel')}\"{newline}"

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

        # AI Service Advanced Settings
        # -----------------------------------------------------------------------------
        if self.getParam('aiservice_s3_accesskey') != "":
            command += f"  --s3-accesskey \"{self.getParam('aiservice_s3_accesskey')}\"{newline}"
        if self.getParam('aiservice_s3_secretkey') != "":
            command += f"  --s3-secretkey \"{self.getParam('aiservice_s3_secretkey')}\"{newline}"
        if self.getParam('aiservice_s3_host') != "":
            command += f"  --s3-host \"{self.getParam('aiservice_s3_host')}\"{newline}"
        if self.getParam('aiservice_s3_port') != "":
            command += f"  --s3-port \"{self.getParam('aiservice_s3_port')}\"{newline}"
        if self.getParam('aiservice_s3_ssl') != "":
            command += f"  --s3-ssl \"{self.getParam('aiservice_s3_ssl')}\"{newline}"
        if self.getParam('aiservice_s3_region') != "":
            command += f"  --s3-region \"{self.getParam('aiservice_s3_region')}\"{newline}"
        if self.getParam('aiservice_s3_bucket_prefix') != "":
            command += f"  --s3-bucket-prefix \"{self.getParam('aiservice_s3_bucket_prefix')}\"{newline}"
        if self.getParam('aiservice_s3_tenants_bucket') != "":
            command += f"  --s3-tenants-bucket \"{self.getParam('aiservice_s3_tenants_bucket')}\"{newline}"
        if self.getParam('aiservice_s3_templates_bucket') != "":
            command += f"  --s3-templates-bucket \"{self.getParam('aiservice_s3_templates_bucket')}\"{newline}"

        if self.getParam('aiservice_odh_model_deployment_type') != "":
            command += f"  --odh-model-deployment-type \"{self.getParam('aiservice_odh_model_deployment_type')}\"{newline}"

        if self.getParam('aiservice_watsonxai_apikey') != "":
            command += f"  --watsonxai-apikey \"{self.getParam('aiservice_watsonxai_apikey')}\"{newline}"
        if self.getParam('aiservice_watsonxai_url') != "":
            command += f"  --watsonxai-url \"{self.getParam('aiservice_watsonxai_url')}\"{newline}"
        if self.getParam('aiservice_watsonxai_project_id') != "":
            command += f"  --watsonxai-project-id \"{self.getParam('aiservice_watsonxai_project_id')}\"{newline}"
        if self.getParam('aiservice_watsonx_action') != "":
            command += f"  --watsonx-action \"{self.getParam('aiservice_watsonx_action')}\"{newline}"
        if self.getParam('aiservice_watsonxai_ca_crt') != "":
            command += f"  --watsonxai-ca-crt \"{self.getParam('aiservice_watsonxai_ca_crt')}\"{newline}"
        if self.getParam('aiservice_watsonxai_deployment_id') != "":
            command += f"  --watsonxai-deployment-id \"{self.getParam('aiservice_watsonxai_deployment_id')}\"{newline}"
        if self.getParam('aiservice_watsonxai_space_id') != "":
            command += f"  --watsonxai-space-id \"{self.getParam('aiservice_watsonxai_space_id')}\"{newline}"
        if self.getParam('aiservice_watsonxai_instance_id') != "":
            command += f"  --watsonxai-instance-id \"{self.getParam('aiservice_watsonxai_instance_id')}\"{newline}"
        if self.getParam('aiservice_watsonxai_username') != "":
            command += f"  --watsonxai-username \"{self.getParam('aiservice_watsonxai_username')}\"{newline}"
        if self.getParam('aiservice_watsonxai_version') != "":
            command += f"  --watsonxai-version \"{self.getParam('aiservice_watsonxai_version')}\"{newline}"
        if self.getParam('aiservice_watsonxai_full') != "":
            command += f"  --watsonxai-full \"{self.getParam('aiservice_watsonxai_full')}\"{newline}"

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

        if self.getParam('rsl_url') != "":
            command += f"  --rsl-url \"{self.getParam('rsl_url')}\"{newline}"
        if self.getParam('rsl_org_id') != "":
            command += f"  --rsl-org-id \"{self.getParam('rsl_org_id')}\"{newline}"
        if self.getParam('rsl_token') != "":
            command += f"  --rsl-token \"{self.getParam('rsl_token')}\"{newline}"
        if self.getParam('rsl_ca_crt') != "":
            command += f"  --rsl-ca-crt \"{self.getParam('rsl_ca_crt')}\"{newline}"

        command += "  --accept-license --no-confirm"
        return command
