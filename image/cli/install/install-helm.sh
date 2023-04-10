#!/bin/bash

# Install Helm for argocd sidecar
set -e

curl -L https://mirror.openshift.com/pub/openshift-v4/clients/helm/latest/helm-linux-amd64 -o /usr/local/bin/helm
chown default:root /usr/local/bin/helm
chmod -R g=u /usr/local/bin/helm