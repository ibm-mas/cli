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
from base64 import b64encode
from json import loads


class ConfigGeneratorMixin():
    def generateJDBCCfg(self, instanceId: str, scope: str, destination: str, appId: str = "", workspaceId: str = "") -> None:
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

    def generateAiCfg(self, instanceId: str, scope: str, destination: str, workspaceId: str = "") -> None:
        templateFile = path.join(self.templatesDir, "aicfg.yml.j2")
        with open(templateFile) as tFile:
            template = Template(tFile.read())

        if scope == "workspace":
            assert workspaceId != ""

        name = self.promptForString("Configuration Display Name")
        url = self.promptForString("AI Service URL")
        tenantId = self.promptForString("AI Service Tenant ID")
        apikey = self.promptForString("AI Service API Key", isPassword=True)

        enabled = self.yesOrNo("Enable AI Configuration")
        metaAgentEnabled = self.yesOrNo("Enable Meta Agent")
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

            cfg_display_name=name,

            ai_url=url,
            ai_tenant_id=tenantId,
            ai_apikey=apikey,
            ai_enabled=enabled,
            meta_agent_enabled=metaAgentEnabled,

            ai_ssl_enabled=sslEnabled,
            ai_cert_local_file_content=certLocalFileContent
        )

        with open(destination, 'w') as f:
            f.write(cfg)
            f.write('\n')

    def generateMongoCfg(self, instanceId: str, destination: str) -> None:
        templateFile = path.join(self.templatesDir, "suite_mongocfg.yml.j2")

        with open(templateFile) as tFile:
            template = Template(tFile.read())

        name = self.promptForString("Configuration Display Name")
        hosts = self.promptForString("MongoDb Hosts (comma-separated list)")

        username = self.promptForString("MongoDb Username")
        password = self.promptForString("MongoDb Password", isPassword=True)
        encoded_username = b64encode(username.encode('ascii')).decode("ascii")
        encoded_password = b64encode(password.encode('ascii')).decode("ascii")
        sslCertFile = self.promptForFile("Path to certificate file")
        with open(sslCertFile) as cFile:
            certLocalFileContent = cFile.read()

        cfg = template.render(
            mas_instance_id=instanceId,
            cfg_display_name=name,
            mongodb_hosts=hosts,
            mongodb_admin_username=encoded_username,
            mongodb_admin_password=encoded_password,
            mongodb_ca_pem_local_file=certLocalFileContent
        )

        with open(destination, 'w') as f:
            f.write(cfg)
            f.write('\n')

    def generateFacilitiesCfg(self, destination: str) -> None:
        templateFile = path.join(self.templatesDir, "facilities-configs.yml.j2")

        with open(templateFile) as tFile:
            template = Template(tFile.read())

        dwfagents = self.getParam("mas_ws_facilities_dwfagents")
        maxconnpoolsize = self.getParam("mas_ws_facilities_db_maxconnpoolsize")
        userfiles_size = self.getParam("mas_ws_facilities_storage_userfiles_size")
        log_size = self.getParam("mas_ws_facilities_storage_log_size")
        cfg = template.render(
            mas_instance_id=self.getParam("mas_instance_id"),
            mas_ws_facilities_storage_log_size=log_size if log_size != "" else 30,
            mas_ws_facilities_storage_userfiles_size=userfiles_size if userfiles_size != "" else 50,
            mas_ws_facilities_db_maxconnpoolsize=maxconnpoolsize if maxconnpoolsize != "" else 200,
            mas_ws_facilities_dwfagents=loads(dwfagents) if dwfagents != '' else ''
        )

        with open(destination, 'w') as f:
            f.write(cfg)
            f.write('\n')
