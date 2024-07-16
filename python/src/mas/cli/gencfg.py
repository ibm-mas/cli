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
from jinja2 import Template

class ConfigGeneratorMixin():
    def generateJDBCCfg(
            self,
            instanceId: str,
            scope: str,
            destination: str,
            appId: str="",
            workspaceId: str="") -> None:

        templateFile = path.join(self.templatesDir, "jdbccfg.yml.j2")
        with open(templateFile) as tFile:
            template = Template(tFile.read())

        if scope == "workspace-application":
            assert appId != ""
            assert workspaceId != ""

        name = self.promptForString("Configuration Display Name")
        url = self.promptForString("JDBC Connection String")

        username = self.promptForString("JDBC Username")
        password = self.promptForString("JDBC Password", isPassword=True)

        sslEnabled = self.yesOrNo("Enable SSL Connection")

        if sslEnabled:
            sslCertFile = self.promptForFile("Path to certificate file")
            with open(sslCertFile) as cFile:
                certLocalFileContent = cFile.read()
        else:
            certLocalFileContent = ""

        cfg = template.render(
            scope=scope,

            mas_instance_id=instanceId,
            mas_workspace_id=workspaceId,
            mas_application_id=appId,

            cfg_display_name=name,

            jdbc_url=url,
            jdbc_username=username,
            jdbc_password=password,

            jdbc_ssl_enabled=sslEnabled,
            jdbc_cert_local_file_content=certLocalFileContent
        )

        with open(destination, 'w') as f:
            f.write(cfg)
            f.write('\n')
