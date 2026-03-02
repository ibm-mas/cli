# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from typing import TYPE_CHECKING, Dict, List
from os import path
from prompt_toolkit import print_formatted_text


if TYPE_CHECKING:
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.validation import Validator


class MongoDbSettingsMixin():
    if TYPE_CHECKING:
        # Attributes from BaseApp and other mixins
        params: Dict[str, str]
        architecture: str | None
        showAdvancedOptions: bool
        localConfigDir: str | None

        # Methods from BaseApp
        def setParam(self, param: str, value: str) -> None:
            ...

        def getParam(self, param: str) -> str:
            ...

        # Methods from PrintMixin
        def printH1(self, message: str) -> None:
            ...

        def printDescription(self, content: List[str]) -> None:
            ...

        # Methods from PromptMixin
        def yesOrNo(self, message: str, param: str | None = None) -> bool:
            ...

        def promptForString(
            self,
            message: str,
            param: str | None = None,
            default: str = "",
            isPassword: bool = False,
            validator: Validator | None = None,
            completer: WordCompleter | None = None
        ) -> str:
            ...

        # Methods from other mixins
        def selectLocalConfigDir(self) -> None:
            ...

        def generateMongoCfg(self, instanceId: str, destination: str) -> None:
            ...

    def configMongoDb(self) -> None:
        self.printH1("Configure MongoDb")
        self.printDescription([
            "The installer can setup mongoce in your OpenShift cluster (available only for amd64) or you may choose to configure MAS to use an existing mongodb"
        ])

        if (self.architecture != "s390x" and self.architecture != "ppc64le") and self.yesOrNo("Create MongoDb cluster using MongoDb Community Edition Operator"):
            if self.showAdvancedOptions:
                self.promptForString("MongoDb namespace", "mongodb_namespace", default="mongoce")
            else:
                # Even though "" works as the default, we use this value to contruct other values so we need to explicitly set it
                self.setParam("mongodb_namespace", "mongoce")

            self.setParam("mongodb_action", "install")
            self.setParam("sls_mongodb_cfg_file", f"/workspace/configs/mongo-{self.getParam('mongodb_namespace')}.yml")
        else:
            self.setParam("mongodb_action", "byo")
            self.setParam("sls_mongodb_cfg_file", "/workspace/additional-configs/mongodb-system.yaml")
            self.selectLocalConfigDir()

            instanceId = self.getParam('mas_instance_id')
            # Check if a configuration already exists before creating a new one
            assert self.localConfigDir is not None, "localConfigDir must be set"
            mongoCfgFile = path.join(self.localConfigDir, "mongodb-system.yaml")

            print_formatted_text(f"Searching for system mongodb configuration file in {mongoCfgFile} ...")
            if path.exists(mongoCfgFile):
                if self.yesOrNo("System mongodb configuration file 'mongodb-system.yaml' already exists.  Do you want to generate a new one"):
                    self.generateMongoCfg(instanceId=instanceId, destination=mongoCfgFile)
            else:
                print_formatted_text(f"Expected file ({mongoCfgFile}) was not found, generating a valid system mongodb configuration file now ...")
                self.generateMongoCfg(instanceId=instanceId, destination=mongoCfgFile)
