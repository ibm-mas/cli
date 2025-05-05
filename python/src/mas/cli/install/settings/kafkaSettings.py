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


class KafkaSettingsMixin():
    def configKafka(self) -> None:
        if self.installIoT:
            self.printH1("Configure Kafka")
            self.printDescription([
                "Maximo IoT requires a shared system-scope Kafka instance",
                "Supported Kafka providers: Strimzi, Red Hat AMQ Streams, IBM Cloud Event Streams and AWS MSK",
                "You may also choose to configure MAS to use an existing Kafka instance by providing a pre-existing configuration file"
            ])
            if self.yesOrNo("Create system Kafka instance using one of the supported providers"):
                self.setParam("kafka_action_system", "install")

                if self.showAdvancedOptions:
                    self.printDescription([
                        "",
                        "Kafka Provider:",
                        "  1. Strimzi (opensource)",
                        "  2. Red Hat AMQ Streams (requires a separate license)",
                        "  3. IBM Cloud Event Streams (paid IBM Cloud service)",
                        "  4. AWS MSK (paid AWS service)"
                    ])
                    self.promptForListSelect("Select Kafka provider", ["strimzi", "redhat", "ibm", "aws"], "kafka_provider")
                else:
                    self.setParam("kafka_provider", "strimzi")

                if self.getParam("kafka_provider") == "strimzi":
                    self.printDescription([
                        "",
                        "Strimzi: Cluster Version",
                        "The version of the Strimzi operator available on your cluster will determine the supported versions of Kafka that can be deployed.",
                        " - If you are using the latest available operator catalog then the default version below can be accepted",
                        " - If you are using older operator catalogs (e.g. in a disconnected install) you should confirm the supported versions in your OperatorHub"
                    ])
                    if self.showAdvancedOptions:
                        self.promptForString("Strimzi namespace", "kafka_namespace", default="strimzi")
                    self.promptForString("Kafka version", "kafka_version", default="3.9.0")

                elif self.getParam("kafka_provider") == "redhat":
                    self.printDescription([
                        "",
                        "Red Hat AMQ Streams: Cluster Version",
                        "The version of the Red Hat AMQ Streams operator available on your cluster will determine the supported versions of Kafka that can be deployed.",
                        " - If you are using the latest available operator catalog then the default version below can be accepted",
                        " - If you are using older operator catalogs (e.g. in a disconnected install) you should confirm the supported versions in your OperatorHub"
                    ])
                    self.promptForString("Install namespace", "kafka_namespace", default="amq-streams")
                    self.promptForString("Kafka version", "kafka_version", default="3.8.0")

                elif self.getParam("kafka_provider") == "ibm":
                    print()
                    self.promptForString("IBM Cloud API Key", "ibmcloud_apikey", isPassword=True)
                    self.promptForString("IBM Event Streams resource group" "eventstreams_resourcegroup", default="Default")
                    self.promptForString("IBM Event Streams instance name", "eventstreams_name", default=f"eventstreams-{self.getParam('mas_instance_id')}")
                    self.promptForString("IBM Event Streams location", "eventstreams_location", default="us-east")

                elif self.getParam("kafka_provider") == "aws":
                    self.printDescription([
                        "",
                        "While provisioning the AWS MSK instance, you will be required to provide the AWS Virtual Private Cloud ID and subnet details",
                        "where your instance will be deployed to properly configure inbound and outbound connectivity.",
                        "You should be able to find these information inside your VPC and subnet configurations in the target AWS account.",
                        "For more details about AWS subnet/CIDR configuration, refer: <Orange><u>https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html</u></Orange>"
                    ])
                    self.promptForString("AWS Access Key ID", "aws_access_key_id", isPassword=True)
                    self.promptForString("AWS Secret Access Key" "aws_secret_access_key", isPassword=True)
                    self.promptForString("AWS Region", "aws_region", default="us-east-1")
                    self.promptForString("Virtual Private Cloud (VPC) ID", "vpc_id")
                    self.promptForString("MSK Instance Username", "aws_kafka_user_name", default="masuser")
                    self.promptForString("MSK Instance Password", "aws_kafka_user_password", isPassword=True)
                    self.promptForString("MSK Instance Type", "aws_msk_instance_type", default="kafka.m5.large")
                    self.promptForString("MSK Total Number of Broker Nodes", "aws_msk_instance_number", default="3")
                    self.promptForString("MSK Storage Size (in GB)", "aws_msk_volume_size", defauklt="100")
                    self.promptForString("Availability Zone 1 CIDR", "aws_msk_cidr_az1")
                    self.promptForString("Availability Zone 2 CIDR", "aws_msk_cidr_az2")
                    self.promptForString("Availability Zone 3 CIDR", "aws_msk_cidr_az3")
                    self.promptForString("Ingress CIDR", "aws_msk_ingress_cidr")
                    self.promptForString("Egress CIDR", "aws_msk_egress_cidr")
            else:
                self.setParam("kafka_action_system", "byo")
                self.selectLocalConfigDir()
                instanceId = self.getParam('mas_instance_id')

                # Check if a configuration already exists
                kafkaCfgFile = path.join(self.localConfigDir, f"kafka-{instanceId}-system.yaml")
                print_formatted_text(f"Searching for system kafka configuration file in {kafkaCfgFile} ...")
                if path.exists(kafkaCfgFile):
                    print_formatted_text(f"Provided Kafka configuration file {kafkaCfgFile} will be applied")
                else:
                    self.fatalError(f"Kafka configuration file does not exist: '{kafkaCfgFile}'.  In order to continue, provide an existing Kafka configuration file or choose one of the supported Kafka providers to be installed")
