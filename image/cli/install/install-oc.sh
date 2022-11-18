#!/bin/bash

# Install OpenShift CLI 4.10.41
set -e

wget -q https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.10.41/openshift-client-linux.tar.gz
tar -zxf openshift-client-linux.tar.gz
mv oc /usr/local/bin/
mv kubectl /usr/local/bin/
rm -rf openshift-client-linux.tar.gz
