#!/bin/bash

# 1. Configure Junit report
# -----------------------------------------------------------------------------
export JUNIT_OUTPUT_DIR=/opt/app-root/ansible/junit/
export JUNIT_HIDE_TASK_ARGUMENTS=true
export JUNIT_TASK_CLASS=true


# 2. Connect to the local cluster
# -----------------------------------------------------------------------------
export K8S_AUTH_HOST=https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT_HTTPS
export K8S_AUTH_VERIFY_SSL=false
export K8S_AUTH_API_KEY=$(cat /run/secrets/kubernetes.io/serviceaccount/token)


# 3. Export everything in /workspace/settings
# -----------------------------------------------------------------------------
echo "Export all env vars defined in /workspace/settings"
for file in /workspace/settings/*; do
  if [[ -f $file ]]; then
    echo "Exporting $file"
    # Temporarily turn off glob, otherwise any wildcard characters (*) in the
    # vars will be expanded to matching filenames.
    set -f
    export $(basename $file)="$(cat $file)"
    set +f
  fi
done


# 4. Print out all env vars
# -----------------------------------------------------------------------------
# This is great for debugging problems, but generally should not be left enabled
#
# If the logging in the Ansible code is not sufficient to understand the issue
# then you need to ADDRESS THE LACK OF LOGGING IN THE ANSIBLE CODE
# env | sort
