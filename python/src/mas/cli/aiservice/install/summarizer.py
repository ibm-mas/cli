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
        self.printParamSummary("Environment Type", "environment_type")

        self.printH2("AI Service Tenant Entitlement")
        self.printParamSummary("Entitlement Type", "tenant_entitlement_type")
        self.printParamSummary("Start Date", "tenant_entitlement_start_date")
        self.printParamSummary("End Date", "tenant_entitlement_end_date")

        self.printH2("S3 Configuration")
        # self.printParamSummary("Storage provider", "aiservice_s3_provider")
        if self.getParam("minio_root_user") is not None and self.getParam("minio_root_user") != "":
            self.printParamSummary("Minio Root Username", "minio_root_user")
        print()
        self.printParamSummary("Host", "aiservice_s3_host")
        self.printParamSummary("Port", "aiservice_s3_port")
        self.printParamSummary("SSL Enabled", "aiservice_s3_ssl")
        self.printParamSummary("Region", "aiservice_s3_region")
        self.printParamSummary("Bucket Prefix", "aiservice_s3_bucket_prefix")
        self.printParamSummary("Templates Bucket Name", "aiservice_s3_templates_bucket")
        self.printParamSummary("Tenants Bucket Name", "aiservice_s3_tenants_bucket")

        self.printH2("IBM WatsonX")
        self.printParamSummary("URL", "aiservice_watsonxai_url")
        self.printParamSummary("Project ID", "aiservice_watsonxai_project_id")

        self.printH2("RSL")
        self.printParamSummary("URL", "rsl_url")
        self.printParamSummary("Organization ID", "rsl_org_id")

    def db2Summary(self) -> None:
        self.printH2("IBM Db2 Univeral Operator Configuration")
        self.printParamSummary("Action", "db2_action_aiservice")
        self.printParamSummary("Install Namespace", "db2_namespace")
        self.printParamSummary("Subscription Channel", "db2_channel")

    def droSummary(self) -> None:
        self.printH2("IBM Data Reporter Operator (DRO) Configuration")
        self.printParamSummary("Contact e-mail", "dro_contact_email")
        self.printParamSummary("First name", "dro_contact_firstname")
        self.printParamSummary("Last name", "dro_contact_lastname")
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
