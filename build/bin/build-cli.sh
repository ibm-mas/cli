#!/bin/bash
set -e

if [ "$DEV_MODE" != "true" ]; then
  source ${GITHUB_WORKSPACE}/build/bin/.env.sh
  source ${GITHUB_WORKSPACE}/build/bin/.functions.sh
else
  export VERSION=localdev
  export GITHUB_WORKSPACE=$(pwd)
fi

sed -i "s#VERSION=latest#VERSION=${VERSION}#g" ${GITHUB_WORKSPACE}/image/cli/mascli/mas

cd $GITHUB_WORKSPACE/image/cli/mascli
chmod ug+x $GITHUB_WORKSPACE/image/cli/mascli/mas
chmod ug+x $GITHUB_WORKSPACE/image/cli/mascli/must-gather/*
tar -czvf $GITHUB_WORKSPACE/ibm-mas-cli-$VERSION.tgz --directory $GITHUB_WORKSPACE/image/cli/mascli *
