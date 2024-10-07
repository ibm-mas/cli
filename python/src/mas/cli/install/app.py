#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
import logging.handlers
from sys import exit
from os import path
import re

from openshift.dynamic.exceptions import NotFoundError

from prompt_toolkit import prompt, print_formatted_text, HTML

from tabulate import tabulate

from halo import Halo

from ..cli import BaseApp
from ..gencfg import ConfigGeneratorMixin
from .argBuilder import installArgBuilderMixin
from .argParser import installArgParser
from .settings import InstallSettingsMixin
from .summarizer import InstallSummarizerMixin

from mas.cli.validators import (
  InstanceIDFormatValidator,
  WorkspaceIDFormatValidator,
  WorkspaceNameFormatValidator,
  TimeoutFormatValidator,
  StorageClassValidator,
  OptimizerInstallPlanValidator
)

from mas.devops.ocp import createNamespace, getStorageClass, getStorageClasses
from mas.devops.tekton import (
    installOpenShiftPipelines,
    updateTektonDefinitions,
    preparePipelinesNamespace,
    prepareInstallSecrets,
    testCLI,
    launchInstallPipeline
)

logger = logging.getLogger(__name__)


class InstallApp(BaseApp, InstallSettingsMixin, InstallSummarizerMixin, ConfigGeneratorMixin, installArgBuilderMixin):
    def validateCatalogSource(self):
        catalogsAPI = self.dynamicClient.resources.get(api_version="operators.coreos.com/v1alpha1", kind="CatalogSource")
        try:
            catalog = catalogsAPI.get(name="ibm-operator-catalog", namespace="openshift-marketplace")
            catalogDisplayName = catalog.spec.displayName

            m = re.match(r".+(?P<catalogId>v[89]-(?P<catalogVersion>[0-9]+)-amd64)", catalogDisplayName)
            if m:
                # catalogId = v8-yymmdd-amd64
                # catalogVersion = yymmdd
                catalogId = m.group("catalogId")
            elif re.match(r".+v8-amd64", catalogDisplayName):
                catalogId = "v8-amd64"
            else:
                self.fatalError(f"IBM Maximo Operator Catalog is already installed on this cluster. However, it is not possible to identify its version. If you wish to install a new MAS instance using the {self.getParam('mas_catalog_version')} catalog please first run 'mas update' to switch to this catalog, this will ensure the appropriate actions are performed as part of the catalog update")

            if catalogId != self.getParam("mas_catalog_version"):
                self.fatalError(f"IBM Maximo Operator Catalog {catalogId} is already installed on this cluster, if you wish to install a new MAS instance using the {self.getParam('mas_catalog_version')} catalog please first run 'mas update' to switch to this catalog, this will ensure the appropriate actions are performed as part of the catalog update")
        except NotFoundError:
            # There's no existing catalog installed
            pass

    def validateInternalRegistryAvailable(self):
        """
        We can save customers wasted time by detecting if the image-registry service
        is available in the cluster.  If it's not, and they've selected to install
        Manage then their install is going to fail, so let's just prevent the install
        starting in the first place.
        """
        serviceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Service")
        try:
            serviceAPI.get(name="image-registry", namespace="openshift-image-registry")
        except NotFoundError:
            self.fatalError(
                "\n".join([
                    "Unable to proceed with installation of Maximo Manage.  Could not detect the required \"image-registry\" service in the openshift-image-registry namespace",
                    "For more information refer to <u>https://www.ibm.com/docs/en/masv-and-l/continuous-delivery?topic=installing-enabling-openshift-internal-image-registry</u>"
                ])
            )

    def licensePrompt(self):
        licenses = {
            "8.9.x": " - <u>https://ibm.biz/MAS89-License</u>",
            "8.10.x": " - <u>https://ibm.biz/MAS810-License</u>",
            "8.11.x": " - <u>https://ibm.biz/MAS811-License</u>\n - <u>https://ibm.biz/MAXIT81-License</u>",
            "9.0.x": " - <u>https://ibm.biz/MAS90-License</u>\n - <u>https://ibm.biz/MaximoIT90-License</u>\n - <u>https://ibm.biz/MAXArcGIS90-License</u>"
        }

        if not self.licenseAccepted:
            self.printH1("License Terms")
            self.printDescription([
                "To continue with the installation, you must accept the license terms:",
                licenses[self.getParam('mas_channel')]
            ])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

    def configICR(self):
        if self.devMode:
            self.setParam("mas_icr_cp", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local")
            self.setParam("mas_icr_cpopen", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen")
            self.setParam("sls_icr_cpopen", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen")
        else:
            self.setParam("mas_icr_cp", "cp.icr.io/cp")
            self.setParam("mas_icr_cpopen", "icr.io/cpopen")
            self.setParam("sls_icr_cpopen", "icr.io/cpopen")

    def configICRCredentials(self):
        self.printH1("Configure IBM Container Registry")
        self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
        if self.devMode:
            self.promptForString("Artifactory username", "artifactory_username", isPassword=True)
            self.promptForString("Artifactory token", "artifactory_token", isPassword=True)

    def configCertManager(self):
        # Only install of Red Hat Cert-Manager has been supported since the January 2025 catalog update
        self.setParam("cert_manager_provider", "redhat")
        self.setParam("cert_manager_action", "install")

    def configCatalog(self):
        self.printH1("IBM Maximo Operator Catalog Selection")
        if self.devMode:
            self.promptForString("Select catalog source", "mas_catalog_version", default="v9-master-amd64")
            self.promptForString("Select channel", "mas_channel", default="9.1.x-dev")
        else:
            print(tabulate(self.installOptions, headers="keys", tablefmt="simple_grid"))
            catalogSelection = self.promptForInt("Select catalog and release", default=1)

            self.setParam("mas_catalog_version", self.installOptions[catalogSelection-1]["catalog"])
            self.setParam("mas_channel", self.installOptions[catalogSelection-1]["release"])

    def configSLS(self) -> None:
        self.printH1("Configure Product License")
        self.slsLicenseFileLocal = self.promptForFile("License file", mustExist=True, envVar="SLS_LICENSE_FILE_LOCAL")
        self.promptForString("Contact e-mail address", "uds_contact_email")
        self.promptForString("Contact first name", "uds_contact_firstname")
        self.promptForString("Contact last name", "uds_contact_lastname")

        self.promptForString("IBM Data Reporter Operator (DRO) Namespace", "dro_namespace", default="redhat-marketplace")

    def selectLocalConfigDir(self) -> None:
        if self.localConfigDir is None:
            # You need to tell us where the configuration file can be found
            self.localConfigDir = self.promptForDir("Select Local configuration directory")

    def configGrafana(self) -> None:
        try:
            packagemanifestAPI = self.dynamicClient.resources.get(api_version="packages.operators.coreos.com/v1", kind="PackageManifest")
            packagemanifestAPI.get(name="grafana-operator", namespace="openshift-marketplace")
            if self.skipGrafanaInstall:
                self.setParam("grafana_action", "none")
            else:
                self.setParam("grafana_action", "install")
        except NotFoundError:
            self.setParam("grafana_action", "none")

        if self.interactiveMode:
            self.printH1("Configure Grafana")
            if self.getParam("grafana_action") == "none":
                print_formatted_text("The Grafana operator package is not available in any catalogs on the target cluster, the installation of Grafana will be disabled")
            else:
                self.promptForString("Install namespace", "grafana_v5_namespace", default="grafana5")
                self.promptForString("Grafana storage size", "grafana_instance_storage_size", default="10Gi")

    def configMongoDb(self) -> None:
        self.printH1("Configure MongoDb")
        self.promptForString("Install namespace", "mongodb_namespace", default="mongoce")

    def configSpecialCharacters(self):
        self.printH1("Configure special characters for userID and username")
        self.yesOrNo("Do you want to allow special characters for user IDs and usernames?", "mas_special_characters")

    def configCP4D(self):
        if self.getParam("mas_catalog_version") in ["v9-240625-amd64", "v9-240730-amd64", "v9-240827-amd64", "v9-241003-amd64"]:
            logger.debug(f"Using automatic CP4D product version: {self.getParam('cpd_product_version')}")
            self.setParam("cpd_product_version", "4.8.0")
        elif self.getParam("cpd_product_version") == "":
            if self.noConfirm:
                self.fatalError("Cloud Pak for Data version must be set manually, but --no-confirm flag has been set")
            self.printDescription([
                f"Unknown catalog {self.getParam('mas_catalog_version')}, please manually select the version of Cloud Pak for Data to use"
            ])
            self.promptForString("Cloud Pak for Data product version", "cpd_product_version", default="4.8.0")
            logger.debug(f"Using user-provided (prompt) CP4D product version: {self.getParam('cpd_product_version')}")
        else:
            logger.debug(f"Using user-provided (flags) CP4D product version: {self.getParam('cpd_product_version')}")
        self.deployCP4D = True

    def configSSOProperties(self):
        self.printH1("Single Sign-On (SSO)")
        self.printDescription([
            "Many aspects of Maximo Application Suite's Single Sign-On (SSO) can be customized:",
            " - Idle session automatic logout timer",
            " - Session, access token, and refresh token timeouts",
            " - Default identity provider (IDP), and seamless login",
            " - Brower cookie properties"
        ])
        if self.yesOrNo("Configure SSO properties"):
            self.promptForInt("Idle session logout timer (seconds)", "idle_timeout")
            self.promptForString("Session timeout (e.g. '12h' for 12 hours)", "idp_session_timeout", validator=TimeoutFormatValidator())
            self.promptForString("Access token timeout (e.g. '30m' for 30 minutes)", "access_token_timeout", validator=TimeoutFormatValidator())
            self.promptForString("Refresh token timeout (e.g. '12h' for 12 hours)", "refresh_token_timeout", validator=TimeoutFormatValidator())
            self.promptForString("Default Identity Provider", "default_idp")

            self.promptForString("SSO cookie name", "sso_cookie_name")
            self.yesOrNo("Enable seamless login", "seamless_login")
            self.yesOrNo("Allow default SSO cookie name", "allow_default_sso_cookie_name")
            self.yesOrNo("Use only custom cookie name", "use_only_custom_cookie_name")
            self.yesOrNo("Disable LDAP cookie", "disable_ldap_cookie")
            self.yesOrNo("Allow custom cache key", "allow_custom_cache_key")

    def configGuidedTour(self):
        self.printH1("Enable Guided Tour")
        self.printDescription([
            "By default, Maximo Application Suite is configured with guided tour, you can disable this if it not required"
        ])
        if not self.yesOrNo("Enable Guided Tour"):
            self.setParam("mas_enable_walkme","false")

    def configMAS(self):
        self.printH1("Configure MAS Instance")
        self.printDescription([
            "Instance ID restrictions:",
            " - Must be 3-12 characters long",
            " - Must only use lowercase letters, numbers, and hypen (-) symbol",
            " - Must start with a lowercase letter",
            " - Must end with a lowercase letter or a number"
        ])
        self.promptForString("Instance ID", "mas_instance_id", validator=InstanceIDFormatValidator())
        self.printDescription([
            "",
            "Workspace ID restrictions:",
            " - Must be 3-12 characters long",
            " - Must only use lowercase letters and numbers",
            " - Must start with a lowercase letter"
        ])
        self.promptForString("Workspace ID", "mas_workspace_id", validator=WorkspaceIDFormatValidator())
        self.printDescription([
            "",
            "Workspace display name restrictions:",
            " - Must be 3-300 characters long"
        ])
        self.promptForString("Workspace name", "mas_workspace_name", validator=WorkspaceNameFormatValidator())

        self.configOperationMode()
        self.configCATrust()
        self.configDNSAndCerts()
        self.configSSOProperties()
        self.configSpecialCharacters()
        self.configGuidedTour()

    def configCATrust(self) -> None:
        self.printH1("Certificate Authority Trust")
        self.printDescription([
            "By default, Maximo Application Suite is configured to trust well-known certificate authoritories, you can disable this so that it will only trust the CAs that you explicitly define"
        ])
        self.yesOrNo("Trust default CAs", "mas_trust_default_cas")

    def configOperationMode(self):
        self.printH1("Configure Operational Mode")
        self.printDescription([
            "Maximo Application Suite can be installed in a non-production mode for internal development and testing, this setting cannot be changed after installation:",
            " - All applications, add-ons, and solutions have 0 (zero) installation AppPoints in non-production installations.",
            " - These specifications are also visible in the metrics that are shared with IBM and in the product UI.",
            "",
            "  1. Production",
            "  2. Non-Production"
        ])
        self.operationalMode = self.promptForInt("Operational Mode", default=1)

    def configAnnotations(self):
        if self.operationalMode == 2:
            self.setParam("mas_annotations", "mas.ibm.com/operationalMode=nonproduction")

    def configSNO(self):
        if self.isSNO():
            self.setParam("mongodb_replicas", "1")
            self.setParam("mongodb_cpu_requests", "500m")
            self.setParam("mas_app_settings_aio_flag", "false")

    def configDNSAndCerts(self):
        self.printH1("Cluster Ingress Secret Override")
        self.printDescription([
            "In most OpenShift clusters the installation is able to automatically locate the default ingress certificate, however in some configurations it is necessary to manually configure the name of the secret",
            "Unless you see an error during the ocp-verify stage indicating that the secret can not be determined you do not need to set this and can leave the response empty"
        ])
        self.promptForString("Cluster ingress certificate secret name", "ocp_ingress_tls_secret_name", default="")

        self.printH1("Configure Domain & Certificate Management")
        configureDomainAndCertMgmt = self.yesOrNo('Configure domain & certificate management')
        if configureDomainAndCertMgmt:
            configureDomain = self.yesOrNo('Configure custom domain')
            if configureDomain:
                self.promptForString("MAS top-level domain", "mas_domain")
                self.printDescription([
                    "",
                    "DNS Integrations:",
                    "  1. Cloudflare",
                    "  2. IBM Cloud Internet Services",
                    "  3. AWS Route 53",
                    "  4. None (I will set up DNS myself)"
                ])

                dnsProvider = self.promptForInt("DNS Provider")

                if dnsProvider == 1:
                    self.configDNSAndCertsCloudflare()
                elif dnsProvider == 2:
                    self.configDNSAndCertsCIS()
                elif dnsProvider == 3:
                    self.configDNSAndCertsRoute53()
                elif dnsProvider == 4:
                    # Use MAS default self-signed cluster issuer with a custom domain
                    self.setParam("dns_provider", "")
                    self.setParam("mas_cluster_issuer", "")
            else:
                # Use MAS default self-signed cluster issuer with the default domain
                self.setParam("dns_provider", "")
                self.setParam("mas_domain", "")
                self.setParam("mas_cluster_issuer", "")
            self.manualCerts = self.yesOrNo("Configure manual certificates")
            self.setParam("mas_manual_cert_mgmt", self.manualCerts)
            if self.getParam("mas_manual_cert_mgmt"):
                self.manualCertsDir = self.promptForDir("Enter the path containing the manual certificates", mustExist=True)
                self.setParam("mas_manual_cert_dir", self.manualCertsDir)

    def configDNSAndCertsCloudflare(self):
        # User has chosen to set up DNS integration with Cloudflare
        self.setParam("dns_provider", "cloudflare")
        self.promptForString("Cloudflare e-mail", "cloudflare_email")
        self.promptForString("Cloudflare API token", "cloudflare_apitoken")
        self.promptForString("Cloudflare zone", "cloudflare_zone")
        self.promptForString("Cloudflare subdomain", "cloudflare_subdomain")

        self.printDescription([
            "Certificate Issuer:",
            "  1. LetsEncrypt (Production)",
            "  2. LetsEncrypt (Staging)",
            "  3. Self-Signed"
        ])
        certIssuer = self.promptForInt("Certificate issuer")
        certIssuerOptions = [
            f"{self.getParam('mas_instance_id')}-cloudflare-le-prod",
            f"{self.getParam('mas_instance_id')}-cloudflare-le-stg",
            ""
        ]
        self.setParam("mas_cluster_issuer", certIssuerOptions[certIssuer-1])

    def configDNSAndCertsCIS(self):
        self.setParam("dns_provider", "cis")
        self.promptForString("CIS e-mail", "cis_email")
        self.promptForString("CIS API token", "cis_apikey")
        self.promptForString("CIS CRN", "cis_crn")
        self.promptForString("CIS subdomain", "cis_subdomain")

        self.printDescription([
            "Certificate Issuer:",
            "  1. LetsEncrypt (Production)",
            "  2. LetsEncrypt (Staging)",
            "  3. Self-Signed"
        ])
        certIssuer = self.promptForInt("Certificate issuer")
        certIssuerOptions = [
            f"{self.getParam('mas_instance_id')}-cis-le-prod",
            f"{self.getParam('mas_instance_id')}-cis-le-stg",
            ""
        ]
        self.setParam("mas_cluster_issuer", certIssuerOptions[certIssuer-1])

    def configDNSAndCertsRoute53(self):
        self.setParam("dns_provider", "route53")
        self.printDescription([
            "Provide your AWS account access key ID & secret access key",
            "This will be used to authenticate into the AWS account where your AWS Route 53 hosted zone instance is located",
            ""
        ])
        self.promptForString("AWS Access Key ID", "aws_access_key_id", isPassword=True)
        self.promptForString("AWS Secret Access Key", "aws_secret_access_key", isPassword=True)

        self.printDescription([
            "Provide your AWS Route 53 hosted zone instance details",
            "This information will be used to create webhook resources between your cluster and your AWS Route 53 instance (cluster issuer and cname records)",
            "in order for it to be able to resolve DNS entries for all the subdomains created for your Maximo Application Suite instance",
            "",
            "Therefore, the AWS Route 53 subdomain + the AWS Route 53 hosted zone name defined, when combined, needs to match with the chosen MAS Top Level domain, otherwise the DNS records won't be able to get resolved"
        ])
        self.promptForString("AWS Route 53 hosted zone name", "route53_hosted_zone_name")
        self.promptForString("AWS Route 53 hosted zone region", "route53_hosted_zone_region")
        self.promptForString("AWS Route 53 subdomain", "route53_subdomain")
        self.promptForString("AWS Route 53 e-mail", "route53_email")

        self.setParam("mas_cluster_issuer", f"{self.getParam('mas_instance_id')}-route53-le-prod")

    def configApps(self):
        self.printH1("Application Selection")
        self.installIoT = self.yesOrNo("Install IoT")

        if self.installIoT:
            self.configAppChannel("iot")
            self.installMonitor = self.yesOrNo("Install Monitor")
        else:
            self.installMonitor = False

        if self.installMonitor:
            self.configAppChannel("monitor")

        self.installManage = self.yesOrNo("Install Manage")

        if self.installManage:
            self.configAppChannel("manage")

        # Predict for MAS 8.10 is effectively unsupported now, because it has not shipped support for Cloud Pak for Data 4.8 as of June 2023 catalog update
        if self.installIoT and self.installManage and self.getParam("mas_channel") != "8.10.x":
            self.installPredict = self.yesOrNo("Install Predict")
        else:
            self.installPredict = False

        if self.installPredict:
            self.configAppChannel("predict")

        # Assist is only installable on MAS 9.0.x due to withdrawal of support for Watson Discovery in our managed dependency stack and the inability of Assist 8.x to support this
        if not self.getParam("mas_channel").startswith("8."):
            self.installAssist = self.yesOrNo("Install Assist")
            if self.installAssist:
                self.configAppChannel("assist")
        else:
            self.installAssist = False

        self.installOptimizer = self.yesOrNo("Install Optimizer")
        if self.installOptimizer:
            self.configAppChannel("optimizer")

        self.installInspection = self.yesOrNo("Install Visual Inspection")
        if self.installInspection:
            self.configAppChannel("visualinspection")

    def configAppChannel(self, appId):
        versions = self.getCompatibleVersions(self.params["mas_channel"], appId)
        if len(versions) == 0:
            self.params[f"mas_app_channel_{appId}"] = prompt(HTML('<Yellow>Custom channel</Yellow> '))
        else:
            self.params[f"mas_app_channel_{appId}"] = versions[0]

    def configStorageClasses(self):
        self.printH1("Configure Storage Class Usage")
        self.printDescription([
            "Maximo Application Suite and it's dependencies require storage classes that support ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes:",
            "  - ReadWriteOnce volumes can be mounted as read-write by multiple pods on a single node.",
            "  - ReadWriteMany volumes can be mounted as read-write by multiple pods across many nodes.",
            ""
        ])
        # 1. ROKS
        if getStorageClass(self.dynamicClient, "ibmc-file-gold-gid") is not None:
            print_formatted_text(HTML("<MediumSeaGreen>Storage provider auto-detected: IBMCloud ROKS</MediumSeaGreen>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteOnce): ibmc-block-gold</LightSlateGrey>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteMany): ibmc-file-gold-gid</LightSlateGrey>"))
            self.storageClassProvider = "ibmc"
            self.params["storage_class_rwo"] = "ibmc-block-gold"
            self.params["storage_class_rwx"] = "ibmc-file-gold-gid"
        # 2. OCS
        elif getStorageClass(self.dynamicClient, "ocs-storagecluster-cephfs") is not None:
            print_formatted_text(HTML("<MediumSeaGreen>Storage provider auto-detected: OpenShift Container Storage</MediumSeaGreen>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteOnce): ocs-storagecluster-ceph-rbd</LightSlateGrey>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteMany): ocs-storagecluster-cephfs</LightSlateGrey>"))
            self.storageClassProvider = "ocs"
            self.params["storage_class_rwo"] = "ocs-storagecluster-ceph-rbd"
            self.params["storage_class_rwx"] = "ocs-storagecluster-cephfs"
        # 3. NFS Client
        elif getStorageClass(self.dynamicClient, "nfs-client") is not None:
            print_formatted_text(HTML("<MediumSeaGreen>Storage provider auto-detected: NFS Client</MediumSeaGreen>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteOnce): nfs-client</LightSlateGrey>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteMany): nfs-client</LightSlateGrey>"))
            self.storageClassProvider = "nfs"
            self.params["storage_class_rwo"] = "nfs-client"
            self.params["storage_class_rwx"] = "nfs-client"
        # 4. Azure
        elif getStorageClass(self.dynamicClient, "managed-premium") is not None:
            print_formatted_text(HTML("<MediumSeaGreen>Storage provider auto-detected: Azure Managed</MediumSeaGreen>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteOnce): managed-premium</LightSlateGrey>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteMany): azurefiles-premium</LightSlateGrey>"))
            self.storageClassProvider = "azure"
            self.params["storage_class_rwo"] = "managed-premium"
            self.params["storage_class_rwx"] = "azurefiles-premium"
        # 5. AWS
        elif getStorageClass(self.dynamicClient, "gp2") is not None:
            print_formatted_text(HTML("<MediumSeaGreen>Storage provider auto-detected: AWS gp2</MediumSeaGreen>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteOnce): gp2</LightSlateGrey>"))
            print_formatted_text(HTML("<LightSlateGrey>  - Storage class (ReadWriteMany): efs</LightSlateGrey>"))
            self.storageClassProvider = "aws"
            self.params["storage_class_rwo"] = "gp2"
            self.params["storage_class_rwx"] = "efs"

        overrideStorageClasses = False
        if "storage_class_rwx" in self.params and self.params["storage_class_rwx"] != "":
            overrideStorageClasses = not self.yesOrNo("Use the auto-detected storage classes")

        if "storage_class_rwx" not in self.params or self.params["storage_class_rwx"] == "" or overrideStorageClasses:
            self.storageClassProvider = "custom"

            self.printDescription([
                "Select the ReadWriteOnce and ReadWriteMany storage classes to use from the list below:",
                "Enter 'none' for the ReadWriteMany storage class if you do not have a suitable class available in the cluster, however this will limit what can be installed"
            ])
            for storageClass in getStorageClasses(self.dynamicClient):
                print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))

            self.params["storage_class_rwo"] = prompt(HTML('<Yellow>ReadWriteOnce (RWO) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)
            self.params["storage_class_rwx"] = prompt(HTML('<Yellow>ReadWriteMany (RWX) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)

        # Configure storage class for pipeline PVC
        # We prefer to use ReadWriteMany, but we can cope with ReadWriteOnce if necessary
        if self.isSNO() or self.params["storage_class_rwx"] == "none":
            self.pipelineStorageClass = self.getParam("storage_class_rwo")
            self.pipelineStorageAccessMode = "ReadWriteOnce"
        else:
            self.pipelineStorageClass = self.getParam("storage_class_rwx")
            self.pipelineStorageAccessMode = "ReadWriteMany"

    def setIoTStorageClasses(self) -> None:
        if self.installIoT:
            self.setParam("mas_app_settings_iot_fpl_pvc_storage_class",  self.getParam("storage_class_rwo"))
            self.setParam("mas_app_settings_iot_mqttbroker_pvc_storage_class",  self.getParam("storage_class_rwo"))

    def optimizerSettings(self) -> None:
        if self.installOptimizer:
            self.printH1("Configure Maximo Optimizer")
            self.printDescription(["Customize your Optimizer installation, 'full' and 'limited' install plans are available, refer to the product documentation for more information"])

            self.promptForString("Plan [full/limited]", "mas_app_plan_optimizer", default="full", validator=OptimizerInstallPlanValidator())

    def predictSettings(self) -> None:
        if self.installPredict:
            self.printH1("Configure Maximo Predict")
            self.printDescription([
                "Predict application supports integration with IBM SPSS and Watson Openscale which are optional services installed on top of IBM Cloud Pak for Data",
                "Unless requested these will not be installed"
            ])
            self.configCP4D()
            self.yesOrNo("Install IBM SPSS Statistics", "cpd_install_spss")
            self.yesOrNo("Install Watson OpenScale", "cpd_install_openscale")

    def assistSettings(self) -> None:
        if self.installAssist:
            self.printH1("Configure Maximo Assist")
            self.printDescription([
                "Assist requires access to Cloud Object Storage (COS), this install supports automatic setup using either IBMCloud COS or in-cluster COS via OpenShift Container Storage/OpenShift Data Foundation (OCS/ODF)"
            ])
            self.configCP4D()
            self.promptForString("COS Provider [ibm/ocs]", "cos_type")
            if self.getParam("cos_type") == "ibm":
                self.promptForString("IBM Cloud API Key", "ibmcloud_apikey", isPassword=True)
                self.promptForString("IBM Cloud Resource Group", "cos_resourcegroup")

    def interactiveMode(self) -> None:
        # Interactive mode
        self.interactiveMode = True

        # Catalog
        self.configCatalog()
        if not self.devMode:
            self.validateCatalogSource()
            self.licensePrompt()

        # SNO & Storage Classes
        self.configSNO()
        self.configStorageClasses()

        # Licensing (SLS and DRO)
        self.configSLS()
        self.configICRCredentials()

        # MAS Core
        self.configCertManager()
        self.configMAS()

        # MAS Applications
        self.configApps()
        self.validateInternalRegistryAvailable()
        # Note: manageSettings(), predictSettings(), or assistSettings() functions can trigger configCP4D()
        self.manageSettings()
        self.optimizerSettings()
        self.predictSettings()
        self.assistSettings()

        # Dependencies
        self.configMongoDb()  # Will only do anything if IoT or Manage have been selected for install
        self.configDb2()
        self.configKafka()  # Will only do anything if IoT has been selected for install

        self.configGrafana()
        self.configTurbonomic()

        # TODO: Support ECK integration via the interactive install mode
        # TODO: Support MAS superuser username/password via the interactive install mode

    def nonInteractiveMode(self) -> None:
        # Non-interactive mode
        self.interactiveMode = False

        # Set defaults
        self.storageClassProvider="custom"
        self.installAssist = False
        self.installIoT = False
        self.installMonitor = False
        self.installManage = False
        self.installPredict = False
        self.installInspection = False
        self.installOptimizer = False
        self.deployCP4D = False
        self.db2SetAffinity = False
        self.db2SetTolerations = False

        self.approvals = {
            "approval_core": {"id": "suite-verify"},  # After Core Platform verification has completed
            "approval_assist": {"id": "app-cfg-assist"},  # After Assist workspace has been configured
            "approval_iot": {"id": "app-cfg-iot"},  # After IoT workspace has been configured
            "approval_manage": {"id": "app-cfg-manage"},  # After Manage workspace has been configured
            "approval_monitor": {"id": "app-cfg-monitor"},  # After Monitor workspace has been configured
            "approval_optimizer": {"id": "app-cfg-optimizer"},  # After Optimizer workspace has been configured
            "approval_predict": {"id": "app-cfg-predict"},  # After Predict workspace has been configured
            "approval_visualinspection": {"id": "app-cfg-visualinspection"}  # After Visual Inspection workspace has been configured
        }

        self.configGrafana()

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
            # MAS
            "mas_catalog_digest",
            "mas_superuser_username",
            "mas_superuser_password",
            "mas_trust_default_cas",
            "mas_app_settings_server_bundles_size",
            "mas_app_settings_default_jms",
            "mas_app_settings_persistent_volumes_flag",
            "mas_appws_bindings_jdbc_manage",
            "mas_app_settings_demodata",
            "mas_appws_components",
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
            "ocp_ingress_tls_secret_name",
            # DRO
            "dro_namespace",
            # MongoDb
            "mongodb_namespace",
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
            "cpd_install_openscale",
            "cpd_install_spss",
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
            # Special chars
            "mas_special_characters"
        ]

        for key, value in vars(self.args).items():
            # These fields we just pass straight through to the parameters and fail if they are not set
            if key in requiredParams:
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.setParam(key, value)

            # These fields we just pass straight through to the parameters
            elif key in optionalParams:
                if value is not None:
                    self.setParam(key, value)

            elif key == "kafka_provider":
                if value is not None:
                    self.setParam("kafka_provider", value)
                    self.setParam("kafka_action_system", "install")

            elif key == "kafka_username":
                if value is not None:
                    self.setParam("kafka_user_name", value)
                    self.setParam("aws_kafka_user_name", value)

            elif key == "kafka_password":
                if value is not None:
                    self.setParam("kafka_user_password", value)
                    self.setParam("aws_kafka_user_password", value)

            elif key == "non_prod":
                if not value:
                    self.operationalMode = 1
                else:
                    self.operationalMode = 2
                    self.setParam("mas_annotations", "mas.ibm.com/operationalMode=nonproduction")

            elif key == "additional_configs":
                self.localConfigDir = value

            elif key == "pod_templates":
                # For the named configurations we will convert into the path
                if value in ["best-effort", "guaranteed"]:
                    self.setParam("mas_pod_templates_dir", path.join(self.templatesDir, "pod-templates", value))
                else:
                    self.setParam("mas_pod_templates_dir", value)

            elif key == "assist_channel":
                if value is not None:
                    self.setParam("mas_app_channel_assist", value)
                    self.installAssist = True
            elif key == "iot_channel":
                if value is not None:
                    self.setParam("mas_app_channel_iot", value)
                    self.installIoT = True
            elif key == "monitor_channel":
                if value is not None:
                    self.setParam("mas_app_channel_monitor", value)
                    self.installMonitor = True
            elif key == "manage_channel":
                if value is not None:
                    self.setParam("mas_app_channel_manage", value)
                    self.installManage = True
            elif key == "predict_channel":
                if value is not None:
                    self.setParam("mas_app_channel_predict", value)
                    self.installPredict = True
                    self.deployCP4D = True
            elif key == "visualinspection_channel":
                if value is not None:
                    self.setParam("mas_app_channel_visualinspection", value)
                    self.installInspection = True
            elif key == "optimizer_channel":
                if value is not None:
                    self.setParam("mas_app_channel_optimizer", value)
                    self.installOptimizer = True
            elif key == "optimizer_plan":
                if value is not None:
                    self.setParam("mas_app_plan_optimizer", value)

            # Manage advanced settings that need extra processing
            elif key == "mas_app_settings_server_bundle_size":
                if value is not None:
                    self.setParam(key, value)
                    if value in ["jms", "snojms"]:
                        self.setParam("mas_app_settings_persistent_volumes_flag", "true")

            # These settings are used by the CLI rather than passed to the PipelineRun
            elif key == "storage_accessmode":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageAccessMode = value
            elif key == "storage_pipeline":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageClass = value
            elif key == "license_file":
                    if value is None:
                        self.fatalError(f"{key} must be set")
                    self.slsLicenseFileLocal = value

            elif key.startswith("approval_"):
                if key not in self.approvals:
                    raise KeyError(f"{key} is not a supported approval workflow ID: {self.approvals.keys()}")

                if value != "":
                    valueParts = value.split(":")
                    if len(valueParts) != 4:
                        self.fatalError(f"Unsupported format for {key} ({value}).  Expected APPROVAL_KEY:MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE")
                    else:
                        try:
                            self.approvals[key]["approvalKey"] = valueParts[0]
                            self.approvals[key]["maxRetries"] = int(valueParts[1])
                            self.approvals[key]["retryDelay"] = int(valueParts[2])
                            self.approvals[key]["ignoreFailure"] = bool(valueParts[3])
                        except:
                            self.fatalError(f"Unsupported format for {key} ({value}).  Expected string:int:int:boolean")

            # Arguments that we don't need to do anything with
            elif key in ["accept_license", "dev_mode", "skip_pre_check", "skip_grafana_install", "no_confirm", "no_wait_for_pvc", "help"]:
                pass

            elif key == "manual_certificates":
                if value is not None:
                    self.setParam("mas_manual_cert_mgmt", True)
                    self.setParam("mas_manual_cert_dir", value)
                else:
                    self.setParam("mas_manual_cert_mgmt", False)

            # Fail if there's any arguments we don't know how to handle
            else:
                print(f"Unknown option: {key} {value}")
                self.fatalError(f"Unknown option: {key} {value}")

        # Once we've processed the inputs, we should validate the catalog source & prompt to accept the license terms
        if not self.devMode:
            self.validateCatalogSource()
            self.licensePrompt()

    def install(self, argv):
        """
        Install MAS instance
        """
        args = installArgParser.parse_args(args=argv)

        # We use the presence of --mas-instance-id to determine whether
        # the CLI is being started in interactive mode or not
        instanceId = args.mas_instance_id

        # Properties for arguments that control the behavior of the CLI
        self.noConfirm = args.no_confirm
        self.waitForPVC = not args.no_wait_for_pvc
        self.licenseAccepted = args.accept_license
        self.devMode = args.dev_mode
        self.skipGrafanaInstall = args.skip_grafana_install

        self.approvals = {}

        # Store all args
        self.args = args

        # These flags work for setting params in both interactive and non-interactive modes
        if args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        self.installOptions = [
            {
                "#": 1,
                "catalog": "v9-241003-amd64",
                "release": "9.0.x",
                "core": "9.0.3",
                "assist": "9.0.2",
                "iot": "9.0.3",
                "manage": "9.0.3",
                "monitor": "9.0.3",
                "optimizer": "9.0.3",
                "predict": "9.0.2",
                "inspection": "9.0.3"
            },
            {
                "#": 2,
                "catalog": "v9-241003-amd64",
                "release": "8.11.x",
                "core": "8.11.15",
                "assist": "8.8.6",
                "iot": "8.8.13",
                "manage": "8.7.12",
                "monitor": "8.11.11",
                "optimizer": "8.5.9",
                "predict": "8.9.5",
                "inspection": "8.9.6"
            },
            {
                "#": 3,
                "catalog": "v9-241003-amd64",
                "release": "8.10.x",
                "core": "8.10.18",
                "assist": "8.7.7",
                "iot": "8.7.17",
                "manage": "8.6.18",
                "monitor": "8.10.14",
                "optimizer": "8.4.10",
                "predict": "8.8.3",
                "inspection": "8.8.4"
            },            
            {
                "#": 4,
                "catalog": "v9-240827-amd64",
                "release": "9.0.x",
                "core": "9.0.2",
                "assist": "9.0.2",
                "iot": "9.0.2",
                "manage": "9.0.2",
                "monitor": "9.0.2",
                "optimizer": "9.0.2",
                "predict": "9.0.1",
                "inspection": "9.0.2"
            },
            {
                "#": 5,
                "catalog": "v9-240827-amd64",
                "release": "8.11.x",
                "core": "8.11.14",
                "assist": "8.8.6",
                "iot": "8.8.12",
                "manage": "8.7.11",
                "monitor": "8.11.10",
                "optimizer": "8.5.8",
                "predict": "8.9.3",
                "inspection": "8.9.5"
            },
            {
                "#": 6,
                "catalog": "v9-240827-amd64",
                "release": "8.10.x",
                "core": "8.10.17",
                "assist": "8.7.7",
                "iot": "8.7.16",
                "manage": "8.6.17",
                "monitor": "8.10.13",
                "optimizer": "8.4.9",
                "predict": "8.8.3",
                "inspection": "8.8.4"
            },
            {
                "#": 7,
                "catalog": "v9-240730-amd64",
                "release": "9.0.x",
                "core": "9.0.1",
                "assist": "9.0.1",
                "iot": "9.0.1",
                "manage": "9.0.1",
                "monitor": "9.0.1",
                "optimizer": "9.0.1",
                "predict": "9.0.0",
                "inspection": "9.0.0"
            },
            {
                "#": 8,
                "catalog": "v9-240730-amd64",
                "release": "8.11.x",
                "core": "8.11.13",
                "assist": "8.8.5",
                "iot": "8.8.11",
                "manage": "8.7.10",
                "monitor": "8.11.9",
                "optimizer": "8.5.7",
                "predict": "8.9.3",
                "inspection": "8.9.4"
            },
            {
                "#": 9,
                "catalog": "v9-240730-amd64",
                "release": "8.10.x",
                "core": "8.10.16",
                "assist": "8.7.6",
                "iot": "8.7.15",
                "manage": "8.6.16",
                "monitor": "8.10.12",
                "optimizer": "8.4.8",
                "predict": "8.8.3",
                "inspection": "8.8.4"
            }
        ]

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available.  See log file for details</Red>"))
            exit(1)

        # Basic settings before the user provides any input
        self.configICR()
        self.configCertManager()
        self.deployCP4D = False

        # UDS install has not been supported since the January 2024 catalog update
        self.setParam("uds_action", "install-dro")

        # User must either provide the configuration via numerous command line arguments, or the interactive prompts
        if instanceId is None:
            self.interactiveMode()
        else:
            self.nonInteractiveMode()

        # After we've configured the basic inputs, we can calculate these ones
        self.setIoTStorageClasses()
        if self.deployCP4D:
            self.configCP4D()

        # The entitlement file for SLS is mounted as a secret in /workspace/entitlement
        entitlementFileBaseName = path.basename(self.slsLicenseFileLocal)
        self.setParam("sls_entitlement_file", f"/workspace/entitlement/{entitlementFileBaseName}")

        # Set up the secrets for additional configs, podtemplates and manual certificates
        self.additionalConfigs()
        self.podTemplates()
        self.manualCertificates()

        # Show a summary of the installation configuration
        self.printH1("Non-Interactive Install Command")
        self.printDescription([
            "Save and re-use the following script to re-run this install without needing to answer the interactive prompts again",
            "",
            self.buildCommand()
        ])

        # Based on the parameters set the annotations correctly
        self.configAnnotations()

        self.displayInstallSummary()

        if not self.noConfirm:
            print()
            self.printDescription([
                "Please carefully review your choices above, correcting mistakes now is much easier than after the install has begun"
            ])
            continueWithInstall = self.yesOrNo("Proceed with these settings")

        # Prepare the namespace and launch the installation pipeline
        if self.noConfirm or continueWithInstall:
            self.createTektonFileWithDigest()

            self.printH1("Launch Install")
            pipelinesNamespace = f"mas-{self.getParam('mas_instance_id')}-pipelines"

            if not self.noConfirm:
                self.printDescription(["If you are using storage classes that utilize 'WaitForFirstConsumer' binding mode choose 'No' at the prompt below"])
                wait = self.yesOrNo("Wait for PVCs to bind")
            else:
                wait = False

            with Halo(text='Validating OpenShift Pipelines installation', spinner=self.spinner) as h:
                installOpenShiftPipelines(self.dynamicClient)
                h.stop_and_persist(symbol=self.successIcon, text=f"OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("mas_instance_id"),
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                    waitForBind=wait
                )
                prepareInstallSecrets(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("mas_instance_id"),
                    slsLicenseFile=self.slsLicenseFileLocal,
                    additionalConfigs=self.additionalConfigsSecret,
                    podTemplates=self.podTemplatesSecret,
                    certs=self.certsSecret
                )

                self.setupApprovals(pipelinesNamespace)

                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text=f'Testing availability of MAS CLI image in cluster', spinner=self.spinner) as h:
                testCLI()
                h.stop_and_persist(symbol=self.successIcon, text=f"MAS CLI image deployment test completed")

            with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

            with Halo(text=f"Submitting PipelineRun for {self.getParam('mas_instance_id')} install", spinner=self.spinner) as h:
                pipelineURL = launchInstallPipeline(dynClient=self.dynamicClient, params=self.params)
                if pipelineURL is not None:
                    h.stop_and_persist(symbol=self.successIcon, text=f"PipelineRun for {self.getParam('mas_instance_id')} install submitted")
                    print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
                else:
                    h.stop_and_persist(symbol=self.failureIcon, text=f"Failed to submit PipelineRun for {self.getParam('mas_instance_id')} install, see log file for details")
                    print()

    def setupApprovals(self, namespace: str) -> None:
        """
        Ensure the supported approval configmaps are in the expected state for the start of the run:
         - not present (if approval is not required)
         - present with the chosen state field initialized to ""
        """
        for approval in self.approvals.values():
            if "approvalKey" in approval:
                # Enable this approval workload
                logger.debug(f"Approval workflow for {approval['id']} will be enabled during install ({approval['maxRetries']} / {approval['retryDelay']}s / {approval['approvalKey']} / {approval['ignoreFailure']})")
                self.initializeApprovalConfigMap(namespace, approval['id'], approval['approvalKey'], approval['maxRetries'], approval['retryDelay'], approval['ignoreFailure'])
            else:
                # Disable this approval workload
                logger.debug(f"Approval workflow for {approval['id']} will be disabled during install")
                self.initializeApprovalConfigMap(namespace, approval['id'])
