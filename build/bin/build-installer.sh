#!/bin/bash
set -e

if [ "$DEV_MODE" != "true" ]; then
  source ${GITHUB_WORKSPACE}/build/bin/.env.sh
  source ${GITHUB_WORKSPACE}/build/bin/.functions.sh
else
  export VERSION=localdev
  export GITHUB_WORKSPACE=$(pwd)
fi

cd $GITHUB_WORKSPACE/bin
tar -czvf $GITHUB_WORKSPACE/ibm-mas-installer-$VERSION.tgz --directory $GITHUB_WORKSPACE/bin *
