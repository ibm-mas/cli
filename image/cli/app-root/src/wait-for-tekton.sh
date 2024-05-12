#!/usr/bin/env bash

# Usage
# -----
# Fail if the pipelinerun failed:
#   wait-for-tekton.sh --type pipelinerun --name mypipelinerun --namespace mynamespace
# Ignore failures in the pipelinerun:
#   wait-for-tekton.sh --type pipelinerun --name mypipelinerun --namespace mynamespace --ignore-failure
# Wait for a taskrun:
#   wait-for-tekton.sh --type taskrun --name mytaskrun --namespace mynamespace


MAX_RETRIES=${MAX_RETRIES:-50}  # Just over 4 hours hours
DELAY=${DELAY:-300}  # 5 minute interval
IGNORE_FAILURE=${IGNORE_FAILURE:-False}  # Return success RC even if pipelinerun failed
TYPE=pipelinerun  # Set whether to wait for a pipelinerun or a taskrun of the given name
while [[ $# -gt 0 ]]
do
  key="$1"
  shift
  case $key in
    --type)
      TYPE=$1
      shift
      ;;
    --name)
      NAME=$1
      shift
      ;;
    --suffix)
      SUFFIX=$1
      shift
      ;;
    --namespace)
      NAMESPACE=$1
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

if [[ -z "$NAME" || -z "$NAMESPACE" ]]; then
  echo "No ${TYPE} defined, nothing to wait for."
  exit 0
fi

if [[ -z "$SUFFIX"] ]]; then
  NAME="${NAME}-${SUFFIX}"
fi
echo "Waiting for ${TYPE}/${NAME} in ${NAMESPACE} to complete ..."

echo ""
echo "Status of ${TYPE}"
echo "------------------------------------------------------------------"
oc -n ${NAMESPACE} get ${TYPE}/${NAME}

echo ""
echo "Waiting for ${TYPE}/${NAME} to complete"
echo "------------------------------------------------------------------"
# oc -n ${NAMESPACE} wait ${TYPE}/${NAME} --for=condition=Succeeded --timeout=24h

COMPLETION_TIME=$(oc -n ${NAMESPACE} get ${TYPE}/${NAME} -o jsonpath='{.status.completionTime}')
RETRIES_USED=0
while [[ "$COMPLETION_TIME" == "" && "$RETRIES_USED" -lt "$MAX_RETRIES" ]]; do
  echo "[$RETRIES_USED/$MAX_RETRIES] ${TYPE}/${NAME} is still running.  Waiting ${DELAY} seconds before checking again"
  sleep $DELAY
  COMPLETION_TIME=$(oc -n ${NAMESPACE} get ${TYPE}/${NAME} -o jsonpath='{.status.completionTime}')
  RETRIES_USED=$((RETRIES_USED + 1))
done

echo "Completion Time = $COMPLETION_TIME"
echo "Retries Used    = $RETRIES_USED"
RESULT=$(oc -n ${NAMESPACE} get ${TYPE}/$NAME -o jsonpath='{.status.conditions[0].status}')

if [[ "$RESULT" == "True" ]]; then
  echo "Result          = ${TYPE} completed successfully"
  exit 0
elif [[ "$IGNORE_FAILURE" == "True" || "$IGNORE_FAILURE" == "true" ]]; then
  echo "Result          = ${TYPE} failed (ignored)"
  exit 0
else
  echo "Result          = ${TYPE} failed"
  exit 1
fi
