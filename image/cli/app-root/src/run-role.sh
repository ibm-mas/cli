#!/bin/bash

if [ -e "/workspace/additional-configs" ]; then
  cp /workspace/additional-configs/* /workspace/configs/
fi

source /opt/app-root/src/copy-certificates.sh
source /opt/app-root/src/env.sh

# Useful for debugging permission issues
# oc whoami
# oc auth can-i --list

python3 /opt/app-root/src/register-start.py

export ROLE_NAME=$1
shift

# Send Slack start notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-start \
    --task-name "$ROLE_NAME" \
    # --pipeline-name "${PIPELINE_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
fi

ansible-playbook ibm.mas_devops.run_role $@
rc=$?

# Send Slack completion notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-complete \
    --rc $rc \
    --task-name "$ROLE_NAME" \
    # --pipeline-name "${PIPELINE_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
fi

python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
