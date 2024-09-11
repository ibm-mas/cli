# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from os import path
from prompt_toolkit import print_formatted_text

class MongodbSettingsMixin():
    def configMongoDb(self) -> None:

         self.printDescription([
            "The installer can setup mongoce in your OpenShift cluster (available only for amd64 )or you may choose to configure MAS to use an existing mongodb"
         ])
         self.printH1("Configure MongoDb")
         self.promptForString("Install namespace", "mongodb_namespace", default="mongoce")

         if self.yesOrNo("CConfigure MongoDb in your OpenShift cluster"):
            self.setParam("mongo_action_system", "install")
         else:
            mongodb_namespace = 'mongoce'
            self.setParam("mongo_action_system", "byo")
            self.selectLocalConfigDir()

            # Check if a configuration already exists before creating a new one
            mongoCfgFile = path.join(self.localConfigDir, f"mongo-{mongodb_namespace}.yaml")
            print_formatted_text(f"Searching for system database configuration file in {mongoCfgFile} ...")
            if path.exists(mongoCfgFile):
                if self.yesOrNo(f"System database configuration file 'mongo-{instanceId}-system.yam' already exists.  Do you want to generate a new one"):
                    self.generateMongoCfg(instanceId=instanceId, destination=mongoCfgFile)
            else:
                print_formatted_text(f"Expected file ({mongoCfgFile}) was not found, generating a valid system database configuration file now ...")
                self.generateMongoCfg(instanceId=instanceId,destination=mongoCfgFile)