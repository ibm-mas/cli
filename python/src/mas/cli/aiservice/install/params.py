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
    "mas_aibroker_storage_provider",
    "mas_aibroker_storage_accesskey",
    "mas_aibroker_storage_secretkey",
    "mas_aibroker_storage_host",
    "mas_aibroker_storage_port",
    "mas_aibroker_storage_ssl",
    "mas_aibroker_storage_region",
    "mas_aibroker_storage_pipelines_bucket",
    "mas_aibroker_storage_tenants_bucket",
    "mas_aibroker_storage_templates_bucket",
    "mas_aibroker_tenant_name",
    "mas_aibroker_watsonxai_apikey",
    "mas_aibroker_watsonxai_url",
    "mas_aibroker_watsonxai_project_id",
    "mas_aibroker_watsonx_action",
    "mas_aibroker_db_host",
    "mas_aibroker_db_port",
    "mas_aibroker_db_user",
    "mas_aibroker_db_database",
    "mas_aibroker_db_secret_name",
    "mas_aibroker_db_secret_key",
    "mas_aibroker_db_secret_value",
    "aibroker_instance_id",
    "mariadb_user",
    "mariadb_password",
    "minio_root_user",
    "minio_root_password",
    "tenant_entitlement_type",
    "tenant_entitlement_start_date",
    "tenant_entitlement_end_date",
    "mas_aibroker_s3_bucket_prefix",
    "mas_aibroker_s3_region",
    "mas_aibroker_s3_endpoint_url",
    "mas_aibroker_tenant_s3_bucket_prefix",
    "mas_aibroker_tenant_s3_region",
    "mas_aibroker_tenant_s3_endpoint_url",
    "mas_aibroker_tenant_s3_access_key",
    "mas_aibroker_tenant_s3_secret_key",
    "rsl_url",
    "rsl_org_id",
    "rsl_token",
    "install_minio_aiservice",
    "install_sls_aiservice",
    "install_dro_aiservice",
    "install_db2_aiservice",
    "mas_aibroker_dro_secret_name",
    "mas_aibroker_dro_api_key",
    "mas_aibroker_dro_url",
    "mas_aibroker_dro_ca_cert",
    "mas_aibroker_db2_username",
    "mas_aibroker_db2_password",
    "mas_aibroker_db2_jdbc_url",
    "mas_aibroker_db2_ssl_enabled",
    "mas_aibroker_db2_ca_cert",
    "mas_aibroker_sls_secret_name",
    "mas_aibroker_sls_registration_key",
    "mas_aibroker_sls_url",
    "mas_aibroker_sls_ca_cert",
    "environment_type",
]
