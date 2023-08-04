#!/bin/bash
# Install ROSA Cli
set -e

wget -q https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/rosa-linux.tar.gz?extIdCarryOver=true&intcmp=701f20000012k69AAA&sc_cid=701f2000001Css5AAC
tar -xzf tar xvf rosa-linux.tar.gz
sudo mv rosa /usr/local/bin/rosa
rosa version