# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Declarative specification of the non-interactive `mas install` command that
the interactive wizard prints at the end of a run.

Each entry names the argparse dest it maps to; the flag spelling is resolved
from the real installArgParser at render time (see common.commandBuilder).
Only what argparse cannot express is spelled out here: where a value comes
from, which parameters are secrets (env-masked with an export placeholder),
and the conditions under which a flag is emitted.
"""

from ..common.commandBuilder import CommandArg, paramIsFalse, paramIsTrue, renderCommand
from .argParser import installArgParser
from .facilities.agents import facilitiesAgents

# ---------------------------------------------------------------------------
# Condition helpers
# ---------------------------------------------------------------------------

# Boolean conditions use paramIsTrue/paramIsFalse from common.commandBuilder:
# interactive runs store 'true'/'false' strings, non-interactive runs copy
# argparse's native booleans into params, and both must work.
_isTrue = paramIsTrue
_isFalse = paramIsFalse


def _eq(param: str, expected: str):
    return lambda app: app.getParam(param) == expected


def _ne(param: str, unexpected: str):
    return lambda app: app.getParam(param) != unexpected


def _attr(name: str, default=None):
    return lambda app: getattr(app, name, default)


def _attrTruthy(name: str):
    return lambda app: bool(getattr(app, name, False))


def _dedicatedSls(app) -> bool:
    instanceId = app.getParam("mas_instance_id")
    return instanceId != "" and app.getParam("sls_namespace") == f"mas-{instanceId}-sls"


def _db2Action(*params: str):
    return lambda app: any(app.getParam(param) == "install" for param in params)


# Any of the universal Db2 operators is being installed (excludes AI Service's own Db2)
_db2Universal = _db2Action("db2_action_system", "db2_action_manage", "db2_action_facilities")

# Any Db2 at all is being installed, including AI Service's own Db2
_db2Any = _db2Action("db2_action_system", "db2_action_manage", "db2_action_facilities", "db2_action_aiservice")

# Kafka is configured (the Kafka-related flags are only meaningful then)
_kafka = _ne("kafka_provider", "")

# An external S3-compatible object store is used (rather than the in-cluster Minio deployed by --install-minio)
_externalS3 = lambda app: app.getParam("minio_root_user") == ""  # noqa: E731

# CIS enhanced security options are only prompted for when enhanced security is enabled
_cis = _eq("dns_provider", "cis")
_cisEnhanced = lambda app: _cis(app) and _isTrue("cis_enhanced_security")(app)  # noqa: E731

# Minio credentials are only valid as a pair
_minio = lambda app: app.getParam("minio_root_user") != "" and app.getParam("minio_root_password") != ""  # noqa: E731

_installManage = _attrTruthy("installManage")


# ---------------------------------------------------------------------------
# Command specification
# ---------------------------------------------------------------------------

INSTALL_COMMAND_ARGS = [
    # MAS Catalog Selection & Entitlement
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_catalog_version"),
    CommandArg(dest="mas_catalog_digest"),
    CommandArg(dest="ibm_entitlement_key", env_var="IBM_ENTITLEMENT_KEY", required=True),
    # MAS Basic Configuration
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_channel"),
    CommandArg(dest="mas_instance_id"),
    CommandArg(dest="mas_workspace_id"),
    CommandArg(dest="mas_workspace_name"),
    CommandArg(dest="mas_special_characters", const=True, when=_isTrue("mas_special_characters")),
    # ECK Integration
    # -----------------------------------------------------------------------------
    CommandArg(dest="eck_action", const=True, when=_eq("eck_action", "install")),
    CommandArg(dest="eck_enable_logstash", const=True, when=_isTrue("eck_enable_logstash")),
    CommandArg(dest="eck_remote_es_hosts"),
    CommandArg(dest="eck_remote_es_username"),
    CommandArg(dest="eck_remote_es_password", env_var="ES_PASSWORD"),
    # MAS Advanced Configuration
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_superuser_username"),
    CommandArg(dest="mas_superuser_password", env_var="SUPERUSER_PASSWORD"),
    CommandArg(dest="additional_configs", value=_attr("localConfigDir")),
    CommandArg(dest="pod_templates", value=_attr("podTemplatesKeyword"), when=lambda app: getattr(app, "podTemplatesKeyword", None) is not None),
    CommandArg(dest="pod_templates", param="mas_pod_templates_dir", when=lambda app: getattr(app, "podTemplatesKeyword", None) is None),
    CommandArg(dest="non_prod", const=True, when=lambda app: getattr(app, "operationalMode", 1) == 2),
    CommandArg(dest="mas_admin_mode", value=lambda app: getattr(app, "mas_admin_mode", "") or app.getParam("mas_admin_mode")),
    CommandArg(dest="mas_trust_default_cas", const=True, when=_isFalse("mas_trust_default_cas")),
    CommandArg(dest="manual_certificates", value=_attr("manualCertsDir"), when=_isTrue("mas_manual_cert_mgmt")),
    CommandArg(dest="mas_routing_mode"),
    CommandArg(dest="mas_ingress_controller_name"),
    CommandArg(dest="mas_configure_ingress", const=True, when=_isTrue("mas_configure_ingress")),
    CommandArg(dest="mas_use_service_mesh"),
    CommandArg(dest="mas_manual_route_mgmt", const=True, when=_isTrue("mas_manual_route_mgmt")),
    CommandArg(dest="mas_domain"),
    # DNS Provider
    # -----------------------------------------------------------------------------
    CommandArg(dest="dns_provider"),
    CommandArg(dest="cis_apikey", env_var="CIS_APIKEY", when=_cis),
    CommandArg(dest="cis_subdomain", when=_cis),
    CommandArg(dest="cis_crn", when=_cis),
    CommandArg(dest="cis_email", when=_cis),
    CommandArg(dest="cis_enhanced_security", const=True, when=_cisEnhanced),
    CommandArg(dest="cis_service_name", when=_cisEnhanced),
    CommandArg(dest="update_dns_entries", const=True, when=lambda app: _cisEnhanced(app) and _isTrue("update_dns_entries")(app)),
    CommandArg(dest="cis_waf", const=True, when=lambda app: _cisEnhanced(app) and _isTrue("cis_waf")(app)),
    CommandArg(dest="cis_proxy", const=True, when=lambda app: _cisEnhanced(app) and _isTrue("cis_proxy")(app)),
    CommandArg(dest="delete_wildcards", const=True, when=lambda app: _cisEnhanced(app) and _isTrue("delete_wildcards")(app)),
    CommandArg(dest="override_edge_certs", const=True, when=lambda app: _cisEnhanced(app) and _isTrue("override_edge_certs")(app)),
    CommandArg(dest="cloudflare_apitoken", env_var="CLOUDFLARE_APITOKEN", when=_eq("dns_provider", "cloudflare")),
    CommandArg(dest="cloudflare_email", when=_eq("dns_provider", "cloudflare")),
    CommandArg(dest="cloudflare_zone", when=_eq("dns_provider", "cloudflare")),
    CommandArg(dest="cloudflare_subdomain", when=_eq("dns_provider", "cloudflare")),
    CommandArg(dest="route53_hosted_zone_name", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_hosted_zone_region", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_subdomain", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_email", when=_eq("dns_provider", "route53")),
    CommandArg(dest="mas_cluster_issuer"),
    CommandArg(dest="mas_issuer_kind"),
    CommandArg(dest="mas_enable_walkme", const=True, when=_isFalse("mas_enable_walkme")),
    CommandArg(dest="mas_feature_usage", const=True, when=_isFalse("mas_feature_usage")),
    CommandArg(dest="mas_usability_metrics", const=True, when=_isFalse("mas_usability_metrics")),
    CommandArg(dest="mas_deployment_progression", const=True, when=_isFalse("mas_deployment_progression")),
    CommandArg(dest="enable_ipv6", const=True, when=_isTrue("enable_ipv6")),
    # Storage
    # -----------------------------------------------------------------------------
    CommandArg(dest="storage_class_rwo"),
    CommandArg(dest="storage_class_rwx"),
    CommandArg(dest="storage_pipeline", value=_attr("pipelineStorageClass")),
    CommandArg(dest="storage_accessmode", value=_attr("pipelineStorageAccessMode")),
    # IBM Suite License Service
    # -----------------------------------------------------------------------------
    CommandArg(dest="dedicated_sls", const=True, when=_dedicatedSls),
    CommandArg(dest="sls_namespace", when=lambda app: _ne("sls_namespace", "ibm-sls")(app) and not _dedicatedSls(app)),
    CommandArg(dest="sls_channel"),
    CommandArg(dest="license_file", value=_attr("slsLicenseFileLocal")),
    # IBM Data Reporting Operator (DRO)
    # -----------------------------------------------------------------------------
    CommandArg(dest="dro_contact_email"),
    CommandArg(dest="dro_contact_firstname"),
    CommandArg(dest="dro_contact_lastname"),
    CommandArg(dest="dro_namespace"),
    # MongoDb Community Operator
    # -----------------------------------------------------------------------------
    CommandArg(dest="mongodb_namespace"),
    CommandArg(dest="mongodb_provider", when=_attrTruthy("devMode")),
    # OCP Configuration
    # -----------------------------------------------------------------------------
    CommandArg(dest="ocp_ingress_tls_secret_name"),
    CommandArg(dest="ocp_ingress"),
    # Grafana
    # -----------------------------------------------------------------------------
    CommandArg(dest="skip_grafana_install", const=True, when=_attrTruthy("skipGrafanaInstall")),
    CommandArg(dest="grafana_v5_namespace"),
    CommandArg(dest="grafana_instance_storage_size"),
    # MAS Applications
    # -----------------------------------------------------------------------------
    CommandArg(dest="assist_channel", param="mas_app_channel_assist", when=_attrTruthy("installAssist")),
    CommandArg(dest="iot_channel", param="mas_app_channel_iot", when=_attrTruthy("installIoT")),
    CommandArg(dest="monitor_channel", param="mas_app_channel_monitor", when=_attrTruthy("installMonitor")),
    CommandArg(dest="manage_channel", param="mas_app_channel_manage", when=_installManage),
    CommandArg(dest="optimizer_channel", param="mas_app_channel_optimizer", when=_attrTruthy("installOptimizer")),
    CommandArg(dest="optimizer_plan", param="mas_app_plan_optimizer", when=_attrTruthy("installOptimizer")),
    CommandArg(dest="predict_channel", param="mas_app_channel_predict", when=_attrTruthy("installPredict")),
    CommandArg(dest="visualinspection_channel", param="mas_app_channel_visualinspection", when=_attrTruthy("installInspection")),
    CommandArg(dest="facilities_channel", param="mas_app_channel_facilities", when=_attrTruthy("installFacilities")),
    CommandArg(dest="aiservice_channel", when=_attrTruthy("installAIService")),
    CommandArg(dest="configure_aiassistant", when=_attrTruthy("installAIService")),
    CommandArg(dest="install_mcpi", const=True, when=_attrTruthy("installMcpi")),
    CommandArg(dest="mas_arcgis_channel", when=_attrTruthy("installArcgis")),
    # Manage Advanced Settings
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_appws_bindings_jdbc_manage", when=_installManage),
    CommandArg(dest="mas_appws_bindings_kafka_manage", when=_installManage),
    CommandArg(dest="mas_appws_components", when=_installManage),
    CommandArg(dest="mas_app_settings_server_bundles_size", when=_installManage),
    CommandArg(dest="mas_app_settings_default_jms", const=True, when=lambda app: _installManage(app) and _isTrue("mas_app_settings_default_jms")(app)),
    CommandArg(
        dest="mas_app_settings_persistent_volumes_flag",
        const=True,
        when=lambda app: _installManage(app) and _isTrue("mas_app_settings_persistent_volumes_flag")(app),
    ),
    CommandArg(dest="mas_app_settings_demodata", const=True, when=lambda app: _installManage(app) and _isTrue("mas_app_settings_demodata")(app)),
    CommandArg(dest="mas_app_settings_customization_archive_name", when=_installManage),
    CommandArg(dest="mas_app_settings_customization_archive_url", when=_installManage),
    CommandArg(dest="mas_app_settings_customization_archive_username", env_var="CUSTOMIZATION_ARCHIVE_USERNAME", when=_installManage),
    CommandArg(dest="mas_app_settings_customization_archive_password", env_var="CUSTOMIZATION_PASSWORD", when=_installManage),
    CommandArg(dest="mas_app_settings_tablespace", when=_installManage),
    CommandArg(dest="mas_app_settings_indexspace", when=_installManage),
    CommandArg(dest="mas_app_settings_db2_schema", when=_installManage),
    CommandArg(dest="mas_manage_encryptionsecret_crypto_key", env_var="CRYPTO_KEY", when=_installManage),
    CommandArg(dest="mas_manage_encryptionsecret_cryptox_key", env_var="CRYPTOX_KEY", when=_installManage),
    CommandArg(dest="mas_manage_encryptionsecret_old_crypto_key", env_var="OLD_CRYPTO_KEY", when=_installManage),
    CommandArg(dest="mas_manage_encryptionsecret_old_cryptox_key", env_var="OLD_CRYPTOX_KEY", when=_installManage),
    CommandArg(dest="mas_manage_ws_db_encryptionsecret", when=_installManage),
    CommandArg(dest="mas_app_settings_base_lang", when=_installManage),
    CommandArg(dest="mas_app_settings_secondary_langs", when=_installManage),
    CommandArg(dest="mas_app_settings_server_timezone", when=_installManage),
    CommandArg(dest="mas_manage_attachments_provider", when=_installManage),
    CommandArg(dest="mas_manage_attachment_configuration_mode", when=_installManage),
    CommandArg(
        dest="mas_appws_bindings_health_wsl_flag", const=True, when=lambda app: _installManage(app) and _isTrue("mas_appws_bindings_health_wsl_flag")(app)
    ),
    CommandArg(dest="mas_appws_upgrade_type", when=_installManage),
    CommandArg(dest="manage_bind_aiservice_instance_id", when=_installManage),
    CommandArg(dest="manage_bind_aiservice_tenant_id", when=_installManage),
    # Facilities Advanced Settings
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_ws_facilities_size", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_app_om_upgrade_mode", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_pull_policy", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_routes_timeout", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_liberty_extension_XML", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_vault_secret", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_dwfagents", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_db_maxconnpoolsize", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_log_class", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_log_mode", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_log_size", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_userfiles_class", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_userfiles_mode", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_storage_userfiles_size", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_server_timezone", when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_properties_file_local", value=_attr("facilitiesPropertiesFileLocal"), when=_attrTruthy("installFacilities")),
    CommandArg(dest="mas_ws_facilities_properties_secret_name", when=_attrTruthy("installFacilities")),
    *[CommandArg(dest=f"mas_ws_facilities_{agent}_deploymentmode", when=_attrTruthy("installFacilities")) for agent in facilitiesAgents],
    # AI Service Advanced Settings
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_instance_id", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_certificate_issuer", when=_attrTruthy("installAIService")),
    CommandArg(dest="db2_action_aiservice", const=True, when=lambda app: _attrTruthy("installAIService")(app) and _eq("db2_action_aiservice", "install")(app)),
    CommandArg(dest="aiservice_db_jdbc_url", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_db_username", env_var="AISERVICE_DB_USERNAME", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_db_password", env_var="AISERVICE_DB_PASSWORD", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_db_ca_cert", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_s3_accesskey", env_var="AISERVICE_S3_ACCESSKEY", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_secretkey", env_var="AISERVICE_S3_SECRETKEY", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_host", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_port", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_ssl", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_region", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_bucket_prefix", when=lambda app: _attrTruthy("installAIService")(app) and _externalS3(app)),
    CommandArg(dest="aiservice_s3_tenants_bucket", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_s3_templates_bucket", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_odh_model_deployment_type", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_rhoai_model_deployment_type", when=_attrTruthy("installAIService")),
    CommandArg(dest="rhoai_channel", when=_attrTruthy("installAIService")),
    CommandArg(dest="rhoai", const=True, when=lambda app: _attrTruthy("installAIService")(app) and _isTrue("rhoai")(app)),
    CommandArg(
        dest="mas_app_settings_persistent_volumes_flag",
        const=True,
        when=lambda app: _attrTruthy("installAIService")(app) and _isTrue("mas_app_settings_persistent_volumes_flag")(app),
    ),
    CommandArg(dest="aiservice_watsonxai_apikey", env_var="AISERVICE_WATSONXAI_APIKEY", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_url", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_project_id", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonx_action", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_ca_crt", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_deployment_id", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_space_id", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_instance_id", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_username", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_version", when=_attrTruthy("installAIService")),
    CommandArg(dest="aiservice_watsonxai_on_prem", when=_attrTruthy("installAIService")),
    CommandArg(dest="install_minio_aiservice", const=True, when=lambda app: _attrTruthy("installAIService")(app) and _ne("minio_root_user", "")(app)),
    CommandArg(dest="minio_root_user", env_var="MINIO_ROOT_USER", when=lambda app: _attrTruthy("installAIService")(app) and _ne("minio_root_user", "")(app)),
    CommandArg(
        dest="minio_root_password", env_var="MINIO_ROOT_PASSWORD", when=lambda app: _attrTruthy("installAIService")(app) and _ne("minio_root_password", "")(app)
    ),
    CommandArg(dest="tenant_entitlement_type", when=_attrTruthy("installAIService")),
    CommandArg(dest="tenant_entitlement_start_date", when=_attrTruthy("installAIService")),
    CommandArg(dest="tenant_entitlement_end_date", when=_attrTruthy("installAIService")),
    CommandArg(dest="tenant_scheduling_config_file", value=_attr("aiserviceTenantSchedulingConfigFileLocal"), when=_attrTruthy("installAIService")),
    CommandArg(dest="tenant_operator_config_file", value=_attr("aiserviceTenantOperatorConfigFileLocal"), when=_attrTruthy("installAIService")),
    CommandArg(dest="rsl_ca_crt", when=_attrTruthy("installAIService")),
    # IBM Cloud Pak for Data
    # -----------------------------------------------------------------------------
    CommandArg(dest="cpd_product_version"),
    CommandArg(dest="cpd_install_ws", const=True, when=_isTrue("cpd_install_ws")),
    CommandArg(dest="cpd_install_wml", const=True, when=_isTrue("cpd_install_wml")),
    CommandArg(dest="cpd_install_ae", const=True, when=_isTrue("cpd_install_ae")),
    # IBM Db2 Universal Operator
    # -----------------------------------------------------------------------------
    CommandArg(dest="db2_action_system", const=True, when=_eq("db2_action_system", "install")),
    CommandArg(dest="db2_action_manage", const=True, when=_eq("db2_action_manage", "install")),
    CommandArg(dest="db2_action_facilities", const=True, when=_eq("db2_action_facilities", "install")),
    CommandArg(dest="db2_channel", when=_db2Any),
    CommandArg(dest="db2_license_file", value=_attr("db2LicenseFileLocal"), when=_db2Any),
    CommandArg(dest="db2_namespace", when=_db2Universal),
    CommandArg(dest="db2_type", when=_db2Universal),
    CommandArg(dest="db2_timezone", when=_db2Action("db2_action_system", "db2_action_manage")),
    CommandArg(dest="db2_facilities_timezone", when=_eq("db2_action_facilities", "install")),
    CommandArg(dest="db2_affinity_key", when=_db2Universal),
    CommandArg(dest="db2_affinity_value", when=_db2Universal),
    CommandArg(dest="db2_tolerate_key", when=_db2Universal),
    CommandArg(dest="db2_tolerate_value", when=_db2Universal),
    CommandArg(dest="db2_tolerate_effect", when=_db2Universal),
    CommandArg(dest="db2_cpu_requests", when=_db2Universal),
    CommandArg(dest="db2_cpu_limits", when=_db2Universal),
    CommandArg(dest="db2_memory_requests", when=_db2Universal),
    CommandArg(dest="db2_memory_limits", when=_db2Universal),
    CommandArg(dest="db2_backup_storage_size", when=_db2Universal),
    CommandArg(dest="db2_data_storage_size", when=_db2Universal),
    CommandArg(dest="db2_logs_storage_size", when=_db2Universal),
    CommandArg(dest="db2_meta_storage_size", when=_db2Universal),
    CommandArg(dest="db2_temp_storage_size", when=_db2Universal),
    CommandArg(dest="db2u_kind", when=_db2Universal),
    # Kafka
    # -----------------------------------------------------------------------------
    CommandArg(dest="kafka_provider"),
    CommandArg(dest="kafka_username", when=_kafka),
    CommandArg(dest="kafka_password", env_var="KAFKA_PASSWORD", when=_kafka),
    CommandArg(dest="kafka_namespace", when=_kafka),
    CommandArg(dest="kafka_version", when=_kafka),
    # Kafka - MSK
    CommandArg(dest="aws_msk_instance_type", when=_kafka),
    CommandArg(dest="aws_msk_instance_number", when=_kafka),
    CommandArg(dest="aws_msk_volume_size", when=_kafka),
    CommandArg(dest="aws_msk_cidr_az1", when=_kafka),
    CommandArg(dest="aws_msk_cidr_az2", when=_kafka),
    CommandArg(dest="aws_msk_cidr_az3", when=_kafka),
    CommandArg(dest="aws_msk_egress_cidr", when=_kafka),
    CommandArg(dest="aws_msk_ingress_cidr", when=_kafka),
    # Kafka - Event Streams
    CommandArg(dest="eventstreams_resourcegroup", when=_kafka),
    CommandArg(dest="eventstreams_name", when=_kafka),
    CommandArg(dest="eventstreams_location", when=_kafka),
    # COS
    # -----------------------------------------------------------------------------
    CommandArg(dest="cos_type"),
    CommandArg(dest="cos_resourcegroup", when=_ne("cos_type", "")),
    CommandArg(dest="cos_region", when=_ne("cos_type", "")),
    CommandArg(dest="cos_apikey", env_var="COS_APIKEY", when=_ne("cos_type", "")),
    CommandArg(dest="cos_instance_name", when=_ne("cos_type", "")),
    CommandArg(dest="cos_bucket_name", when=_ne("cos_type", "")),
    # Cloud Providers
    # -----------------------------------------------------------------------------
    CommandArg(dest="ibmcloud_apikey", env_var="IBMCLOUD_APIKEY"),
    CommandArg(dest="aws_access_key_id", env_var="AWS_ACCESS_KEY_ID"),
    CommandArg(dest="aws_secret_access_key", env_var="AWS_SECRET_ACCESS_KEY"),
    CommandArg(dest="secret_access_key", env_var="SECRET_ACCESS_KEY"),
    CommandArg(dest="aws_region", when=_ne("secret_access_key", "")),
    CommandArg(dest="aws_vpc_id", when=_ne("secret_access_key", "")),
    # Development Mode
    # -----------------------------------------------------------------------------
    CommandArg(dest="artifactory_username", env_var="ARTIFACTORY_USERNAME", extra_exports=("ARTIFACTORY_TOKEN",)),
    CommandArg(dest="artifactory_token", env_var="ARTIFACTORY_TOKEN", when=_ne("artifactory_username", "")),
    # Approvals
    # -----------------------------------------------------------------------------
    CommandArg(dest="approval_core"),
    CommandArg(dest="approval_assist"),
    CommandArg(dest="approval_iot"),
    CommandArg(dest="approval_manage"),
    CommandArg(dest="approval_monitor"),
    CommandArg(dest="approval_optimizer"),
    CommandArg(dest="approval_predict"),
    CommandArg(dest="approval_visualinspection"),
    CommandArg(dest="approval_facilities"),
    CommandArg(dest="approval_aiservice"),
    # Slack
    # -----------------------------------------------------------------------------
    CommandArg(dest="slack_channel"),
    CommandArg(dest="slack_token", env_var="SLACK_TOKEN"),
    # More Options
    # -----------------------------------------------------------------------------
    CommandArg(dest="dev_mode", const=True, when=_attrTruthy("devMode")),
    CommandArg(dest="skip_pre_check", const=True, when=_isTrue("skip_pre_check")),
    CommandArg(dest="image_pull_policy"),
    CommandArg(dest="service_account_name"),
    CommandArg(dest="use_cli_digest", value=_attr("cliDigest"), when=lambda app: getattr(app, "useCliDigest", False) and getattr(app, "cliDigest", None)),
    CommandArg(dest="use_cli_digest", const=True, when=lambda app: getattr(app, "useCliDigest", False) and not getattr(app, "cliDigest", None)),
    # Footer
    # -----------------------------------------------------------------------------
    CommandArg(dest="accept_license", const=True, required=True),
    CommandArg(dest="no_confirm", const=True, required=True),
]


class installArgBuilderMixin:
    def buildCommand(self) -> str:
        """
        Render the equivalent non-interactive `mas install` command for the
        current wizard state, with secrets replaced by environment variables.
        """
        return renderCommand("mas install", INSTALL_COMMAND_ARGS, self, installArgParser)
