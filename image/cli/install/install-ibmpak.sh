#!/bin/bash

# Install IBM Pak oc addon
set -e

curl -L https://github.com/IBM/ibm-pak-plugin/releases/download/v1.3.1/oc-ibm_pak-linux-amd64.tar.gz -o oc-ibm_pak-linux-amd64.tar.gz
tar -xvf oc-ibm_pak-linux-amd64.tar.gz
mv oc-ibm_pak-linux-amd64 /usr/local/bin/oc-ibm_pak

oc ibm-pak --version
