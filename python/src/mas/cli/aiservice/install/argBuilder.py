# *****************************************************************************
# Copyright (c) 2025, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Declarative specification of the non-interactive `mas aiservice-install`
command that the interactive wizard prints at the end of a run.

Each entry names the argparse dest it maps to; the flag spelling is resolved
from the real aiServiceinstallArgParser at render time (see
common.commandBuilder).  Only what argparse cannot express is spelled out
here: where a value comes from, which parameters are secrets (env-masked
with an export placeholder), and the conditions under which a flag is
emitted.
"""

from ...common.commandBuilder import CommandArg, paramIsTrue, renderCommand
from .argParser import aiServiceinstallArgParser

# ---------------------------------------------------------------------------
# Condition helpers
# ---------------------------------------------------------------------------

# Boolean conditions use paramIsTrue from common.commandBuilder: interactive
# runs store 'true'/'false' strings, non-interactive runs copy argparse's
# native booleans into params, and both must work.
_isTrue = paramIsTrue


def _eq(param: str, expected: str):
    return lambda app: app.getParam(param) == expected


def _ne(param: str, unexpected: str):
    return lambda app: app.getParam(param) != unexpected


def _attr(name: str, default=None):
    return lambda app: getattr(app, name, default)


def _attrTruthy(name: str):
    return lambda app: bool(getattr(app, name, False))


def _dedicatedSls(app) -> bool:
    instanceId = app.getParam("aiservice_instance_id")
    return instanceId != "" and app.getParam("sls_namespace") == f"mas-{instanceId}-sls"


# CIS enhanced security options are only prompted for when enhanced security is enabled
_cis = _eq("dns_provider", "cis")
_cisEnhanced = lambda app: _cis(app) and _isTrue("cis_enhanced_security")(app)  # noqa: E731


# ---------------------------------------------------------------------------
# Command specification
# ---------------------------------------------------------------------------

AISERVICE_INSTALL_COMMAND_ARGS = [
    # MAS Catalog Selection & Entitlement
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_catalog_version"),
    CommandArg(dest="mas_catalog_digest"),
    CommandArg(dest="ibm_entitlement_key", env_var="IBM_ENTITLEMENT_KEY", required=True),
    # AI Service Instance
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_instance_id"),
    CommandArg(dest="additional_configs", value=_attr("localConfigDir")),
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
    # AI Service Channel
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_channel"),
    # Development Mode
    # -----------------------------------------------------------------------------
    CommandArg(dest="artifactory_username", env_var="ARTIFACTORY_USERNAME", extra_exports=("ARTIFACTORY_TOKEN",)),
    CommandArg(dest="artifactory_token", env_var="ARTIFACTORY_TOKEN", when=_ne("artifactory_username", "")),
    # Approvals
    # -----------------------------------------------------------------------------
    CommandArg(dest="approval_aiservice"),
    # More Options
    # -----------------------------------------------------------------------------
    CommandArg(dest="dev_mode", const=True, when=_attrTruthy("devMode")),
    CommandArg(dest="skip_pre_check", const=True, when=_isTrue("skip_pre_check")),
    CommandArg(dest="image_pull_policy"),
    CommandArg(dest="service_account_name"),
    # OCP Configuration
    # -----------------------------------------------------------------------------
    CommandArg(dest="ocp_ingress_tls_secret_name"),
    CommandArg(dest="ocp_ingress"),
    # Certificate Issuer & Domain
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_certificate_issuer"),
    CommandArg(dest="aiservice_domain"),
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
    CommandArg(dest="route53_hosted_zone_name", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_hosted_zone_region", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_subdomain", when=_eq("dns_provider", "route53")),
    CommandArg(dest="route53_email", when=_eq("dns_provider", "route53")),
    CommandArg(dest="aws_access_key_id", env_var="AWS_ACCESS_KEY_ID", when=_eq("dns_provider", "route53")),
    CommandArg(dest="aws_secret_access_key", env_var="AWS_SECRET_ACCESS_KEY", when=_eq("dns_provider", "route53")),
    CommandArg(dest="enable_ipv6", const=True, when=_isTrue("enable_ipv6")),
    # Object Storage
    # -----------------------------------------------------------------------------
    CommandArg(dest="install_ceph", const=True, when=_isTrue("install_ceph")),
    CommandArg(dest="aiservice_s3_accesskey", env_var="AISERVICE_S3_ACCESSKEY", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_secretkey", env_var="AISERVICE_S3_SECRETKEY", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_host", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_port", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_ssl", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_region", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_bucket_prefix", when=_ne("install_ceph", "true")),
    CommandArg(dest="aiservice_s3_tenants_bucket"),
    CommandArg(dest="aiservice_s3_templates_bucket"),
    # Model Deployment
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_odh_model_deployment_type"),
    CommandArg(dest="aiservice_rhoai_model_deployment_type"),
    CommandArg(dest="rhoai_channel"),
    CommandArg(dest="rhoai", const=True, when=_isTrue("rhoai")),
    # Watsonx
    # -----------------------------------------------------------------------------
    CommandArg(dest="aiservice_watsonxai_apikey", env_var="AISERVICE_WATSONXAI_APIKEY"),
    CommandArg(dest="aiservice_watsonxai_url"),
    CommandArg(dest="aiservice_watsonxai_project_id"),
    CommandArg(dest="aiservice_watsonx_action"),
    CommandArg(dest="aiservice_watsonxai_ca_crt"),
    CommandArg(dest="aiservice_watsonxai_deployment_id"),
    CommandArg(dest="aiservice_watsonxai_space_id"),
    CommandArg(dest="aiservice_watsonxai_instance_id"),
    CommandArg(dest="aiservice_watsonxai_username"),
    CommandArg(dest="aiservice_watsonxai_version"),
    CommandArg(dest="aiservice_watsonxai_on_prem"),
    # Tenant Entitlement
    # -----------------------------------------------------------------------------
    CommandArg(dest="tenant_entitlement_type"),
    CommandArg(dest="tenant_entitlement_start_date"),
    CommandArg(dest="tenant_entitlement_end_date"),
    CommandArg(dest="tenant_scheduling_config_file", value=_attr("aiserviceTenantSchedulingConfigFileLocal")),
    CommandArg(dest="tenant_operator_config_file", value=_attr("aiserviceTenantOperatorConfigFileLocal")),
    CommandArg(dest="rsl_ca_crt"),
    # Database Configuration
    # -----------------------------------------------------------------------------
    CommandArg(dest="db2_action_aiservice", const=True, when=_eq("db2_action_aiservice", "install")),
    CommandArg(dest="db2_channel", when=_eq("db2_action_aiservice", "install")),
    CommandArg(dest="db2_license_file", value=_attr("db2LicenseFileLocal"), when=_eq("db2_action_aiservice", "install")),
    CommandArg(dest="aiservice_db_jdbc_url"),
    CommandArg(dest="aiservice_db_username", env_var="AISERVICE_DB_USERNAME"),
    CommandArg(dest="aiservice_db_password", env_var="AISERVICE_DB_PASSWORD"),
    CommandArg(dest="aiservice_db_ca_cert"),
    # Footer
    # -----------------------------------------------------------------------------
    CommandArg(dest="accept_license", const=True, required=True),
    CommandArg(dest="no_confirm", const=True, required=True),
]


class aiServiceInstallArgBuilderMixin:
    def buildCommand(self) -> str:
        """
        Render the equivalent non-interactive `mas aiservice-install` command
        for the current wizard state, with secrets replaced by environment
        variables.
        """
        return renderCommand("mas aiservice-install", AISERVICE_INSTALL_COMMAND_ARGS, self, aiServiceinstallArgParser)
