# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging

logger = logging.getLogger(__name__)


class GitOpsInstallArgBuilderMixin():
    """
    Mixin class for building non-interactive command-line arguments.

    This class provides functionality to generate a complete command-line
    string that can be used to reproduce the current installation configuration
    in non-interactive mode. This is useful for:
    - Saving installation configurations for reuse
    - Automating installations in CI/CD pipelines
    - Documenting installation parameters
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def getParam(self, param: str) -> str:
        ...  # type: ignore

    useTekton: bool  # type: ignore
    mas_app_ids: list  # type: ignore

    def buildCommand(self) -> str:
        """
        Build a complete non-interactive command string from current parameters.

        This method constructs a shell command that includes all necessary
        arguments to reproduce the current installation configuration without
        requiring interactive prompts.

        Returns:
            str: A formatted command string with all parameters

        Example:
            export IBM_ENTITLEMENT_KEY=x
            mas gitops-install --account-id myaccount \\
              --cluster-id cluster1 \\
              --instance-id inst1 \\
              --accept-license --no-confirm
        """
        newline = " \\\n"
        command = ""

        # Export sensitive environment variables
        if self.getParam('ibm_entitlement_key'):
            command += "export IBM_ENTITLEMENT_KEY=x\n"
        if self.getParam('gitops_repo_token_secret'):
            command += "export GITOPS_REPO_TOKEN_SECRET=x\n"
        if self.getParam('sm_aws_access_key_id'):
            command += "export SM_AWS_ACCESS_KEY_ID=x\n"
        if self.getParam('sm_aws_secret_access_key'):
            command += "export SM_AWS_SECRET_ACCESS_KEY=x\n"

        # Start command
        command += "mas gitops-install"

        # Execution Mode
        # Note: --use-tekton is the default, so we only add --direct when not using Tekton
        if hasattr(self, 'useTekton') and not self.useTekton:
            command += f" --direct{newline}"

        # GitOps Configuration
        if self.getParam('github_host'):
            command += f"  --github-host \"{self.getParam('github_host')}\"{newline}"
        if self.getParam('github_org'):
            command += f"  --github-org \"{self.getParam('github_org')}\"{newline}"
        if self.getParam('github_repo'):
            command += f"  --github-repo \"{self.getParam('github_repo')}\"{newline}"
        if self.getParam('git_branch') and self.getParam('git_branch') != 'main':
            command += f"  --git-branch \"{self.getParam('git_branch')}\"{newline}"
        if self.getParam('gitops_repo_token_secret'):
            command += f"  --gitops-repo-token-secret $GITOPS_REPO_TOKEN_SECRET{newline}"
        if self.getParam('account_id'):
            command += f"  --account-id \"{self.getParam('account_id')}\"{newline}"
        if self.getParam('cluster_id'):
            command += f"  --cluster-id \"{self.getParam('cluster_id')}\"{newline}"
        if self.getParam('cluster_url'):
            command += f"  --cluster-url \"{self.getParam('cluster_url')}\"{newline}"
        if self.getParam('secrets_path'):
            command += f"  --secrets-path \"{self.getParam('secrets_path')}\"{newline}"
        if self.getParam('avp_aws_secret_region'):
            command += f"  --avp-aws-secret-region \"{self.getParam('avp_aws_secret_region')}\"{newline}"
        if self.getParam('sm_aws_access_key_id'):
            command += f"  --sm-aws-access-key-id $SM_AWS_ACCESS_KEY_ID{newline}"
        if self.getParam('sm_aws_secret_access_key'):
            command += f"  --sm-aws-secret-access-key $SM_AWS_SECRET_ACCESS_KEY{newline}"

        # Cluster Configuration
        if self.getParam('mas_catalog_version'):
            command += f"  --mas-catalog-version \"{self.getParam('mas_catalog_version')}\"{newline}"
        if self.getParam('mas_catalog_image'):
            command += f"  --mas-catalog-image \"{self.getParam('mas_catalog_image')}\"{newline}"
        if self.getParam('ibm_entitlement_key'):
            command += f"  --ibm-entitlement-key $IBM_ENTITLEMENT_KEY{newline}"
        if self.getParam('install_dro'):
            command += f"  --install-dro \"{self.getParam('install_dro')}\"{newline}"
        if self.getParam('dro_namespace'):
            command += f"  --dro-namespace \"{self.getParam('dro_namespace')}\"{newline}"
        if self.getParam('dro_install_plan'):
            command += f"  --dro-install-plan \"{self.getParam('dro_install_plan')}\"{newline}"
        if self.getParam('dro_contact_email'):
            command += f"  --dro-contact-email \"{self.getParam('dro_contact_email')}\"{newline}"
        if self.getParam('dro_contact_firstname'):
            command += f"  --dro-contact-firstname \"{self.getParam('dro_contact_firstname')}\"{newline}"
        if self.getParam('dro_contact_lastname'):
            command += f"  --dro-contact-lastname \"{self.getParam('dro_contact_lastname')}\"{newline}"
        if self.getParam('install_gpu'):
            command += f"  --install-gpu \"{self.getParam('install_gpu')}\"{newline}"
        if self.getParam('gpu_namespace'):
            command += f"  --gpu-namespace \"{self.getParam('gpu_namespace')}\"{newline}"
        if self.getParam('install_cert_manager'):
            command += f"  --install-cert-manager \"{self.getParam('install_cert_manager')}\"{newline}"
        if self.getParam('install_nfd'):
            command += f"  --install-nfd \"{self.getParam('install_nfd')}\"{newline}"
        if self.getParam('storage_class_rwo'):
            command += f"  --storage-class-rwo \"{self.getParam('storage_class_rwo')}\"{newline}"
        if self.getParam('storage_class_rwx'):
            command += f"  --storage-class-rwx \"{self.getParam('storage_class_rwx')}\"{newline}"
        if self.getParam('ocp_domain'):
            command += f"  --ocp-domain \"{self.getParam('ocp_domain')}\"{newline}"
        if self.getParam('dns_provider'):
            command += f"  --dns-provider \"{self.getParam('dns_provider')}\"{newline}"

        # Instance Configuration
        if self.getParam('mas_instance_id'):
            command += f"  --mas-instance-id \"{self.getParam('mas_instance_id')}\"{newline}"
        if self.getParam('mas_channel'):
            command += f"  --mas-channel \"{self.getParam('mas_channel')}\"{newline}"
        if self.getParam('mas_domain'):
            command += f"  --mas-domain \"{self.getParam('mas_domain')}\"{newline}"
        if self.getParam('mas_workspace_id'):
            command += f"  --mas-workspace-id \"{self.getParam('mas_workspace_id')}\"{newline}"
        if self.getParam('mas_workspace_name'):
            command += f"  --mas-workspace-name \"{self.getParam('mas_workspace_name')}\"{newline}"
        if self.getParam('operational_mode'):
            command += f"  --operational-mode \"{self.getParam('operational_mode')}\"{newline}"
        if self.getParam('sls_channel'):
            command += f"  --sls-channel \"{self.getParam('sls_channel')}\"{newline}"
        if self.getParam('sls_instance_name'):
            command += f"  --sls-instance-name \"{self.getParam('sls_instance_name')}\"{newline}"
        if self.getParam('mongo_provider'):
            command += f"  --mongo-provider \"{self.getParam('mongo_provider')}\"{newline}"
        if self.getParam('mongo_namespace'):
            command += f"  --mongo-namespace \"{self.getParam('mongo_namespace')}\"{newline}"
        if self.getParam('mongodb_action'):
            command += f"  --mongodb-action \"{self.getParam('mongodb_action')}\"{newline}"
        if self.getParam('mongo_yaml_file'):
            command += f"  --mongo-yaml-file \"{self.getParam('mongo_yaml_file')}\"{newline}"
        if self.getParam('mongo_username'):
            command += f"  --mongo-username \"{self.getParam('mongo_username')}\"{newline}"
        if self.getParam('mongo_password'):
            command += f"  --mongo-password \"{self.getParam('mongo_password')}\"{newline}"

        # Dependencies Configuration (optional)
        if self.getParam('vpc_ipv4_cidr'):
            command += f"  --vpc-ipv4-cidr \"{self.getParam('vpc_ipv4_cidr')}\"{newline}"
        if self.getParam('aws_docdb_instance_number'):
            command += f"  --aws-docdb-instance-number \"{self.getParam('aws_docdb_instance_number')}\"{newline}"
        if self.getParam('aws_docdb_engine_version'):
            command += f"  --aws-docdb-engine-version \"{self.getParam('aws_docdb_engine_version')}\"{newline}"
        if self.getParam('kafka_provider'):
            command += f"  --kafka-provider \"{self.getParam('kafka_provider')}\"{newline}"
        if self.getParam('kafka_version'):
            command += f"  --kafka-version \"{self.getParam('kafka_version')}\"{newline}"
        if self.getParam('kafka_action'):
            command += f"  --kafka-action \"{self.getParam('kafka_action')}\"{newline}"
        if self.getParam('kafkacfg_file_name'):
            command += f"  --kafkacfg-file-name \"{self.getParam('kafkacfg_file_name')}\"{newline}"
        if self.getParam('aws_msk_instance_type'):
            command += f"  --aws-msk-instance-type \"{self.getParam('aws_msk_instance_type')}\"{newline}"
        if self.getParam('efs_action'):
            command += f"  --efs-action \"{self.getParam('efs_action')}\"{newline}"
        if self.getParam('cloud_provider'):
            command += f"  --cloud-provider \"{self.getParam('cloud_provider')}\"{newline}"
        if self.getParam('ibmcloud_resourcegroup'):
            command += f"  --ibmcloud-resourcegroup \"{self.getParam('ibmcloud_resourcegroup')}\"{newline}"
        if self.getParam('ibmcloud_apikey'):
            command += f"  --ibmcloud-apikey \"{self.getParam('ibmcloud_apikey')}\"{newline}"
        if self.getParam('cos_type'):
            command += f"  --cos-type \"{self.getParam('cos_type')}\"{newline}"
        if self.getParam('cos_resourcegroup'):
            command += f"  --cos-resourcegroup \"{self.getParam('cos_resourcegroup')}\"{newline}"
        if self.getParam('cos_action'):
            command += f"  --cos-action \"{self.getParam('cos_action')}\"{newline}"
        if self.getParam('cos_use_hmac'):
            command += f"  --cos-use-hmac \"{self.getParam('cos_use_hmac')}\"{newline}"
        if self.getParam('cos_apikey'):
            command += f"  --cos-apikey \"{self.getParam('cos_apikey')}\"{newline}"
        if self.getParam('github_pat'):
            command += f"  --github-pat \"{self.getParam('github_pat')}\"{newline}"

        # SMTP Configuration (optional)
        if self.getParam('smtp_host'):
            command += f"  --smtp-host \"{self.getParam('smtp_host')}\"{newline}"
        if self.getParam('smtp_port'):
            command += f"  --smtp-port \"{self.getParam('smtp_port')}\"{newline}"
        if self.getParam('smtp_username'):
            command += f"  --smtp-username \"{self.getParam('smtp_username')}\"{newline}"
        if self.getParam('smtp_password'):
            command += f"  --smtp-password \"{self.getParam('smtp_password')}\"{newline}"
        if self.getParam('smtp_from'):
            command += f"  --smtp-from \"{self.getParam('smtp_from')}\"{newline}"

        # LDAP Configuration (optional)
        if self.getParam('ldap_url'):
            command += f"  --ldap-url \"{self.getParam('ldap_url')}\"{newline}"
        if self.getParam('ldap_bind_dn'):
            command += f"  --ldap-bind-dn \"{self.getParam('ldap_bind_dn')}\"{newline}"
        if self.getParam('ldap_bind_password'):
            command += f"  --ldap-bind-password \"{self.getParam('ldap_bind_password')}\"{newline}"
        if self.getParam('ldap_user_base_dn'):
            command += f"  --ldap-user-base-dn \"{self.getParam('ldap_user_base_dn')}\"{newline}"
        if self.getParam('ldap_group_base_dn'):
            command += f"  --ldap-group-base-dn \"{self.getParam('ldap_group_base_dn')}\"{newline}"
        if self.getParam('ldap_certificate_file'):
            command += f"  --ldap-certificate-file \"{self.getParam('ldap_certificate_file')}\"{newline}"

        # Advanced GitOps Configuration Files
        if self.getParam('sls_entitlement_file'):
            command += f"  --sls-entitlement-file \"{self.getParam('sls_entitlement_file')}\"{newline}"
        if self.getParam('dro_ca_certificate_file'):
            command += f"  --dro-ca-certificate-file \"{self.getParam('dro_ca_certificate_file')}\"{newline}"
        if self.getParam('mas_manual_certs_yaml'):
            command += f"  --mas-manual-certs-yaml \"{self.getParam('mas_manual_certs_yaml')}\"{newline}"
        if self.getParam('mas_pod_template_file'):
            command += f"  --mas-pod-template-file \"{self.getParam('mas_pod_template_file')}\"{newline}"
        if self.getParam('mas_bascfg_pod_template_file'):
            command += f"  --mas-bascfg-pod-template-file \"{self.getParam('mas_bascfg_pod_template_file')}\"{newline}"
        if self.getParam('mas_slscfg_pod_template_file'):
            command += f"  --mas-slscfg-pod-template-file \"{self.getParam('mas_slscfg_pod_template_file')}\"{newline}"
        if self.getParam('mas_smtpcfg_pod_template_file'):
            command += f"  --mas-smtpcfg-pod-template-file \"{self.getParam('mas_smtpcfg_pod_template_file')}\"{newline}"
        if self.getParam('mas_appcfg_pod_template_file'):
            command += f"  --mas-appcfg-pod-template-file \"{self.getParam('mas_appcfg_pod_template_file')}\"{newline}"
        if self.getParam('suite_spec_additional_properties_yaml'):
            command += f"  --suite-spec-additional-properties-yaml \"{self.getParam('suite_spec_additional_properties_yaml')}\"{newline}"
        if self.getParam('suite_spec_settings_additional_properties_yaml'):
            command += f"  --suite-spec-settings-additional-properties-yaml \"{self.getParam('suite_spec_settings_additional_properties_yaml')}\"{newline}"
        if self.getParam('smtp_config_ca_certificate_file'):
            command += f"  --smtp-config-ca-certificate-file \"{self.getParam('smtp_config_ca_certificate_file')}\"{newline}"

        # Applications Configuration
        if self.getParam('mas_app_ids'):
            command += f"  --mas-app-ids \"{self.getParam('mas_app_ids')}\"{newline}"

            # Per-app configuration
            if hasattr(self, 'mas_app_ids'):
                for app_id in self.mas_app_ids:
                    app_arg = app_id.replace('-', '')

                    if self.getParam(f'{app_id}_channel'):
                        command += f"  --{app_arg}-channel \"{self.getParam(f'{app_id}_channel')}\"{newline}"
                    if self.getParam(f'{app_id}_db_action'):
                        command += f"  --{app_arg}-db-action \"{self.getParam(f'{app_id}_db_action')}\"{newline}"
                    if self.getParam(f'{app_id}_db_type'):
                        command += f"  --{app_arg}-db-type \"{self.getParam(f'{app_id}_db_type')}\"{newline}"
                    if self.getParam(f'{app_id}_db_host'):
                        command += f"  --{app_arg}-db-host \"{self.getParam(f'{app_id}_db_host')}\"{newline}"
                    if self.getParam(f'{app_id}_db_port'):
                        command += f"  --{app_arg}-db-port \"{self.getParam(f'{app_id}_db_port')}\"{newline}"
                    if self.getParam(f'{app_id}_db_name'):
                        command += f"  --{app_arg}-db-name \"{self.getParam(f'{app_id}_db_name')}\"{newline}"
                    if self.getParam(f'{app_id}_db_username'):
                        command += f"  --{app_arg}-db-username \"{self.getParam(f'{app_id}_db_username')}\"{newline}"
                    if self.getParam(f'{app_id}_db_password'):
                        command += f"  --{app_arg}-db-password \"{self.getParam(f'{app_id}_db_password')}\"{newline}"

                    # App-specific advanced configuration files
                    if app_id in ['manage', 'iot', 'facilities']:
                        if self.getParam(f'db2_{app_id}_config_file'):
                            command += f"  --db2-{app_arg}-config-file \"{self.getParam(f'db2_{app_id}_config_file')}\"{newline}"

                    if self.getParam(f'mas_appws_spec_{app_id}_file'):
                        command += f"  --mas-appws-spec-{app_arg}-file \"{self.getParam(f'mas_appws_spec_{app_id}_file')}\"{newline}"

                    if self.getParam(f'mas_app_spec_{app_id}_file'):
                        command += f"  --mas-app-spec-{app_arg}-file \"{self.getParam(f'mas_app_spec_{app_id}_file')}\"{newline}"

                    if self.getParam(f'jdbc_cert_{app_id}_file'):
                        command += f"  --jdbc-cert-{app_arg}-file \"{self.getParam(f'jdbc_cert_{app_id}_file')}\"{newline}"

                    if app_id == 'manage':
                        if self.getParam('mas_app_global_secrets_manage_file'):
                            command += f"  --mas-app-global-secrets-manage-file \"{self.getParam('mas_app_global_secrets_manage_file')}\"{newline}"

        # Final flags
        command += "  --accept-license --no-confirm"

        return command
