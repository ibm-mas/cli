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
    "uds_contact_email",
    "uds_contact_firstname",
    "uds_contact_lastname"
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
    # Aibroker
    "aiservice_storage_provider",
    "aiservice_storage_accesskey",
    "aiservice_storage_secretkey",
    "aiservice_storage_host",
    "aiservice_storage_port",
    "aiservice_storage_ssl",
    "aiservice_storage_region",
    "aiservice_storage_pipelines_bucket",
    "aiservice_storage_tenants_bucket",
    "aiservice_storage_templates_bucket",

    "aiservice_watsonxai_apikey",
    "aiservice_watsonxai_url",
    "aiservice_watsonxai_project_id",
    "aiservice_watsonx_action",

    "aiservice_instance_id",

    "minio_root_user",
    "minio_root_password",

    "tenant_entitlement_type",
    "tenant_entitlement_start_date",
    "tenant_entitlement_end_date",

    "aiservice_s3_bucket_prefix",
    "aiservice_s3_region",
    "aiservice_s3_endpoint_url",
    "aiservice_tenant_s3_bucket_prefix",
    "aiservice_tenant_s3_region",
    "aiservice_tenant_s3_endpoint_url",
    "aiservice_tenant_s3_access_key",
    "aiservice_tenant_s3_secret_key",

    "rsl_url",
    "rsl_org_id",
    "rsl_token",

    "environment_type",
]
