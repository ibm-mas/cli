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

# Capture the playbook name for notification
PLAYBOOK_NAME="$1"

# Send Slack start notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-start \
    --task-name "$PLAYBOOK_NAME" \
    --pipeline-name "${PIPELINE_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
fi

ansible-playbook ibm.mas_devops."$@"
rc=$?

# Send Slack completion notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-complete \
    --rc $rc \
    --task-name "$PLAYBOOK_NAME" \
    --pipeline-name "${PIPELINE_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
fi

python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
