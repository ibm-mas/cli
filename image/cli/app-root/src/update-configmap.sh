#!/usr/bin/env bash

# Usage
# -----
# Wait for the configmap to have the required key exist:
#   wait-for-configmap.sh --namespace mynamespace --name myconfigmap --key key1
# Wait for the configmap to have the required value set in the key:
#   wait-for-configmap.sh --namespace mynamespace --name myconfigmap --key key1 --value value1


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
    --name)
      CONFIGMAP_NAME=$1
      shift
      ;;
    --key)
      CONFIGMAP_KEY=$1
      shift
      ;;
    --value)
      CONFIGMAP_VALUE=$1
      shift
      ;;
    *)
      # Unknown option
      echo "Usage Error: Unsupported option \"${key}\""
      exit 1
      ;;
  esac
done

if [[ -z "$CONFIGMAP_VALUE" || -z "$CONFIGMAP_NAME" || -z "$CONFIGMAP_KEY" || -z "$NAMESPACE" ]]; then
  echo "NAMESPACE, CONFIGMAP_NAME, CONFIGMAP_KEY, and CONFIGMAP_VALUE must all be defined."
  exit 0
fi

echo ""
echo "Status of ${CONFIGMAP_NAME}"
echo "------------------------------------------------------------------"
oc -n ${NAMESPACE} get configmap/${CONFIGMAP_NAME} -o yaml
CM_EXISTS=$?
echo

if [[ "$CM_EXISTS" == "0" ]]; then
  echo "Updating existing configmap to set ${CONFIGMAP_KEY}=${CONFIGMAP_VALUE}"
  oc -n ${NAMESPACE} patch configmap/${CONFIGMAP_NAME} -p "{\"data\": { \"${CONFIGMAP_KEY}\": \"${CONFIGMAP_VALUE}\" }}"
  exit $?
else
  echo "Creating new configmap with ${CONFIGMAP_KEY}=${CONFIGMAP_VALUE}"
  oc -n ${NAMESPACE} create configmap ${CONFIGMAP_NAME} --from-literal=${CONFIGMAP_KEY}=c${CONFIGMAP_VALUE}
  exit $?
fi
