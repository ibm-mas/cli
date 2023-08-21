#!/bin/bash

# Install yq CLI
set -e

curl -L  "https://github.com/mikefarah/yq/releases/download/v4.35.1/yq_linux_amd64"  > yq
mv yq /usr/local/bin/

yq --version
