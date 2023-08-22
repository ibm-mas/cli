#!/bin/bash

# Install yq CLI
set -e

mkdir -p /opt/mikefarah/bin
curl -L  "https://github.com/mikefarah/yq/releases/download/v4.35.1/yq_linux_amd64"  > /opt/mikefarah/bin/yq
chmod 755 /opt/mikefarah/bin/yq

/opt/mikefarah/bin/yq --version
