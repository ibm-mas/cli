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
from os import path, getenv
import re
import calendar

from openshift.dynamic.exceptions import NotFoundError

from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.completion import WordCompleter

from tabulate import tabulate

from halo import Halo

from ..cli import BaseApp
from ..gencfg import ConfigGeneratorMixin
from .argBuilder import installArgBuilderMixin
from .argParser import installArgParser
from .settings import InstallSettingsMixin
from .summarizer import InstallSummarizerMixin
from .params import requiredParams, optionalParams
from .catalogs import supportedCatalogs

from mas.cli.validators import (
    InstanceIDFormatValidator,
    WorkspaceIDFormatValidator,
    WorkspaceNameFormatValidator,
    TimeoutFormatValidator,
    StorageClassValidator,
    OptimizerInstallPlanValidator
)

from mas.devops.ocp import createNamespace, getStorageClasses
from mas.devops.mas import getCurrentCatalog, getDefaultStorageClasses
from mas.devops.sls import findSLSByNamespace
from mas.devops.data import getCatalog
from mas.devops.tekton import (
    installOpenShiftPipelines,
    updateTektonDefinitions,
    preparePipelinesNamespace,
    prepareInstallSecrets,
    testCLI,
    launchInstallPipeline
)

logger = logging.getLogger(__name__)


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> InstallApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< InstallApp.{func.__name__}")
        return result
    return wrapper


