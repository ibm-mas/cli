# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from mas.cli.validators import LanguageValidator
from mas.devops.aiservice import listAiServiceTenantInstances, listAiServiceInstances
from mas.devops.utils import isVersionEqualOrAfter
from openshift.dynamic.exceptions import ResourceNotFoundError
from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.completion import WordCompleter

from ...validators import AiserviceTeanantIDValidator

import logging

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from prompt_toolkit.validation import Validator

    from ..context import InstallContext


class ManageSettingsMixin:
    if TYPE_CHECKING:
        # Context object with all state
        context: InstallContext

        # Methods from PrintMixin
        def printH1(self, message: str) -> None: ...  # noqa: E704

        def printH2(self, message: str) -> None: ...  # noqa: E704

        def printDescription(self, content: list[str]) -> None: ...  # noqa: E704

        # Methods from PromptMixin
        def yesOrNo(
            self, message: str, param: str | None = None
        ) -> bool: ...  # noqa: E704

        def promptForString(  # noqa: E704
            self,
            message: str,
            param: str | None = None,
            default: str = "",
            isPassword: bool = False,
            validator: Validator | None = None,
            completer: WordCompleter | None = None,
        ) -> str: ...

        def promptForInt(  # noqa: E704
            self,
            message: str,
            param: str | None = None,
            default: int | None = None,
            min: int | None = None,
            max: int | None = None,
        ) -> int: ...

        def fatalError(  # noqa: E704
            self, message: str, exception: Exception | None = None
        ) -> NoReturn: ...

        # Methods from other mixins
        def configCP4D(self) -> None: ...  # noqa: E704

    def manageSettings(self) -> None:
        if self.context.installManage:
            self.printH1(f"Configure Maximo {self.context.manageAppName}")
            self.printDescription(
                [
                    f"Customize your {self.context.manageAppName} installation, refer to the product documentation for more information"
                ]
            )

            self.manageSettingsComponents()

            self.manageSettingsServerBundleConfig()
            self.manageSettingsJMS()
            self.manageSettingsDatabase()
            self.manageSettingsCustomizationArchive()
            self.manageSettingsAiService()
            self.manageSettingsOther()
            self.manageStorageAndAccessMode()

    def manageStorageAndAccessMode(self) -> None:
        # Default to RWX storage classes, but fall back to RWO in SNO or when user
        # has chosen not to provide a RWX storage class
        storageClass = self.context.getParam("storage_class_rwx")
        accessMode = "ReadWriteMany"
        if self.context.isSNO or self.context.getParam("storage_class_rwx") == "none":
            storageClass = self.context.getParam("storage_class_rwo")
            accessMode = "ReadWriteOnce"

        self.context.setParam(
            "mas_app_settings_doclinks_pvc_storage_class", storageClass
        )
        self.context.setParam("mas_app_settings_bim_pvc_storage_class", storageClass)
        self.context.setParam(
            "mas_app_settings_jms_queue_pvc_storage_class", storageClass
        )

        self.context.setParam("mas_app_settings_doclinks_pvc_accessmode", accessMode)
        self.context.setParam("mas_app_settings_bim_pvc_accessmode", accessMode)
        self.context.setParam("mas_app_settings_jms_queue_pvc_accessmode", accessMode)

    def manageSettingsComponents(self) -> None:
        # Only ask to install Manage components if this is a full Manage installation
        # If this is a Manage Foundation installation, leave mas_appws_components blank
        if self.context.isManageFoundation:
            self.context.params["mas_appws_components"] = ""
        else:
            self.printH2(f"Maximo {self.context.manageAppName} Components")
            self.printDescription(
                [
                    f"The default configuration will install {self.context.manageAppName} with Health enabled, "
                    "alternatively choose exactly what industry solutions and add-ons will be configured"
                ]
            )

            self.context.params["mas_appws_components"] = "base=latest,health=latest"
            if self.yesOrNo("Select components to enable"):
                self.context.params["mas_appws_components"] = "base=latest"
                if self.yesOrNo(" - Asset Configuration Manager"):
                    self.context.params["mas_appws_components"] += ",acm=latest"
                if self.yesOrNo(" - Aviation"):
                    self.context.params["mas_appws_components"] += ",aviation=latest"
                if self.yesOrNo(" - Civil Infrastructure"):
                    self.context.params["mas_appws_components"] += ",civil=latest"

                    # Check if Manage version supports Kafka Image Processor (9.2+)
                    manageChannel = self.context.getParam("mas_app_channel_manage")
                    if manageChannel and isVersionEqualOrAfter("9.2.0", manageChannel):
                        self.printDescription(
                            [
                                "",
                                "Civil Infrastructure Defect Detection with Kafka Image Processor:",
                                "The Kafka Image Processor enables advanced defect detection capabilities.",
                                "This requires a Kafka instance and uses 10GB of storage for image processing.",
                            ]
                        )

                        if self.yesOrNo(
                            "Enable Kafka Image Processor for Civil Infrastructure"
                        ):
                            self.context.enableKafkaImageProcessor = True
                            # Bind Manage to system Kafka (similar to JDBC binding pattern)
                            self.context.setParam(
                                "mas_appws_bindings_kafka_manage", "system"
                            )
                if self.yesOrNo(" - Envizi"):
                    self.context.params["mas_appws_components"] += ",envizi=latest"
                if self.yesOrNo(" - Health"):
                    self.context.params["mas_appws_components"] += ",health=latest"
                if self.yesOrNo(" - Health, Safety and Environment"):
                    self.context.params["mas_appws_components"] += ",hse=latest"
                if self.yesOrNo(" - Maximo IT"):
                    self.context.params["mas_appws_components"] += ",icd=latest"
                if self.yesOrNo(" - Nuclear"):
                    self.context.params["mas_appws_components"] += ",nuclear=latest"
                if self.yesOrNo(" - Oil & Gas"):
                    self.context.params["mas_appws_components"] += ",oilandgas=latest"
                if self.yesOrNo(" - Connector for Oracle Applications"):
                    self.context.params[
                        "mas_appws_components"
                    ] += ",oracleadapter=latest"
                if self.yesOrNo(" - Connector for SAP Application"):
                    self.context.params["mas_appws_components"] += ",sapadapter=latest"
                if self.yesOrNo(" - Service Provider"):
                    self.context.params[
                        "mas_appws_components"
                    ] += ",serviceprovider=latest"
                if self.yesOrNo(" - Spatial"):
                    self.context.params["mas_appws_components"] += ",spatial=latest"
                if self.yesOrNo(" - Strategize"):
                    self.context.params["mas_appws_components"] += ",strategize=latest"
                if self.yesOrNo(" - Transportation"):
                    self.context.params[
                        "mas_appws_components"
                    ] += ",transportation=latest"
                if self.yesOrNo(" - Tririga"):
                    self.context.params["mas_appws_components"] += ",tririga=latest"
                if self.yesOrNo(" - Utilities"):
                    self.context.params["mas_appws_components"] += ",utilities=latest"
                if self.yesOrNo(" - Workday Applications"):
                    self.context.params["mas_appws_components"] += ",workday=latest"
                if self.yesOrNo(" - AIP"):
                    self.context.params["mas_appws_components"] += ",aip=latest"
                if self.yesOrNo(" - Vegetation Management"):
                    self.context.params["mas_appws_components"] += ",vegm=latest"
                # Collaborate is only available in Manage 9.2 or higher
                manageChannel = self.context.getParam("mas_app_channel_manage")
                if manageChannel and isVersionEqualOrAfter("9.2.0", manageChannel):
                    if self.yesOrNo(" - Collaborate"):
                        self.context.params[
                            "mas_appws_components"
                        ] += ",collaborate=latest"
                logger.debug(
                    f"Generated mas_appws_components = {self.context.params['mas_appws_components']}"
                )
                if ",icd=" in self.context.params["mas_appws_components"]:
                    self.printH2("Maximo IT License Terms")
                    self.printDescription(
                        [
                            "For information about your Maximo IT License, see <Orange><u>https://ibm.biz/MAXIT81-License</u></Orange>",
                            "To continue with the installation, you must accept these additional license terms",
                        ]
                    )

                    if not self.yesOrNo("Do you accept the license terms"):
                        exit(1)

    def manageSettingsDatabase(self) -> None:
        if self.context.showAdvancedOptions:
            self.printH2(f"Maximo {self.context.manageAppName} Settings - Database")
            self.printDescription(
                [
                    f"Customise the schema, tablespace, indexspace, and encryption settings used by {self.context.manageAppName}"
                ]
            )

            if self.yesOrNo("Customize database settings"):
                self.promptForString(
                    "Schema", "mas_app_settings_db2_schema", default="maximo"
                )
                self.promptForString(
                    "Tablespace", "mas_app_settings_tablespace", default="MAXDATA"
                )
                self.promptForString(
                    "Indexspace", "mas_app_settings_indexspace", default="MAXINDEX"
                )

                if self.yesOrNo("Customize database encryption settings"):
                    self.promptForString(
                        "MXE_SECURITY_CRYPTO_KEY",
                        "mas_manage_encryptionsecret_crypto_key",
                    )
                    self.promptForString(
                        "MXE_SECURITY_CRYPTOX_KEY",
                        "mas_manage_encryptionsecret_cryptox_key",
                    )
                    self.promptForString(
                        "MXE_SECURITY_OLD_CRYPTO_KEY",
                        "mas_manage_encryptionsecret_old_crypto_key",
                    )
                    self.promptForString(
                        "MXE_SECURITY_OLD_CRYPTOX_KEY",
                        "mas_manage_encryptionsecret_old_cryptox_key",
                    )
                    self.promptForString(
                        "Encryption secret name", "mas_manage_ws_db_encryptionsecret"
                    )

    def manageSettingsServerBundleConfig(self) -> None:
        if not self.context.isManageFoundation:
            if self.context.showAdvancedOptions:
                self.printH2(
                    f"Maximo {self.context.manageAppName} Settings - Server Bundles"
                )
                self.printDescription(
                    [
                        f"Define how you want to configure {self.context.manageAppName} servers:",
                        f" - You can have one or multiple {self.context.manageAppName} servers distributing workload",
                        " - Additionally, you can choose to include JMS server for messaging queues",
                        "",
                        "Configurations:",
                        "  1. Deploy the 'all' server pod only (workload is concentrated in just one server pod but consumes less resource)",
                        "  2. Deploy the 'all' and 'jms' bundle pods (workload is concentrated in just one server pod and includes jms server)",
                    ]
                )

                if not self.context.isSNO:
                    self.printDescription(
                        [
                            "  3. Deploy the 'mea', 'report', 'ui' and 'cron' bundle pods "
                            "(workload is distributed across multiple server pods)",
                            "  4. Deploy the 'mea', 'report', 'ui', 'cron' and 'jms' bundle pods "
                            "(workload is distributed across multiple server pods and includes jms server)",
                        ]
                    )

                manageServerBundleSelection = self.promptForString(
                    "Select a server bundle configuration"
                )

                if manageServerBundleSelection == "1":
                    self.context.setParam("mas_app_settings_server_bundles_size", "dev")
                elif manageServerBundleSelection == "2":
                    self.context.setParam(
                        "mas_app_settings_server_bundles_size", "snojms"
                    )
                    self.context.setParam(
                        "mas_app_settings_persistent_volumes_flag", "true"
                    )
                elif manageServerBundleSelection == "3":
                    self.context.setParam(
                        "mas_app_settings_server_bundles_size", "small"
                    )
                elif manageServerBundleSelection == "4":
                    self.context.setParam("mas_app_settings_server_bundles_size", "jms")
                    self.context.setParam(
                        "mas_app_settings_persistent_volumes_flag", "true"
                    )
                else:
                    self.fatalError("Invalid selection")
            else:
                self.context.setParam("mas_app_settings_server_bundles_size", "dev")

    def manageSettingsJMS(self) -> None:
        if self.context.getParam("mas_app_settings_server_bundles_size") in [
            "jms",
            "snojms",
        ]:
            self.printDescription(
                [
                    f"Only {self.context.manageAppName} JMS sequential queues (sqin and sqout) are enabled by default.",
                    "However, you can enable both sequential (sqin and sqout) and continuous queues (cqin and cqout)",
                ]
            )

            self.yesOrNo(
                f"Enable both {self.context.manageAppName} JMS sequential and continuous queues",
                "mas_app_settings_default_jms",
            )

    def manageSettingsCustomizationArchive(self) -> None:
        # Only ask about customization archive in full Manage installation
        if not self.context.isManageFoundation:
            self.printH2(
                f"Maximo {self.context.manageAppName} Settings - Customization"
            )
            self.printDescription(
                [
                    f"Provide a customization archive to be used in the "
                    f"{self.context.manageAppName} build process"
                ]
            )

            if self.yesOrNo("Include customization archive"):
                self.promptForString(
                    "Customization archive name",
                    "mas_app_settings_customization_archive_name",
                )
                self.promptForString(
                    "Customization archive path/url",
                    "mas_app_settings_customization_archive_url",
                )
                if self.yesOrNo(
                    "Provide authentication to access customization archive URL"
                ):
                    self.promptForString(
                        "Username", "mas_app_settings_customization_archive_username"
                    )
                    self.promptForString(
                        "Password",
                        "mas_app_settings_customization_archive_password",
                        isPassword=True,
                    )

    def manageSettingsDemodata(self) -> None:
        self.yesOrNo("Create demo data", "mas_app_settings_demodata")

    def manageSettingsTimezone(self) -> None:
        self.promptForString(
            f"{self.context.manageAppName} server timezone",
            "mas_app_settings_server_timezone",
            default="GMT",
        )
        # Set Manage dedicated Db2 instance timezone to be same as Manage server timezone
        self.context.setParam(
            "db2_timezone", self.context.getParam("mas_app_settings_server_timezone")
        )

    def manageSettingsLanguages(self) -> None:
        self.printH2(f"Maximo {self.context.manageAppName} Settings - Languages")
        self.printDescription(
            [f"Define the base language for Maximo {self.context.manageAppName}"]
        )
        baseLanguage = self.promptForString(
            "Base language",
            validator=LanguageValidator(list(self.context.supportedLanguages)),
            completer=WordCompleter(list(self.context.supportedLanguages)),
        )

        self.context.setParam("mas_app_settings_base_lang", baseLanguage.upper())

        self.printDescription(
            [
                f"Define the additional languages to be configured in Maximo {self.context.manageAppName}. "
                "Provide a comma-separated list of the supported languages indexes, for example: 'DA,EN,ZH-TW'",
                "A complete list of available language codes is available online:",
                "    <Orange><u>https://www.ibm.com/docs/en/mas-cd/mhmpmh-and-p-u/continuous-delivery?topic=deploy-language-support</u></Orange>",
            ]
        )

        secondaryLanguages = self.promptForString(
            "Secondary language",
            validator=LanguageValidator(list(self.context.supportedLanguages)),
            completer=WordCompleter(list(self.context.supportedLanguages)),
        )
        self.context.setParam(
            "mas_app_settings_secondary_langs", secondaryLanguages.upper()
        )

    def manageSettingsCP4D(self) -> None:
        if (
            self.context.getParam("mas_app_channel_manage") in ["8.7.x", "9.0.x"]
            and self.context.showAdvancedOptions
        ):
            self.printDescription(
                [
                    f"Integration with Cognos Analytics provides additional support for reporting features in "
                    f"Maximo {self.context.manageAppName}, for more information refer to the documentation online: ",
                    " - <Orange><u>https://ibm.biz/BdMuxs</u></Orange>",
                ]
            )
            self.yesOrNo(
                "Enable integration with Cognos Analytics", "cpd_install_cognos"
            )
            self.yesOrNo(
                "Enable integration with Watson Studio Local",
                "mas_appws_bindings_health_flag",
            )

            if (
                self.context.getParam("cpd_install_cognos") == "true"
                or self.context.getParam("mas_appws_bindings_health_flag") == "true"
            ):
                self.configCP4D()

    def manageSettingsOther(self) -> None:
        self.printH2(f"Maximo {self.context.manageAppName} Settings - Other")
        if self.context.isManageFoundation:
            if self.context.showAdvancedOptions:
                self.printDescription(
                    [
                        "Configure additional settings:",
                        "  - Base and additional languages",
                        "  - Server timezone",
                    ]
                )
                self.manageSettingsTimezone()
                self.manageSettingsLanguages()
        else:
            if self.context.showAdvancedOptions:
                self.printDescription(
                    [
                        "Configure additional settings:",
                        "  - Demo data",
                        "  - Base and additional languages",
                        "  - Server timezone",
                        "  - Cognos integration (install Cloud Pak for Data)",
                        "  - Watson Studio Local integration (install Cloud Pak for Data)",
                    ]
                )
                self.manageSettingsDemodata()
                self.manageSettingsTimezone()
                self.manageSettingsLanguages()
                self.manageSettingsCP4D()

    def manageSettingsAiService(self) -> None:
        dynamicClient = self.context.dynamicClient
        if dynamicClient is None:
            self.fatalError("Dynamic client is not initialized")

        try:
            aiserviceTenantInstances = listAiServiceTenantInstances(dynamicClient)
            aiserviceInstances = listAiServiceInstances(dynamicClient)
        except ResourceNotFoundError:
            aiserviceTenantInstances = []
            aiserviceInstances = []

        if self.context.installAIService:
            # if aiservice is being installed along with manage, add default tenant instance
            aiserviceTenantInstances.append("user")
            # Set aiservice instance id from the provided aiservice_instance_id parameter
            if self.context.getParam("aiservice_instance_id"):
                self.context.setParam(
                    "manage_bind_aiservice_instance_id",
                    self.context.getParam("aiservice_instance_id"),
                )
        elif len(aiserviceTenantInstances) == 0 or len(aiserviceInstances) == 0:
            return
        else:
            # Set aiservice instance id from the first instance fetched from cluster
            self.context.setParam(
                "manage_bind_aiservice_instance_id",
                aiserviceInstances[0]["metadata"]["name"],
            )

        self.printH2(
            f"Maximo {self.context.manageAppName} Settings - AI Service Tenant Configuration"
        )

        self.printDescription(
            [
                "Select an AI Service Tenant ID to bind with Manage:",
                " - The selected AI Service Tenant will be used in Manage AI Config Application",
            ]
        )

        if self.context.installAIService:
            self.printDescription(
                [
                    " - As AI Service is being installed along with Manage, a default Tenant ID 'user' is available in the list below"
                ]
            )
            # Show only default 'user' tenant when AI Service is being installed
            aiserviceTenantOptions = ["user"]
            print_formatted_text(HTML("- <u>user</u> (default)"))
        else:
            # Show all available tenants from cluster
            aiserviceTenantOptions = []
            for aiserviceTenant in aiserviceTenantInstances:
                print_formatted_text(
                    HTML(
                        f"- <u>{aiserviceTenant['metadata']['name'].split('-')[-1]}</u>"
                    )
                )
                aiserviceTenantOptions.append(
                    aiserviceTenant["metadata"]["name"].split("-")[-1]
                )

        aiserviceTenantCompleter = WordCompleter(aiserviceTenantOptions)
        print()

        aiserviceTenantInstanceId = self.promptForString(
            "Enter AI Service Tenant ID to bind with Manage: ",
            completer=aiserviceTenantCompleter,
            validator=AiserviceTeanantIDValidator(
                self.context.getParam("manage_bind_aiservice_instance_id"),
                self.context.installAIService,
            ),
        )
        self.context.setParam(
            "manage_bind_aiservice_tenant_id", aiserviceTenantInstanceId
        )
