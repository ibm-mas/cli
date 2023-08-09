#!/bin/bash

if [ -e "/workspace/additional-configs" ]; then
  cp /workspace/additional-configs/* /workspace/configs/
fi

if [ -e "/workspace/entitlement/entitlement.lic" ]; then
  cp /workspace/entitlement/entitlement.lic /workspace/configs/entitlement.lic
fi

source /opt/app-root/src/env.sh

# Useful for debugging permission issues
# oc whoami
# oc auth can-i --list

python3 /opt/app-root/src/register-start.py

ansible-playbook ibm.mas_devops."$@"
rc=$?
python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
