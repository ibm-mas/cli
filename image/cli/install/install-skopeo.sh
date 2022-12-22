#!/bin/bash

# Install skopeo & cloudctl & hostname (needed by cloudctl) & httpd-tools (needed for htpasswd cmd)
set -e

dnf install skopeo hostname httpd-tools -y
dnf clean all
wget -q https://github.com/IBM/cloud-pak-cli/releases/download/v3.17.0/cloudctl-linux-amd64.tar.gz
tar -xf cloudctl-linux-amd64.tar.gz
mv cloudctl-linux-amd64 /usr/bin/cloudctl
rm cloudctl-linux-amd64.tar.gz
