#!/usr/bin/env bash

# Usage
# -----
# Fail if the pipelinerun failed:
#   wait-for-pipelinerun.sh pipelinerunname namespace True
# Ignore failures in the pipelinerun:
#   wait-for-pipelinerun.sh pipelinerunname namespace False

PIPELINERUN_NAME=$1
NAMESPACE=$2
IGNORE_FAILURE=$3
echo "Waiting for pipelinerun/${PIPELINERUN_NAME} in ${NAMESPACE} to complete ..."

echo ""
echo "Status of pipelinerun"
echo "------------------------------------------------------------------"
oc -n ${NAMESPACE} get pipelinerun/${PIPELINERUN_NAME}

echo ""
echo "Waiting for pipelinerun/${PIPELINERUN_NAME} to complete"
echo "------------------------------------------------------------------"
# oc -n ${NAMESPACE} wait pipelinerun/${PIPELINERUN_NAME} --for=condition=Succeeded --timeout=24h

COMPLETION_TIME=$(oc -n ${NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.completionTime}')
# 2 minutes * 720 = ~24 hours
MAX_RETRIES=720
RETRIES_USED=0
DELAY=120
while [[ "$COMPLETION_TIME" == "" && "$RETRIES_USED" -lt "$MAX_RETRIES" ]]; do
  echo "[$RETRIES_USED/$MAX_RETRIES] pipelinerun/$PIPELINERUN_NAME is still running.  Waiting $DELAY seconds before checking again"
  sleep $DELAY
  COMPLETION_TIME=$(oc -n ${NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.completionTime}')
  RETRIES_USED=$((RETRIES_USED + 1))
done

echo "Completion Time = $COMPLETION_TIME"
echo "Retries Used    = $RETRIES_USED"
RESULT=$(oc -n ${NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.conditions[0].status}')

if [[ "$RESULT" == "True" ]]; then
  echo "Result          = PipelineRun completed successfully"
  exit 0
elif [[ "$IGNORE_FAILURE" == "True" ]]; then
  echo "Result          = PipelineRun failed (ignored)"
  exit 0
else
  echo "Result          = PipelineRun failed"
  exit 1
fi
