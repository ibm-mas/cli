#!/usr/bin/env bash

# Usage
# -----
# Wait for the configmap to have the required key exist:
#   wait-for-configmap.sh --namespace mynamespace --name myconfigmap --key key1
# Wait for the configmap to have the required value set in the key:
#   wait-for-configmap.sh --namespace mynamespace --name myconfigmap --key key1 --target-value value1


MAX_RETRIES=${MAX_RETRIES:-50}  # Just over 4 hours hours
DELAY=${DELAY:-300}  # 5 minute interval
IGNORE_FAILURE=${IGNORE_FAILURE:-False}  # Return success RC even if pipelinerun failed
while [[ $# -gt 0 ]]
do
  key="$1"
  shift
  case $key in
    --namespace)
      NAMESPACE=$1
      shift
      ;;

    # Individual task status configmap
    --name)
      CONFIGMAP_NAME=$1
      shift
      ;;
    --key)
      CONFIGMAP_KEY=$1
      shift
      ;;
    --initial-value)
      CONFIGMAP_INITIAL_VALUE=$1
      shift
      ;;
    --target-value)
      CONFIGMAP_TARGET_VALUE=$1
      shift
      ;;

    # Escape clause configmap
    --escape-name)
      ESCAPE_CONFIGMAP_NAME=$1
      shift
      ;;
    --escape-key)
      ESCAPE_CONFIGMAP_KEY=$1
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

echo ""
echo "Inputs"
echo "------------------------------------------------------------------"
echo "Namespace .................. $NAMESPACE"
echo "Config Map ................. $CONFIGMAP_NAME"
echo "Config Map Key ............. $CONFIGMAP_KEY"
echo "Config Map Initial Value.... $CONFIGMAP_INITIAL_VALUE"
echo "Config Map Target Value..... $CONFIGMAP_TARGET_VALUE"
echo "Escape Config Map .......... $ESCAPE_CONFIGMAP_NAME"
echo "Escape Config Map Key ...... $ESCAPE_CONFIGMAP_KEY"
echo "Max Retries ................ $MAX_RETRIES"
echo "Delay ...................... $DELAY"
echo "Ignore Failure ............. $IGNORE_FAILURE"
echo ""

if [[ -z "$CONFIGMAP_NAME" || -z "$CONFIGMAP_KEY" || -z "$NAMESPACE" ]]; then
  echo "NAMESPACE, CONFIGMAP_NAME, and CONFIGMAP_KEY must all be defined, there is nothing to wait for."
  exit 0
fi

echo ""
echo "Status of ${CONFIGMAP_NAME}"
echo "------------------------------------------------------------------"
oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o yaml 2> /dev/null
CM_EXISTS=$?
echo

if [[ -n "$CONFIGMAP_INITIAL_VALUE" ]]; then
  if [[ "$CM_EXISTS" == "0" ]]; then
    echo "Updating existing configmap to set initial value of ${CONFIGMAP_INITIAL_VALUE}"
    oc -n ${NAMESPACE} patch configmap/${CONFIGMAP_NAME} -p "{\"data\": { \"${CONFIGMAP_KEY}\": \"${CONFIGMAP_INITIAL_VALUE}\" }}"
  else
    echo "Creating new configmap with initial value of ${CONFIGMAP_INITIAL_VALUE}"
    oc -n ${NAMESPACE} create configmap ${CONFIGMAP_NAME} --from-literal=${CONFIGMAP_KEY}=c${CONFIGMAP_INITIAL_VALUE}
  fi
fi

echo
echo "Waiting for configmap/${CONFIGMAP_NAME} in ${NAMESPACE} to contain key '${CONFIGMAP_KEY}' ..."
KEY_VALUE=$(oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o jsonpath="{.data.${CONFIGMAP_KEY}}" 2> /dev/null)
RETRIES_USED=1
while [[ "$KEY_VALUE" == "" && "$RETRIES_USED" -le "$MAX_RETRIES" ]]; do
  echo "[$RETRIES_USED/$MAX_RETRIES] ${CONFIGMAP_KEY} does not yet exist in configmap/${CONFIGMAP_NAME}.  Waiting ${DELAY} seconds before checking again"
  sleep $DELAY
  KEY_VALUE=$(oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o jsonpath="{.data.${CONFIGMAP_KEY}}" 2> /dev/null)

  if [[ "${KEY_VALUE}" == "" && -n "${ESCAPE_CONFIGMAP_NAME}" ]]; then
    # Check if the entire install pipeline has stopped so we can exit early
    ESCAPE_VALUE=$(oc -n ${NAMESPACE} get configmap/${ESCAPE_CONFIGMAP_NAME} -o jsonpath="{.data.${ESCAPE_CONFIGMAP_KEY}}" 2> /dev/null)
    if [[ "$ESCAPE_VALUE" != "" ]]; then
      echo "[$RETRIES_USED/$MAX_RETRIES] configmap/${ESCAPE_CONFIGMAP_NAME} indicates that the pipeline we are synchronizing with has already completed: ${ESCAPE_VALUE}"
      # Force an early exit from the loop
      RETRIES_USED=$MAX_RETRIES
    else
      echo "[$RETRIES_USED/$MAX_RETRIES] configmap/${ESCAPE_CONFIGMAP_NAME} indicates that the pipeline we are synchronizing with is still alive: '${ESCAPE_VALUE}'"
    fi
  fi
    RETRIES_USED=$((RETRIES_USED + 1))
