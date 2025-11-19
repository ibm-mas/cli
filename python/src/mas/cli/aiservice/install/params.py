# *****************************************************************************
# Copyright (c) 2024, 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

requiredParams = [
    # MAS
    "mas_catalog_version",
    # Storage classes
    "storage_class_rwo",
    "storage_class_rwx",
    # Entitlement
    "ibm_entitlement_key",
    # DRO
    "dro_contact_email",
    "dro_contact_firstname",
    "dro_contact_lastname"
]

optionalParams = [
    # Pipeline
    "image_pull_policy",
    "service_account_name",
    # Catalogue
    "mas_catalog_digest",
    # SLS
    "sls_namespace",
    # DRO
    "dro_namespace",
    # Db2
    "db2_action_system",
    "db2_action_manage",
    "db2_action_facilities",
    "db2_type",
    "db2_timezone",
    "db2_namespace",
    "db2_channel",
    "db2_affinity_key",
    "db2_affinity_value",
    "db2_tolerate_key",
    "db2_tolerate_value",
    "db2_tolerate_effect",
    "db2_cpu_requests",
    "db2_cpu_limits",
    "db2_memory_requests",
    "db2_memory_limits",
    "db2_backup_storage_size",
    "db2_data_storage_size",
    "db2_logs_storage_size",
    "db2_meta_storage_size",
    "db2_temp_storage_size",
    # Dev Mode
    "artifactory_username",
    "artifactory_token",
    # ODH
    "aiservice_odh_model_deployment_type",
    # AI Service
    "aiservice_s3_accesskey",
    "aiservice_s3_secretkey",
    "aiservice_s3_host",
    "aiservice_s3_port",
    "aiservice_s3_ssl",
    "aiservice_s3_region",
    "aiservice_s3_bucket_prefix",
    "aiservice_s3_tenants_bucket",
    "aiservice_s3_templates_bucket",

    "aiservice_watsonxai_apikey",
    "aiservice_watsonxai_url",
    "aiservice_watsonxai_project_id",
    "aiservice_watsonx_action",
    "aiservice_watsonxai_ca_crt",
    "aiservice_watsonxai_deployment_id",
    "aiservice_watsonxai_space_id",
    "aiservice_watsonxai_instance_id",
    "aiservice_watsonxai_username",
    "aiservice_watsonxai_version",
    "aiservice_watsonxai_full",
    "aiservice_instance_id",
    "aiservice_watsonxai_instance_id",
    "aiservice_watsonxai_verify",

    "minio_root_user",
    "minio_root_password",

    "tenant_entitlement_type",
    "tenant_entitlement_start_date",
    "tenant_entitlement_end_date",

    "rsl_url",
    "rsl_org_id",
    "rsl_token",
    "rsl_ca_crt",
    "environment_type",
]