class InstallApp(BaseApp, InstallSettingsMixin, InstallSummarizerMixin, ConfigGeneratorMixin, installArgBuilderMixin):
    @logMethodCall
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

    @logMethodCall
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
                    "For more information refer to <Orange><u>https://www.ibm.com/docs/en/masv-and-l/continuous-delivery?topic=installing-enabling-openshift-internal-image-registry</u></Orange>"
                ])
            )

    @logMethodCall
    def licensePrompt(self):
        if not self.licenseAccepted:
            self.printH1("License Terms")
            self.printDescription([
                "To continue with the installation, you must accept the license terms:",
                self.licenses[self.getParam('mas_channel')]
            ])

            if self.noConfirm:
                self.fatalError("You must accept the license terms with --accept-license when using the --no-confirm flag")
            else:
                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

    @logMethodCall
    def configICR(self):
        if self.devMode:
            self.setParam("mas_icr_cp", getenv("MAS_ICR_CP", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local"))
            self.setParam("mas_icr_cpopen", getenv("MAS_ICR_CPOPEN", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen"))
            self.setParam("sls_icr_cpopen", getenv("SLS_ICR_CPOPEN", "docker-na-public.artifactory.swg-devops.com/wiotp-docker-local/cpopen"))
        else:
            self.setParam("mas_icr_cp", getenv("MAS_ICR_CP", "cp.icr.io/cp"))
            self.setParam("mas_icr_cpopen", getenv("MAS_ICR_CPOPEN", "icr.io/cpopen"))
            self.setParam("sls_icr_cpopen", getenv("SLS_ICR_CPOPEN", "icr.io/cpopen"))

    @logMethodCall
    def configICRCredentials(self):
        self.printH1("Configure IBM Container Registry")
        self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)
        if self.devMode:
            self.promptForString("Artifactory username", "artifactory_username")
            self.promptForString("Artifactory token", "artifactory_token", isPassword=True)

    @logMethodCall
    def configCertManager(self):
        # Only install of Red Hat Cert-Manager has been supported since the January 2025 catalog update
        self.setParam("cert_manager_provider", "redhat")
        self.setParam("cert_manager_action", "install")

    def formatCatalog(self, name: str) -> str:
        # Convert "v9-241107-amd64" into "November 2024 Update (v9-241107-amd64)"
        date = name.split("-")[1]
        month = int(date[2:4])
        monthName = calendar.month_name[month]
        year = date[:2]
        return f" - {monthName} 20{year} Update\n   <Orange><u>https://ibm-mas.github.io/cli/catalogs/{name}</u></Orange>"

    @logMethodCall
    def processCatalogChoice(self) -> list:
        self.catalogDigest = self.chosenCatalog["catalog_digest"]
        self.catalogMongoDbVersion = self.chosenCatalog["mongo_extras_version_default"]
        if self.architecture != "s390x":
            self.catalogCp4dVersion = self.chosenCatalog["cpd_product_version_default"]

            applications = {
                "Core": "mas_core_version",
                "Manage": "mas_manage_version",
                "IoT": "mas_iot_version",
                "Monitor": "mas_monitor_version",
                "Assist": "mas_assist_version",
                "Optimizer": "mas_optimizer_version",
                "Predict": "mas_predict_version",
                "Inspection": "mas_visualinspection_version",
            }
        else:
            applications = {
                "Core": "mas_core_version",
                "Manage": "mas_manage_version",
            }

        self.catalogReleases = {}
        self.catalogTable = []

        # Dynamically fetch the channels from the chosen catalog
        # based on mas core
        for channel in self.chosenCatalog["mas_core_version"]:
            # {"9.1-feature": "9.1.x-feature"}
            self.catalogReleases.update({channel.replace('.x', ''): channel})

        # Generate catalogTable
        for application, key in applications.items():
            # Add 9.1-feature channel based off 9.0 to those apps that have not onboarded yet
            tempChosenCatalog = self.chosenCatalog[key].copy()
            if '9.1.x-feature' not in tempChosenCatalog:
                tempChosenCatalog.update({"9.1.x-feature": tempChosenCatalog["9.0.x"]})

            self.catalogTable.append({"": application} | {key.replace(".x", ""): value for key, value in sorted(tempChosenCatalog.items(), reverse=True)})

        if self.architecture == "s390x":
            summary = [
                "",
                "<u>Catalog Details</u>",
                f"Catalog Image:         icr.io/cpopen/ibm-maximo-operator-catalog:{self.getParam('mas_catalog_version')}",
                f"Catalog Digest:        {self.catalogDigest}",
                f"MAS Releases:          {', '.join(sorted(self.catalogReleases, reverse=True))}",
                f"MongoDb:               {self.catalogMongoDbVersion}",
            ]
        else:
            summary = [
                "",
                "<u>Catalog Details</u>",
                f"Catalog Image:         icr.io/cpopen/ibm-maximo-operator-catalog:{self.getParam('mas_catalog_version')}",
                f"Catalog Digest:        {self.catalogDigest}",
                f"MAS Releases:          {', '.join(sorted(self.catalogReleases, reverse=True))}",
                f"Cloud Pak for Data:    {self.catalogCp4dVersion}",
                f"MongoDb:               {self.catalogMongoDbVersion}",
            ]

        return summary

    @logMethodCall
    def configCatalog(self):
        self.printH1("IBM Maximo Operator Catalog Selection")
        if self.devMode:
            self.promptForString("Select catalog source", "mas_catalog_version", default="v9-master-amd64")
            self.promptForString("Select channel", "mas_channel", default="9.1.x-dev")
        else:
            catalogInfo = getCurrentCatalog(self.dynamicClient)

            if catalogInfo is None:
                self.printDescription([
                    "The catalog you choose dictates the version of everything that is installed, with Maximo Application Suite this is the only version you need to remember; all other versions are determined by this choice.",
                    "Older catalogs can still be used, but we recommend using an older version of the CLI that aligns with the release date of the catalog.",
                    " - Learn more: <Orange><u>https://ibm-mas.github.io/cli/catalogs/</u></Orange>",
                    ""
                ])
                print("Supported Catalogs:")
                for catalog in self.catalogOptions:
                    catalogString = self.formatCatalog(catalog)
                    print_formatted_text(HTML(f"{catalogString}"))
                print()

                catalogCompleter = WordCompleter(self.catalogOptions)
                catalogSelection = self.promptForString("Select catalog", completer=catalogCompleter)
                self.setParam("mas_catalog_version", catalogSelection)
            else:
                self.printDescription([
                    f"The IBM Maximo Operator Catalog is already installed in this cluster ({catalogInfo['catalogId']}).  If you wish to install MAS using a newer version of the catalog please first update the catalog using mas update."
                ])
                self.setParam("mas_catalog_version", catalogInfo["catalogId"])

            self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))
            catalogSummary = self.processCatalogChoice()
            self.printDescription(catalogSummary)
            self.printDescription([
                "",
                "Two types of release are available:",
                " - GA releases of Maximo Application Suite are supported under IBM's standard 3+1+3 support lifecycle policy.",
                " - 'Feature' releases allow early access to new features for evaluation in non-production environments and are only supported through to the next GA release.",
                ""
            ])

            print(tabulate(self.catalogTable, headers="keys", tablefmt="simple_grid"))

            releaseCompleter = WordCompleter(sorted(self.catalogReleases, reverse=True))
            releaseSelection = self.promptForString("Select release", completer=releaseCompleter)

            self.setParam("mas_channel", self.catalogReleases[releaseSelection])

    @logMethodCall
    def configSLS(self) -> None:
        self.printH1("Configure AppPoint Licensing")
        self.printDescription(
            [
                "By default the MAS instance will be configured to use a cluster-shared License, this provides a shared pool of AppPoints available to all MAS instances on the cluster.",
                "",
            ]
        )

        self.slsMode = 1
        self.slsLicenseFileLocal = None

        if self.showAdvancedOptions:
            self.printDescription(
                [
                    "Alternatively you may choose to install using a dedicated license only available to this MAS instance.",
                    "  1. Install MAS with Cluster-Shared License (AppPoints)",
                    "  2. Install MAS with Dedicated License (AppPoints)",
                ]
            )
            self.slsMode = self.promptForInt("SLS Mode", default=1)

            if self.slsMode not in [1, 2]:
                self.fatalError(f"Invalid selection: {self.slsMode}")

        if not (self.slsMode == 2 and not self.getParam("sls_namespace")):
            sls_namespace = "ibm-sls" if self.slsMode == 1 else self.getParam("sls_namespace")
            if findSLSByNamespace(sls_namespace, dynClient=self.dynamicClient):
                print_formatted_text(HTML(f"<MediumSeaGreen>SLS auto-detected: {sls_namespace}</MediumSeaGreen>"))
                print()
                if not self.yesOrNo("Upload/Replace the license file"):
                    self.setParam("sls_action", "gencfg")
                    return

        self.slsLicenseFileLocal = self.promptForFile("License file", mustExist=True, envVar="SLS_LICENSE_FILE_LOCAL")
        self.setParam("sls_action", "install")

    @logMethodCall
    def configDRO(self) -> None:
        self.promptForString("Contact e-mail address", "uds_contact_email")
        self.promptForString("Contact first name", "uds_contact_firstname")
        self.promptForString("Contact last name", "uds_contact_lastname")

        if self.showAdvancedOptions:
            self.promptForString("IBM Data Reporter Operator (DRO) Namespace", "dro_namespace", default="redhat-marketplace")

    @logMethodCall
    def selectLocalConfigDir(self) -> None:
        if self.localConfigDir is None:
            # You need to tell us where the configuration file can be found
            self.localConfigDir = self.promptForDir("Select Local configuration directory")

    @logMethodCall
    def configGrafana(self) -> None:
        if self.architecture == "s390x":
            # We are not supporting Grafana on s390x at the moment
            self.setParam("grafana_action", "none")
        else:
            try:
                packagemanifestAPI = self.dynamicClient.resources.get(api_version="packages.operators.coreos.com/v1", kind="PackageManifest")
                packagemanifestAPI.get(name="grafana-operator", namespace="openshift-marketplace")
                if self.skipGrafanaInstall:
                    self.setParam("grafana_action", "none")
                else:
                    self.setParam("grafana_action", "install")
            except NotFoundError:
                self.setParam("grafana_action", "none")

            if self.interactiveMode and self.showAdvancedOptions:
                self.printH1("Configure Grafana")
                if self.getParam("grafana_action") == "none":
                    print_formatted_text("The Grafana operator package is not available in any catalogs on the target cluster, the installation of Grafana will be disabled")
                else:
                    self.promptForString("Install namespace", "grafana_v5_namespace", default="grafana5")
                    self.promptForString("Grafana storage size", "grafana_instance_storage_size", default="10Gi")

    @logMethodCall
    def configSpecialCharacters(self):
        if self.showAdvancedOptions:
            self.printH1("Configure special characters for userID and username")
            self.printDescription([
                "By default Maximo Application Suite will not allow special characters in usernames and userIDs, and this is the recommended setting.  However, legacy Maximo products allowed this, so for maximum compatibilty when migrating from EAM 7 you can choose to enable this support."
            ])
            self.yesOrNo("Allow special characters for user IDs and usernames", "mas_special_characters")

    @logMethodCall
    def configCP4D(self):
        if self.getParam("mas_catalog_version") in self.catalogOptions:
            # Note: this will override any version provided by the user (which is intentional!)
            logger.debug(f"Using automatic CP4D product version: {self.getParam('cpd_product_version')}")
            self.setParam("cpd_product_version", self.chosenCatalog["cpd_product_version_default"])
        elif self.getParam("cpd_product_version") == "":
            if self.noConfirm:
                self.fatalError("Cloud Pak for Data version must be set manually, but --no-confirm has been set without setting --cp4d-version")
            self.printDescription([
                f"Unknown catalog {self.getParam('mas_catalog_version')}, please manually select the version of Cloud Pak for Data to use"
            ])
            self.promptForString("Cloud Pak for Data product version", "cpd_product_version", default="4.8.0")
            logger.debug(f"Using user-provided (prompt) CP4D product version: {self.getParam('cpd_product_version')}")
        else:
            logger.debug(f"Using user-provided (flags) CP4D product version: {self.getParam('cpd_product_version')}")
        self.deployCP4D = True

    @logMethodCall
    def configSSOProperties(self):
        if self.showAdvancedOptions:
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

    @logMethodCall
    def configGuidedTour(self):
        if self.showAdvancedOptions:
            self.printH1("Enable Guided Tour")
            self.printDescription([
                "By default, Maximo Application Suite is configured with guided tour, you can disable this if it not required"
            ])
            if not self.yesOrNo("Enable Guided Tour"):
                self.setParam("mas_enable_walkme", "false")

    @logMethodCall
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

        if self.slsMode == 2 and not self.getParam("sls_namespace"):
            self.setParam("sls_namespace", f"mas-{self.getParam('mas_instance_id')}-sls")

        self.configOperationMode()
        self.configCATrust()
        self.configDNSAndCerts()
        self.configSSOProperties()
        self.configSpecialCharacters()
        self.configGuidedTour()

    @logMethodCall
    def configCATrust(self) -> None:
        if self.showAdvancedOptions:
            self.printH1("Certificate Authority Trust")
            self.printDescription([
                "By default, Maximo Application Suite is configured to trust well-known certificate authoritories, you can disable this so that it will only trust the CAs that you explicitly define"
            ])
            self.yesOrNo("Trust default CAs", "mas_trust_default_cas")
        else:
            self.setParam("mas_trust_default_cas", True)

    @logMethodCall
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

    @logMethodCall
    def configAnnotations(self):
        if self.operationalMode == 2:
            self.setParam("mas_annotations", "mas.ibm.com/operationalMode=nonproduction")

    @logMethodCall
    def configSNO(self):
        if self.isSNO():
            self.setParam("mongodb_replicas", "1")
            self.setParam("mongodb_cpu_requests", "500m")
            self.setParam("mas_app_settings_aio_flag", "false")

    @logMethodCall
    def configDNSAndCerts(self):
        if self.showAdvancedOptions:
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
                else:
                    self.manualCertsDir = None

    @logMethodCall
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
        self.setParam("mas_cluster_issuer", certIssuerOptions[certIssuer - 1])

    @logMethodCall
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
        self.setParam("mas_cluster_issuer", certIssuerOptions[certIssuer - 1])

    @logMethodCall
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

    @logMethodCall
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

        self.manageAppName = "Manage"
        self.isManageFoundation = False
        self.installManage = self.yesOrNo(f"Install {self.manageAppName}")

        # If the selection was to not install manage but we are in mas_channel 9.1 or later, we need to set self.isManageFoundation to True
        # Also, we need to force self.installManage to be True because Manage must always be installed in MAS 9.1 or later
        if not self.installManage:
            if not self.getParam("mas_channel").startswith("8.") and not self.getParam("mas_channel").startswith("9.0"):
                self.installManage = True
                self.isManageFoundation = True
                self.setParam("is_full_manage", "false")
                self.manageAppName = "Manage foundation"
                self.printDescription([f"{self.manageAppName} installs the following capabilities: User, Security groups, Application configurator and Mobile configurator."])
        else:
            self.setParam("is_full_manage", "true")

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

        self.installAiBroker = self.yesOrNo("Install AI Broker")
        if self.installAiBroker:
            self.configAppChannel("aibroker")

    @logMethodCall
    def configAppChannel(self, appId):
        versions = self.getCompatibleVersions(self.params["mas_channel"], appId)
        if len(versions) == 0:
            self.params[f"mas_app_channel_{appId}"] = prompt(HTML('<Yellow>Custom channel</Yellow> '))
        else:
            self.params[f"mas_app_channel_{appId}"] = versions[0]

    @logMethodCall
    def configStorageClasses(self):
        self.printH1("Configure Storage Class Usage")
        self.printDescription([
            "Maximo Application Suite and it's dependencies require storage classes that support ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes:",
            "  - ReadWriteOnce volumes can be mounted as read-write by multiple pods on a single node.",
            "  - ReadWriteMany volumes can be mounted as read-write by multiple pods across many nodes.",
            ""
        ])
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)
        if defaultStorageClasses.provider is not None:
            print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteOnce): {defaultStorageClasses.rwo}</LightSlateGrey>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteMany): {defaultStorageClasses.rwx}</LightSlateGrey>"))
            self.storageClassProvider = defaultStorageClasses.provider
            self.params["storage_class_rwo"] = defaultStorageClasses.rwo
            self.params["storage_class_rwx"] = defaultStorageClasses.rwx

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

    @logMethodCall
    def setIoTStorageClasses(self) -> None:
        if self.installIoT:
            self.setParam("mas_app_settings_iot_fpl_pvc_storage_class", self.getParam("storage_class_rwo"))
            self.setParam("mas_app_settings_iot_mqttbroker_pvc_storage_class", self.getParam("storage_class_rwo"))

    @logMethodCall
    def optimizerSettings(self) -> None:
        if self.installOptimizer:
            self.printH1("Configure Maximo Optimizer")
            if self.isSNO():
                self.printDescription(["Using Optimizer 'limited' plan as it is being installed in a single node cluster"])
                self.setParam("mas_app_plan_optimizer", "limited")
            else:
                self.printDescription(["Customize your Optimizer installation, 'full' and 'limited' install plans are available, refer to the product documentation for more information"])
                self.promptForString("Plan [full/limited]", "mas_app_plan_optimizer", default="full", validator=OptimizerInstallPlanValidator())

    @logMethodCall
    def predictSettings(self) -> None:
        if self.showAdvancedOptions and self.installPredict:
            self.printH1("Configure Maximo Predict")
            self.printDescription([
                "Predict application supports integration with IBM SPSS which is an optional service installed on top of IBM Cloud Pak for Data",
                "Unless requested these will not be installed"
            ])
            self.configCP4D()
            self.yesOrNo("Install IBM SPSS Statistics", "cpd_install_spss")

    @logMethodCall
    def assistSettings(self) -> None:
        if self.installAssist:
            self.printH1("Configure Maximo Assist")
            self.printDescription([
                "Assist requires access to Cloud Object Storage (COS), this install supports automatic setup using either IBMCloud COS or in-cluster COS via OpenShift Container Storage/OpenShift Data Foundation (OCS/ODF)"
            ])
            self.configCP4D()
            self.promptForString("COS Provider [ibm/ocs]", "cos_type")
            if self.getParam("cos_type") == "ibm":
                self.promptForString("IBM Cloud API Key", "cos_apikey", isPassword=True)
                self.promptForString("IBM Cloud Resource Group", "cos_resourcegroup")

    @logMethodCall
    def chooseInstallFlavour(self) -> None:
        self.printH1("Choose Install Mode")
        self.printDescription([
            "There are two flavours of the interactive install to choose from: <u>Simplified</u> and <u>Advanced</u>.  The simplified option will present fewer dialogs, but you lose the ability to configure the following aspects of the installation:",
            " - Configure installation namespaces",
            " - Provide pod templates",
            " - Configure Single Sign-On (SSO) settings"
            " - Configure whether to trust well-known certificate authorities by default (defaults to enabled)",
            " - Configure whether the Guided Tour feature is enabled (defaults to enabled)",
            " - Configure whether special characters are allowed in usernames and userids (defaults to disabled)",
            " - Configure a custom domain, DNS integrations, and manual certificates",
            " - Customize Maximo Manage database settings (schema, tablespace, indexspace)",
            " - Customize Maximo Manage server bundle configuration (defaults to \"all\" configuration)",
            " - Enable optional Maximo Manage integration Cognos Analytics and Watson Studio Local",
            " - Enable optional Maximo Predict integration with SPSS",
            " - Enable optional IBM Turbonomic integration",
            " - Customize Db2 node affinity and tolerations, memory, cpu, and storage settings (when using the IBM Db2 Universal Operator)",
            " - Choose alternative Apache Kafka providers (default to Strimzi)",
            " - Customize Grafana storage settings"
        ])
        self.showAdvancedOptions = self.yesOrNo("Show advanced installation options")

    @logMethodCall
    def interactiveMode(self, simplified: bool, advanced: bool) -> None:
        # Interactive mode
        self.interactiveMode = True

        if simplified:
            self.showAdvancedOptions = False
        elif advanced:
            self.showAdvancedOptions = True
        else:
            self.chooseInstallFlavour()

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
        self.configDRO()
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
        self.aibrokerSettings()

        # Dependencies
        self.configMongoDb()
        self.configDb2()
        self.configKafka()  # Will only do anything if IoT has been selected for install

        self.configGrafana()
        self.configTurbonomic()

        # TODO: Support ECK integration via the interactive install mode
        # TODO: Support MAS superuser username/password via the interactive install mode

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        self.interactiveMode = False

        # Set defaults
        # ---------------------------------------------------------------------
        # Unless a config file named "mongodb-system.yaml" is provided via the additional configs mechanism we will be installing a new MongoDb instance
        self.setParam("mongodb_action", "install")

        self.storageClassProvider = "custom"
        self.installAssist = False
        self.installIoT = False
        self.installMonitor = False
        self.installManage = False
        self.installPredict = False
        self.installInspection = False
        self.installOptimizer = False
        self.installAiBroker = False
        self.deployCP4D = False
        self.db2SetAffinity = False
        self.db2SetTolerations = False
        self.slsLicenseFileLocal = None

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
                # If there is a file named mongodb-system.yaml we will use this as a BYO MongoDB datasource
                if self.localConfigDir is not None and path.exists(path.join(self.localConfigDir, "mongodb-system.yaml")):
                    self.setParam("mongodb_action", "byo")
                    self.setParam("sls_mongodb_cfg_file", "/workspace/additional-configs/mongodb-system.yaml")

            elif key == "pod_templates":
                # For the named configurations we will convert into the path
                if value in ["best-effort", "guaranteed"]:
                    self.setParam("mas_pod_templates_dir", path.join(self.templatesDir, "pod-templates", value))
                else:
                    self.setParam("mas_pod_templates_dir", value)

            # We check for both None and "" values for the application channel parameters
            # value = None means the parameter wasn't set at all
            # value = "" means the paramerter was explicitly set to "don't install this application"
            elif key == "assist_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_assist", value)
                    self.installAssist = True
            elif key == "iot_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_iot", value)
                    self.installIoT = True
            elif key == "monitor_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_monitor", value)
                    self.installMonitor = True
            elif key == "manage_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_manage", value)
                    self.installManage = True
            elif key == "predict_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_predict", value)
                    self.installPredict = True
                    self.deployCP4D = True
            elif key == "visualinspection_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_visualinspection", value)
                    self.installInspection = True
            elif key == "aibroker_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_aibroker", value)
                    self.installAiBroker = True
            elif key == "optimizer_channel":
                if value is not None and value != "":
                    self.setParam("mas_app_channel_optimizer", value)
                    self.installOptimizer = True
            elif key == "optimizer_plan":
                if value is not None and value != "":
                    self.setParam("mas_app_plan_optimizer", value)

            # Manage advanced settings that need extra processing
            elif key == "mas_app_settings_server_bundle_size":
                if value is not None:
                    self.setParam(key, value)
                    if value in ["jms", "snojms"]:
                        self.setParam("mas_app_settings_persistent_volumes_flag", "true")

            # MongoDB
            elif key == "mongodb_namespace":
                if value is not None and value != "":
                    self.setParam(key, value)
                    self.setParam("sls_mongodb_cfg_file", f"/workspace/configs/mongo-{value}.yml")

            # SLS
            elif key == "license_file":
                if value is not None and value != "":
                    self.slsLicenseFileLocal = value
                    self.setParam("sls_action", "install")
            elif key == "dedicated_sls":
                if value:
                    self.setParam("sls_namespace", f"mas-{self.args.mas_instance_id}-sls")

            # These settings are used by the CLI rather than passed to the PipelineRun
            elif key == "storage_accessmode":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageAccessMode = value
            elif key == "storage_pipeline":
                if value is None:
                    self.fatalError(f"{key} must be set")
                self.pipelineStorageClass = value

            elif key.startswith("approval_"):
                if key not in self.approvals:
                    raise KeyError(f"{key} is not a supported approval workflow ID: {self.approvals.keys()}")

                if value != "":
                    valueParts = value.split(":")
                    if len(valueParts) != 3:
                        self.fatalError(f"Unsupported format for {key} ({value}).  Expected MAX_RETRIES:RETRY_DELAY:IGNORE_FAILURE")
                    else:
                        try:
                            self.approvals[key]["maxRetries"] = int(valueParts[0])
                            self.approvals[key]["retryDelay"] = int(valueParts[1])
                            self.approvals[key]["ignoreFailure"] = bool(valueParts[2])
                        except ValueError:
                            self.fatalError(f"Unsupported format for {key} ({value}).  Expected int:int:boolean")

            # Arguments that we don't need to do anything with
            elif key in ["accept_license", "dev_mode", "skip_pre_check", "skip_grafana_install", "no_confirm", "no_wait_for_pvc", "help", "advanced", "simplified"]:
                pass

            elif key == "manual_certificates":
                if value is not None:
                    self.setParam("mas_manual_cert_mgmt", True)
                    self.manualCertsDir = value
                else:
                    self.setParam("mas_manual_cert_mgmt", False)
                    self.manualCertsDir = None

            # Fail if there's any arguments we don't know how to handle
            else:
                print(f"Unknown option: {key} {value}")
                self.fatalError(f"Unknown option: {key} {value}")

        if self.installManage:
            # If Manage is being installed and --is-full-manage was set to something different than "false", assume it is "true"
            if self.getParam("is_full_manage") != "false":
                self.setParam("is_full_manage", "true")

        # Load the catalog information
        self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))

        # License file is only optional for existing SLS instance
        if self.slsLicenseFileLocal is None:
            if findSLSByNamespace(self.getParam("sls_namespace"), dynClient=self.dynamicClient):
                self.setParam("sls_action", "gencfg")
            else:
                self.fatalError("--license-file must be set for new SLS install")

        # Once we've processed the inputs, we should validate the catalog source & prompt to accept the license terms
        if not self.devMode:
            self.validateCatalogSource()
            self.licensePrompt()

    @logMethodCall
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

        # Set image_pull_policy of the CLI in interactive mode
        if args.image_pull_policy and args.image_pull_policy != "":
            self.setParam("image_pull_policy", args.image_pull_policy)

        self.approvals = {}

        # Store all args
        self.args = args

        # These flags work for setting params in both interactive and non-interactive modes
        if args.skip_pre_check:
            self.setParam("skip_pre_check", "true")

        if instanceId is None:
            self.printH1("Set Target OpenShift Cluster")
            # Connect to the target cluster
            self.connect()
        else:
            logger.debug("MAS instance ID is set, so we assume already connected to the desired OCP")
            self.lookupTargetArchitecture()

        if self.dynamicClient is None:
            print_formatted_text(HTML("<Red>Error: The Kubernetes dynamic Client is not available.  See log file for details</Red>"))
            exit(1)

        # Perform a check whether the cluster is set up for airgap install, this will trigger an early failure if the cluster is using the now
        # deprecated MaximoApplicationSuite ImageContentSourcePolicy instead of the new ImageDigestMirrorSet
        self.isAirgap()

        # Configure the installOptions for the appropriate architecture
        self.catalogOptions = supportedCatalogs[self.architecture]

        # Basic settings before the user provides any input
        self.configICR()
        self.configCertManager()  # TODO: I think this is redundant, we should look to remove this and the appropriate params in the install pipeline
        self.deployCP4D = False

        # UDS install has not been supported since the January 2024 catalog update
        self.setParam("uds_action", "install-dro")

        # User must either provide the configuration via numerous command line arguments, or the interactive prompts
        if instanceId is None:
            self.interactiveMode(simplified=args.simplified, advanced=args.advanced)
        else:
            self.nonInteractiveMode()

        # After we've configured the basic inputs, we can calculate these ones
        self.setIoTStorageClasses()
        if self.deployCP4D:
            self.configCP4D()

        # Set up the secrets for additional configs, podtemplates, sls license file and manual certificates
        self.additionalConfigs()
        self.podTemplates()
        self.slsLicenseFile()
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
                h.stop_and_persist(symbol=self.successIcon, text="OpenShift Pipelines Operator is installed and ready to use")

            with Halo(text=f'Preparing namespace ({pipelinesNamespace})', spinner=self.spinner) as h:
                createNamespace(self.dynamicClient, pipelinesNamespace)
                preparePipelinesNamespace(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("mas_instance_id"),
                    storageClass=self.pipelineStorageClass,
                    accessMode=self.pipelineStorageAccessMode,
                    waitForBind=wait,
                    configureRBAC=(self.getParam("service_account_name") == "")
                )
                prepareInstallSecrets(
                    dynClient=self.dynamicClient,
                    instanceId=self.getParam("mas_instance_id"),
                    slsLicenseFile=self.slsLicenseFileSecret,
                    additionalConfigs=self.additionalConfigsSecret,
                    podTemplates=self.podTemplatesSecret,
                    certs=self.certsSecret
                )

                self.setupApprovals(pipelinesNamespace)

                h.stop_and_persist(symbol=self.successIcon, text=f"Namespace is ready ({pipelinesNamespace})")

            with Halo(text='Testing availability of MAS CLI image in cluster', spinner=self.spinner) as h:
                testCLI()
                h.stop_and_persist(symbol=self.successIcon, text="MAS CLI image deployment test completed")

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

    @logMethodCall
    def setupApprovals(self, namespace: str) -> None:
        """
        Ensure the supported approval configmaps are in the expected state for the start of the run:
         - not present (if approval is not required)
         - present with the chosen state field initialized to ""
        """
        for approval in self.approvals.values():
            if "maxRetries" in approval:
                # Enable this approval workload
                logger.debug(f"Approval workflow for {approval['id']} will be enabled during install ({approval['maxRetries']} / {approval['retryDelay']}s / {approval['ignoreFailure']})")
                self.initializeApprovalConfigMap(namespace, approval['id'], True, approval['maxRetries'], approval['retryDelay'], approval['ignoreFailure'])
            else:
                # Disable this approval workload
                logger.debug(f"Approval workflow for {approval['id']} will be disabled during install")
                self.initializeApprovalConfigMap(namespace, approval['id'], False)
