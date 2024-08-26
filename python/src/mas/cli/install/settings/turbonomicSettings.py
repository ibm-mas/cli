# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from mas.devops.mas import isAirgapInstall

class TurbonomicSettingsMixin():

    def configTurbonomic(self) -> None:
        self.printH1("Configure Turbonomic")
        self.printDescription([
            "The IBM Turbonomic hybrid cloud cost optimization platform allows you to eliminate this guesswork with solutions that save time and optimize costs",
            " - Learn more: <u>https://www.ibm.com/products/turbonomic</u>"
        ])

        if isAirgapInstall(self.dynamicClient):
            self.printHighlight("The Turbonomic Kubernetes Operator does not support disconnected installation at this time")
        elif self.yesOrNo("Configure IBM Turbonomic integration"):
            self.promptForString("Turbonomic Target Name", "turbonomic_target_name")
            self.promptForString("Turbonomic Server URL", "turbonomic_server_url")
            self.promptForString("Turbonomic Server Version", "turbonomic_server_version")
            self.promptForString("Turbonomic Username", "turbonomic_username")
            self.promptForString("Turbonomic Password", "turbonomic_password", isPassword=True)
