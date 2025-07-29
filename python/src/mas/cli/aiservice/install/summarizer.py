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
import yaml
from mas.devops.ocp import getConsoleURL

logger = logging.getLogger(__name__)


class aiServiceInstallSummarizerMixin():
    def ocpSummary(self) -> None:
        self.printH2("Pipeline Configuration")
        self.printParamSummary("Service Account", "service_account_name")
        self.printParamSummary("Image Pull Policy", "image_pull_policy")
        self.printSummary("Skip Pre-Install Healthcheck", "Yes" if self.getParam('skip_pre_check') == "true" else "No")

        self.printH2("OpenShift Container Platform")
        self.printSummary("Worker Node Architecture", self.architecture)
        self.printSummary("Storage Class Provider", self.storageClassProvider)
        self.printParamSummary("ReadWriteOnce Storage Class", "storage_class_rwo")
        self.printParamSummary("ReadWriteMany Storage Class", "storage_class_rwx")

        self.printParamSummary("Certificate Manager", "cert_manager_provider")
        self.printParamSummary("Cluster Ingress Certificate Secret", "ocp_ingress_tls_secret_name")

    def aiServiceSummary(self) -> None:
        self.printH2("Maximo Operator Catalog")
        self.printParamSummary("Catalog Version", "mas_catalog_version")
        # We only list the digest if it's specified (primary use case is when running development builds in airgap environments)
        if self.getParam("mas_catalog_digest" != ""):
            self.printParamSummary("Catalog Digest", "mas_catalog_digest")

        self.printH2("IBM Container Registry")
        self.printParamSummary("IBM Entitled Registry", "mas_icr_cp")
        self.printParamSummary("IBM Open Registry", "mas_icr_cpopen")

        self.printH2("AI Service")
        self.printParamSummary("Release", "aiservice_channel")
        self.printParamSummary("Instance ID", "aiservice_instance_id")
        self.printParamSummary("Environment type", "environment_type")

        self.printH2("S3 Configuration")
        self.printParamSummary("Storage provider", "aiservice_storage_provider")
        if self.getParam("aiservice_storage_provider") == "minio":
            self.printParamSummary("minio root username", "minio_root_user")
        print()
        self.printParamSummary("Storage access key", "aiservice_storage_accesskey")
        self.printParamSummary("Storage host", "aiservice_storage_host")
        self.printParamSummary("Storage port", "aiservice_storage_port")
        self.printParamSummary("Storage ssl", "aiservice_storage_ssl")
        self.printParamSummary("Storage region", "aiservice_storage_region")
        self.printParamSummary("Storage pipelines bucket", "aiservice_storage_pipelines_bucket")
        self.printParamSummary("Storage tenants bucket", "aiservice_storage_tenants_bucket")
        self.printParamSummary("Storage templates bucket", "aiservice_storage_templates_bucket")
        print()
        self.printParamSummary("S3 bucket prefix", "aiservice_s3_bucket_prefix")
        self.printParamSummary("S3 endpoint url", "aiservice_s3_endpoint_url")
        self.printParamSummary("S3 bucket prefix (tenant level)", "aiservice_tenant_s3_bucket_prefix")
        self.printParamSummary("S3 region (tenant level)", "aiservice_tenant_s3_region")
        self.printParamSummary("S3 endpoint url (tenant level)", "aiservice_tenant_s3_endpoint_url")

        self.printH2("IBM WatsonX")
        self.printParamSummary("Watsonxai machine learning url", "aiservice_watsonxai_url")
        self.printParamSummary("Watsonxai project id", "aiservice_watsonxai_project_id")

        self.printH2("AI Service Tenant")
        self.printParamSummary("Tenant entitlement type", "tenant_entitlement_type")
        self.printParamSummary("Tenant start date", "tenant_entitlement_start_date")
        self.printParamSummary("Tenant end date", "tenant_entitlement_end_date")

        self.printH2("RSL")
        self.printParamSummary("RSL url", "rsl_url")
        self.printParamSummary("ORG Id of RSL", "rsl_org_id")
        self.printParamSummary("Token for RSL", "rsl_token")

    def db2Summary(self) -> None:
        self.printH2("IBM Db2 Univeral Operator Configuration")
        self.printParamSummary("Action", "db2_action_aiservice")
        self.printParamSummary("Install Namespace", "db2_namespace")
        self.printParamSummary("Subscription Channel", "db2_channel")

    def droSummary(self) -> None:
        self.printH2("IBM Data Reporter Operator (DRO) Configuration")
        self.printParamSummary("Contact e-mail", "uds_contact_email")
        self.printParamSummary("First name", "uds_contact_firstname")
        self.printParamSummary("Last name", "uds_contact_lastname")
        self.printParamSummary("Install Namespace", "dro_namespace")

    def slsSummary(self) -> None:
        self.printH2("IBM Suite License Service")
        self.printParamSummary("Namespace", "sls_namespace")
        if self.getParam("sls_action") == "install":
            self.printSummary("Subscription Channel", "3.x")
            self.printParamSummary("IBM Open Registry", "sls_icr_cpopen")
            if self.slsLicenseFileLocal:
                self.printSummary("License File", self.slsLicenseFileLocal)

    def mongoSummary(self) -> None:
        self.printH2("MongoDb")
        if self.getParam("mongodb_action") == "install":
            self.printSummary("Type", "MongoCE Operator")
            self.printParamSummary("Install Namespace", "mongodb_namespace")
        elif self.getParam("mongodb_action") == "byo":
            self.printSummary("Type", "BYO (mongodb-system.yaml)")
        else:
            self.fatalError(f"Unexpected value for mongodb_action parameter: {self.getParam('mongodb_action')}")

    def displayInstallSummary(self) -> None:
        self.printH1("Review Settings")
        self.printDescription([
            "Connected to:",
            f" - <u>{getConsoleURL(self.dynamicClient)}</u>"
        ])

        logger.debug("PipelineRun parameters:")
        logger.debug(yaml.dump(self.params, default_flow_style=False))

        # Cluster Config & AI Service
        self.ocpSummary()
        self.aiServiceSummary()

        # Dependencies
        self.droSummary()
        self.slsSummary()
        self.mongoSummary()
        self.db2Summary()
