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

echo "DEVOPS_SUITE_NAME: $DEVOPS_SUITE_NAME"
echo "DEVOPS_BUILD_NUMBER: $DEVOPS_BUILD_NUMBER"
echo "ANSIBLE_DEVOPS_VERSION: $ANSIBLE_DEVOPS_VERSION"
echo "PIPELINE_NAME: $PIPELINE_NAME"
echo "PIPELINERUN_NAME: $PIPELINERUN_NAME"
echo "DEVOPS_ENVIRONMENT: $DEVOPS_ENVIRONMENT"

export ROLE_NAME=$1
shift

# Send Slack start notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-start \
    --task-name "$DEVOPS_SUITE_NAME" \
    --pipeline-name "${PIPELINERUN_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
  echo "# ----------------- Sending Start Notification Suite: $DEVOPS_SUITE_NAME | pipeline: $PIPELINE_NAME($PIPELINERUN_NAME) | Instance id: $DEVOPS_ENVIRONMENT -------------------- #"
fi

ansible-playbook ibm.mas_devops.run_role $@
rc=$?

# Send Slack completion notification if configured
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_CHANNEL" ]; then
  python3 /opt/app-root/bin/mas-devops-notify-slack \
    --action ansible-complete \
    --rc $rc \
    --task-name "$DEVOPS_SUITE_NAME" \
    --pipeline-name "${PIPELINERUN_NAME:-unknown}" \
    --instance-id "${DEVOPS_ENVIRONMENT:-}" || true
    echo "# ----------------- Sending Stop Notification Suite: $DEVOPS_SUITE_NAME | pipeline: $PIPELINE_NAME($PIPELINERUN_NAME) | Instance id: $DEVOPS_ENVIRONMENT -------------------- #"
fi

python3 /opt/app-root/src/save-junit-to-mongo.py
exit $rc
