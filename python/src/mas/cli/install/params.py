# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
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
    "mas_channel",
    "mas_instance_id",
    "mas_workspace_id",
    "mas_workspace_name",
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
    # OpenShift
    "ocp_ingress_tls_secret_name",
    # MAS
    "mas_catalog_digest",
    "mas_superuser_username",
    "mas_superuser_password",
    "mas_trust_default_cas",
    "mas_app_settings_server_bundles_size",
    "is_full_manage",
    "mas_app_settings_default_jms",
    "mas_app_settings_persistent_volumes_flag",
    "mas_app_settings_demodata",
    "mas_app_settings_customization_archive_name",
    "mas_app_settings_customization_archive_url",
    "mas_app_settings_customization_archive_username",
    "mas_app_settings_customization_archive_password",
    "mas_app_settings_tablespace",
    "mas_app_settings_indexspace",
    "mas_app_settings_db2_schema",
    "mas_app_settings_crypto_key",
    "mas_app_settings_cryptox_key",
    "mas_app_settings_old_crypto_key",
    "mas_app_settings_old_cryptox_key",
    "mas_app_settings_override_encryption_secrets_flag",
    "mas_app_settings_base_lang",
    "mas_app_settings_secondary_langs",
    "mas_app_settings_server_timezone",
    "mas_appws_bindings_jdbc_manage",
    "mas_appws_components",
    "mas_appws_bindings_health_wsl_flag",
    "mas_domain",
    # SLS
    "sls_namespace",
    # DNS Providers
    # TODO: Add CloudFlare and Route53 support
    "dns_provider",
    "cis_email",
    "cis_apikey",
    "cis_crn",
    "cis_subdomain",
    "mas_cluster_issuer",
    # DRO
    "dro_namespace",
    # Db2
    "db2_action_system",
    "db2_action_manage",
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
    # CP4D
    "cpd_product_version",
    "cpd_install_cognos",
    "cpd_install_spss",
    "cpd_install_ws",
    "cpd_install_wml",
    "cpd_install_ae",
    # Kafka
    "kafka_namespace",
    "kafka_version",
    "aws_msk_instance_type",
    "aws_msk_instance_number",
    "aws_msk_volume_size",
    "aws_msk_cidr_az1",
    "aws_msk_cidr_az2",
    "aws_msk_cidr_az3",
    "aws_msk_egress_cidr",
    "aws_msk_ingress_cidr",
    "eventstreams_resource_group",
    "eventstreams_instance_name",
    "eventstreams_instance_location",
    # COS
    "cos_type",
    "cos_resourcegroup",
    "cos_apikey",
    "cos_instance_name",
    "cos_bucket_name",
    # Attachments
    "mas_manage_attachments_provider",
    "mas_manage_attachment_configuration_mode",
    # ECK
    "eck_action",
    "eck_enable_logstash",
    "eck_remote_es_hosts",
    "eck_remote_es_username",
    "eck_remote_es_password",
    # Turbonomic
    "turbonomic_target_name",
    "turbonomic_server_url",
    "turbonomic_server_version",
    "turbonomic_username",
    "turbonomic_password",
    # Cloud Providers
    "ibmcloud_apikey",
    "aws_region",
    "aws_access_key_id",
    "secret_access_key",
    "aws_vpc_id",
    # Dev Mode
    "artifactory_username",
    "artifactory_token",
    # TODO: The way arcgis has been implemented needs to be fixed
    "install_arcgis",
    "mas_arcgis_channel",
    # Guided Tour
    "mas_enable_walkme",
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
    # Special chars
    "mas_special_characters"
]
