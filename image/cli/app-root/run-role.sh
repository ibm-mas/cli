#!/bin/bash

if [ -e "/workspace/additional-configs" ]; then
  cp /workspace/additional-configs/* /workspace/configs/
fi

source /opt/app-root/src/copy-certificates.sh
source /opt/app-root/src/env.sh

# Useful for debugging permission issues
# oc whoami
# oc auth can-i --list

export ROLE_NAME=$1
export ANSIBLE_DEVOPS_VERSION=$(grep -oP '(?<="version": ")[^"]*' $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops/MANIFEST.json) # get ibm.mas_devops version from manifest.json
ansible-playbook ibm.mas_devops.run_role
rc=$?
python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
