#!/bin/bash

if [ -e "/workspace/additional-configs" ]; then
  cp /workspace/additional-configs/* /workspace/configs/
fi

if [ -e "/workspace/entitlement/entitlement.lic" ]; then
  cp /workspace/entitlement/entitlement.lic /workspace/configs/entitlement.lic
fi

# Debug
source /opt/app-root/src/env.sh
oc whoami
oc auth can-i --list

ansible-playbook "$@"
rc=$?
python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
