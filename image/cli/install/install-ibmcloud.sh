#!/bin/bash

# Install IBM CLoud CLI with container-service plugin
set -e

wget -q https://download.clis.cloud.ibm.com/ibm-cloud-cli/2.3.0/IBM_Cloud_CLI_2.3.0_amd64.tar.gz
tar -xvzf IBM_Cloud_CLI_2.3.0_amd64.tar.gz
mv Bluemix_CLI/bin/ibmcloud /usr/local/bin/
rm -rf Bluemix_CLI IBM_Cloud_CLI_2.3.0_amd64.tar.gz
ibmcloud plugin repo-plugins -r 'IBM Cloud'
ibmcloud plugin install container-service
