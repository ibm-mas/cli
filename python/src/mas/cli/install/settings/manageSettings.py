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
logger = logging.getLogger(__name__)

class ManageSettingsMixin():

    def arcgisSettings(self) -> None:
        # If Spatial is selected, then prompt to choose to add IBM Maximo Location Services for Esri, and prompt license
        if "spatial=" in self.getParam("mas_appws_components") and self.getParam("mas_app_channel_manage").startswith("9."):
            self.printDescription([
                "",
                "Maximo Spatial requires a map server provider in order to enable geospatial capabilities",
                "You may choose your preferred map provider later or you can enable IBM Maximo Location Services for Esri now",
                "This includes ArcGIS Enterprise as part of the Manage and Maximo Spatial bundle (Additional AppPoints required)."
            ])

            if self.yesOrNo("Include IBM Maximo Location Services for Esri"):
                self.setParam("install_arcgis", "true")
                self.setParam("mas_arcgis_channel", self.getParam("mas_app_channel_manage"))

                self.printDescription([
                    "",
                    "IBM Maximo Location Services for Esri License Terms",
                    "For information about your IBM Maximo Location Services for Esri License visit: ",
                    " <u>https://ibm.biz/MAXArcGIS90-License</u>",
                    "To continue with the installation, you must accept these additional license terms"
                ])

                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

    def manageSettings(self) -> None:
        if self.installManage:
            self.printH1("Configure Maximo Manage")
            self.printDescription(["Customize your Manage installation, refer to the product documentation for more information"])

            self.manageSettingsComponents()
            self.arcgisSettings()

            self.manageSettingsServerBundleConfig()
            self.manageSettingsJMS()
            self.manageSettingsDatabase()
            self.manageSettingsCustomizationArchive()
            self.manageSettingsOther()

            # Default to RWX storage classes, but fall back to RWO in SNO or when user
            # has chosen not to provide a RWX storage class
            storageClass = self.getParam("storage_class_rwx")
            accessMode = "ReadWriteMany"
            if self.isSNO() or self.getParam("storage_class_rwx") == "none":
                storageClass = self.getParam("storage_class_rwo")
                accessMode = "ReadWriteOnce"

            self.setParam("mas_app_settings_doclinks_pvc_storage_class", storageClass)
            self.setParam("mas_app_settings_bim_pvc_storage_class", storageClass)
            self.setParam("mas_app_settings_jms_queue_pvc_storage_class", storageClass)

            self.setParam("mas_app_settings_doclinks_pvc_accessmode", accessMode)
            self.setParam("mas_app_settings_bim_pvc_accessmode", accessMode)
            self.setParam("mas_app_settings_jms_queue_pvc_accessmode", accessMode)

    def manageSettingsComponents(self) -> None:
        self.printH2("Maximo Manage Components")
        self.printDescription(["The default configuration will install Manage with Health enabled, alternatively choose exactly what industry solutions and add-ons will be configured"])

        self.params["mas_appws_components"] = "base=latest,health=latest"
        if self.yesOrNo("Select components to enable"):
            self.params["mas_appws_components"] = "base=latest"
            if self.yesOrNo(" - Asset Configuration Manager"): self.params["mas_appws_components"] += ",acm=latest"
            if self.yesOrNo(" - Aviation"): self.params["mas_appws_components"] += ",acm=latest"
            if self.yesOrNo(" - Civil Infrastructure"): self.params["mas_appws_components"] += ",civil=latest"
            if self.yesOrNo(" - Envizi"): self.params["mas_appws_components"] += ",envizi=latest"
            if self.yesOrNo(" - Health"): self.params["mas_appws_components"] += ",health=latest"
            if self.yesOrNo(" - Health, Safety and Environment"): self.params["mas_appws_components"] += ",hse=latest"
            if self.yesOrNo(" - Maximo IT"): self.params["mas_appws_components"] += ",icd=latest"
            if self.yesOrNo(" - Nuclear"): self.params["mas_appws_components"] += ",nuclear=latest"
            if self.yesOrNo(" - Oil & Gas"): self.params["mas_appws_components"] += ",oilandgas=latest"
            if self.yesOrNo(" - Connector for Oracle Applications"): self.params["mas_appws_components"] += ",oracleadapter=latest"
            if self.yesOrNo(" - Connector for SAP Application"): self.params["mas_appws_components"] += ",sapadapter=latest"
            if self.yesOrNo(" - Service Provider"): self.params["mas_appws_components"] += ",serviceprovider=latest"
            if self.yesOrNo(" - Spatial"): self.params["mas_appws_components"] += ",spatial=latest"
            if self.yesOrNo(" - Strategize"): self.params["mas_appws_components"] += ",strategize=latest"
            if self.yesOrNo(" - Transportation"): self.params["mas_appws_components"] += ",transportation=latest"
            if self.yesOrNo(" - Tririga"): self.params["mas_appws_components"] += ",tririga=latest"
            if self.yesOrNo(" - Utilities"): self.params["mas_appws_components"] += ",utilities=latest"
            if self.yesOrNo(" - Workday Applications"): self.params["mas_appws_components"] += ",workday=latest"
            logger.debug(f"Generated mas_appws_components = {self.params['mas_appws_components']}")

            if ",icd=" in self.params["mas_appws_components"]:
                self.printH2("Maximo IT License Terms")
                self.printDescription([
                    "For information about your Maximo IT License, see https://ibm.biz/MAXIT81-License",
                    "To continue with the installation, you must accept these additional license terms"
                ])

                if not self.yesOrNo("Do you accept the license terms"):
                    exit(1)

    def manageSettingsDatabase(self) -> None:
        self.printH2("Maximo Manage Settings - Database")
        self.printDescription(["Customise the schema, tablespace, indexspace, and encryption settings used by Manage"])

        if self.yesOrNo("Customize database settings"):
            self.promptForString("Schema", "mas_app_settings_db2_schema", default="maximo")
            self.promptForString("Tablespace", "mas_app_settings_tablespace", default="MAXDATA")
            self.promptForString("Indexspace", "mas_app_settings_indexspace", default="MAXINDEX")

            if self.yesOrNo("Customize database encryption settings"):
                self.promptForString("MXE_SECURITY_CRYPTO_KEY", "mas_app_settings_crypto_key")
                self.promptForString("MXE_SECURITY_CRYPTOX_KEY", "mas_app_settings_cryptox_key")
                self.promptForString("MXE_SECURITY_OLD_CRYPTO_KEY", "mas_app_settings_old_crypto_key")
                self.promptForString("MXE_SECURITY_OLD_CRYPTOX_KEY", "mas_app_settings_old_cryptox_key")
                self.yesOrNo("Override database encryption secrets with provided keys", "mas_app_settings_override_encryption_secrets_flag")

    def manageSettingsServerBundleConfig(self) -> None:
        self.printH2("Maximo Manage Settings - Server Bundles")
        self.printDescription([
            "Define how you want to configure Manage servers:",
            " - You can have one or multiple Manage servers distributing workload",
            " - Additionally, you can choose to include JMS server for messaging queues",
            "",
            "Configurations:",
            "  1. Deploy the 'all' server pod only (workload is concentrated in just one server pod but consumes less resource)",
            "  2. Deploy the 'all' and 'jms' bundle pods (workload is concentrated in just one server pod and includes jms server)"
        ])

        if not self.isSNO():
            self.printDescription([
                "  3. Deploy the 'mea', 'report', 'ui' and 'cron' bundle pods (workload is distributed across multiple server pods)",
                "  4. Deploy the 'mea', 'report', 'ui', 'cron' and 'jms' bundle pods (workload is distributed across multiple server pods and includes jms server)"
            ])

        manageServerBundleSelection = self.promptForString("Select a server bundle configuration")

        if manageServerBundleSelection == "1":
            self.setParam("mas_app_settings_server_bundles_size", "dev")
        elif manageServerBundleSelection == "2":
            self.setParam("mas_app_settings_server_bundles_size", "snojms")
            self.setParam("mas_app_settings_persistent_volumes_flag", "true")
        elif manageServerBundleSelection == "3":
            self.setParam("mas_app_settings_server_bundles_size", "small")
        elif manageServerBundleSelection == "4":
            self.setParam("mas_app_settings_server_bundles_size", "jms")
            self.setParam("mas_app_settings_persistent_volumes_flag", "true")
        else:
            self.fatalError("Invalid selection")

    def manageSettingsJMS (self) -> None:
        if self.getParam("mas_app_settings_server_bundles_size") in ["jms", "snojms"]:
            self.printDescription([
                "Only Manage JMS sequential queues (sqin and sqout) are enabled by default.",
                "However, you can enable both sequential (sqin and sqout) and continuous queues (cqin and cqout)"
            ])

            self.yesOrNo("Enable both Manage JMS sequential and continuous queues", "mas_app_settings_default_jms")

    def manageSettingsCustomizationArchive(self) -> None:
        self.printH2("Maximo Manage Settings - Customization")
        self.printDescription([
            "Provide a customization archive to be used in the Manage build process"
        ])

        if self.yesOrNo("Include customization archive"):
            self.promptForString("Customization archive name", "mas_app_settings_customization_archive_name")
            self.promptForString("Customization archive path/url", "mas_app_settings_customization_archive_url")
            if self.yesOrNo("Provide authentication to access customization archive URL"):
                self.promptForString("Username", "mas_app_settings_customization_archive_username")
                self.promptForString("Password", "mas_app_settings_customization_archive_password", isPassword=True)

    def manageSettingsDemodata(self) -> None:
        self.yesOrNo("Create demo data", "mas_app_settings_demodata")

    def manageSettingsTimezone(self) -> None:
        self.promptForString("Manage server timezone", "mas_app_settings_server_timezone", default="GMT")
        # Set Manage dedicated Db2 instance timezone to be same as Manage server timezone
        self.setParam("db2_timezone", self.getParam("mas_app_settings_server_timezone"))

    def manageSettingsLanguages(self) -> None:
        self.printH2("Maximo Manage Settings - Languages")
        self.printDescription([
            "Define the base language for Maximo Manage"
        ])
        self.promptForString("Base language", "mas_app_settings_base_lang", default="EN")

        self.printDescription([
            "Define the additional languages to be configured in Maximo Manage. provide a comma-separated list of supported languages codes, for example: 'JA,DE,AR'",
            "A complete list of available language codes is available online:",
            "    <u>https://www.ibm.com/docs/en/mas-cd/mhmpmh-and-p-u/continuous-delivery?topic=deploy-language-support</u>"
        ])

        self.promptForString("Secondary languages", "mas_app_settings_secondary_langs")

    def manageSettingsCP4D(self) -> None:
        if self.getParam("mas_app_channel_manage") in ["8.7.x", "9.0.x"]:
            self.printDescription([
                "Integration with Cognos Analytics provides additional support for reporting features in Maximo Manage, for more information refer to the documentation online: ",
                "    <u>https://ibm.biz/BdMuxs</u>"
            ])
            self.yesOrNo("Enable integration with Cognos Analytics", "cpd_install_cognos")
            self.yesOrNo("Enable integration with Watson Studio Local", "mas_appws_bindings_health_flag")

            if self.getParam("cpd_install_cognos") == "true" or self.getParam("mas_appws_bindings_health_flag") == "true":
                self.configCP4D()

    def manageSettingsOther(self) -> None:
        self.printH2("Maximo Manage Settings - Other")
        self.printDescription([
            "Configure additional settings:",
            "  - Demo data",
            "  - Base and additional languages",
            "  - Server timezone",
            "  - Cognos integration (install Cloud Pak for Data)",
            "  - Watson Studio Local integration (install Cloud Pak for Data)"
        ])

        if self.yesOrNo("Configure Additional Settings"):
            self.manageSettingsDemodata()
            self.manageSettingsTimezone()
            self.manageSettingsLanguages()
            self.manageSettingsCP4D()