done

echo
if [[ "$KEY_VALUE" != "" && -z "${CONFIGMAP_TARGET_VALUE}" ]]; then
  echo "Located key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME}"
  exit 0
elif [[ "$KEY_VALUE" == "" && -z "${CONFIGMAP_TARGET_VALUE}" ]]; then
  if [[ "$IGNORE_FAILURE" == "True" || "$IGNORE_FAILURE" == "true" ]]; then
    echo "Failed to locate key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME} (ignored)"
    exit 0
  else
    echo "Failed to locate key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME}"
    exit 1
  fi
else
  # It is guaranteed, at this point, that CONFIGMAP_TARGET_VALUE has a value different from empty/null
  echo "Waiting for configmap/${CONFIGMAP_NAME} in ${NAMESPACE} to contain key '${CONFIGMAP_KEY}' with value '${CONFIGMAP_TARGET_VALUE}' ..."
  KEY_VALUE=$(oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o jsonpath="{.data.${CONFIGMAP_KEY}}" 2> /dev/null)
  # Empty test must be checked besides target value and key value due to the wildcard comparison.
  # Any value is contained in an ** result, but we do not want that
  while [[ ("$KEY_VALUE" == "" || "${CONFIGMAP_TARGET_VALUE}" != *"$KEY_VALUE"*) && "$RETRIES_USED" -le "$MAX_RETRIES" ]]; do
    echo "[$RETRIES_USED/$MAX_RETRIES] ${CONFIGMAP_KEY}=${KEY_VALUE} does not equal '${CONFIGMAP_TARGET_VALUE}' yet in configmap/${CONFIGMAP_NAME}.  Waiting ${DELAY} seconds before checking again"
    sleep $DELAY
    KEY_VALUE=$(oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o jsonpath="{.data.${CONFIGMAP_KEY}}" 2> /dev/null)

    if [[ "${CONFIGMAP_TARGET_VALUE}" != *"${KEY_VALUE}"* && -n "${ESCAPE_CONFIGMAP_NAME}" ]]; then
      # Check if the entire install pipeline has stopped so we can exit early
      ESCAPE_VALUE=$(oc -n ${NAMESPACE} get configmap/${ESCAPE_CONFIGMAP_NAME} -o jsonpath="{.data.${ESCAPE_CONFIGMAP_KEY}}" 2> /dev/null)
      if [[ "$ESCAPE_VALUE" != "" ]]; then
        echo "[$RETRIES_USED/$MAX_RETRIES] configmap/${ESCAPE_CONFIGMAP_NAME} indicates that the pipeline we are synchronizing with has already completed: ${ESCAPE_VALUE}"
        # Force an early exit from the loop
        RETRIES_USED=$MAX_RETRIES
      else
        echo "[$RETRIES_USED/$MAX_RETRIES] configmap/${ESCAPE_CONFIGMAP_NAME} indicates that the pipeline we are synchronizing with is still alive: '${ESCAPE_VALUE}'"
      fi
    fi
    RETRIES_USED=$((RETRIES_USED + 1))
  done

  echo
  # Empty test must be checked besides target value and key value due to the wildcard comparison.
  # Any value is contained in an ** result, but we do not want that
  if [[ "$KEY_VALUE" != "" && "${CONFIGMAP_TARGET_VALUE}" == *"$KEY_VALUE"* ]]; then
    echo "Located key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME} with value '${CONFIGMAP_TARGET_VALUE}'"
    exit 0
  else
    if [[ "$IGNORE_FAILURE" == "True" || "$IGNORE_FAILURE" == "true" ]]; then
      echo "Failed to locate key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME} with value '${CONFIGMAP_TARGET_VALUE}' (ignored)"
      exit 0
    else
      echo "Failed to locate key ${CONFIGMAP_KEY} in configmap/${CONFIGMAP_NAME} with value '${CONFIGMAP_TARGET_VALUE}'"
      exit 1
    fi
  fi
fi
