#!/usr/bin/env bash

# Usage
# -----
# Fail if the pipelinerun failed:
#   wait-for-pipelinerun.sh --name mypipelinerun --namespace mynamespace
# Ignore failures in the pipelinerun:
#   wait-for-pipelinerun.sh --name mypipelinerun --namespace mynamespace --ignore-failure


MAX_RETRIES=50  # Just over 4 hours hours
DELAY=300  # 5 minute interval
while [[ $# -gt 0 ]]
do
  key="$1"
  shift
  case $key in
    --name)
      PIPELINERUN_NAME=$1
      shift
      ;;
    --namespace)
      PIPELINERUN_NAMESPACE=$1
      shift
      ;;
    --max-retries)
      MAX_RETRIES=$1
      shift
      ;;
    --delay)
      DELAY=$1
      shift
      ;;
    --ignore-failure)
      IGNORE_FAILURE=True
      ;;
    *)
      # Unknown option
      echo "Usage Error: Unsupported option \"${key}\""
      exit 1
      ;;
  esac
done

echo "Waiting for pipelinerun/${PIPELINERUN_NAME} in ${PIPELINERUN_NAMESPACE} to complete ..."

echo ""
echo "Status of pipelinerun"
echo "------------------------------------------------------------------"
oc -n ${PIPELINERUN_NAMESPACE} get pipelinerun/${PIPELINERUN_NAME}

echo ""
echo "Waiting for pipelinerun/${PIPELINERUN_NAME} to complete"
echo "------------------------------------------------------------------"
# oc -n ${PIPELINERUN_NAMESPACE} wait pipelinerun/${PIPELINERUN_NAME} --for=condition=Succeeded --timeout=24h

COMPLETION_TIME=$(oc -n ${PIPELINERUN_NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.completionTime}')
RETRIES_USED=0
while [[ "$COMPLETION_TIME" == "" && "$RETRIES_USED" -lt "$MAX_RETRIES" ]]; do
  echo "[$RETRIES_USED/$MAX_RETRIES] pipelinerun/$PIPELINERUN_NAME is still running.  Waiting $DELAY seconds before checking again"
  sleep $DELAY
  COMPLETION_TIME=$(oc -n ${PIPELINERUN_NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.completionTime}')
  RETRIES_USED=$((RETRIES_USED + 1))
done

echo "Completion Time = $COMPLETION_TIME"
echo "Retries Used    = $RETRIES_USED"
RESULT=$(oc -n ${PIPELINERUN_NAMESPACE} get pipelinerun/$PIPELINERUN_NAME -o jsonpath='{.status.conditions[0].status}')

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
