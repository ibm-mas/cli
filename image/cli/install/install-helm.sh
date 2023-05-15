#!/bin/bash

# Install Helm for argocd sidecar
set -e

curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
chown default:root /usr/local/bin/helm
chmod  g=u /usr/local/bin/helm
chmod 777 /usr/local/bin/helm