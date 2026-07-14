#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$DEV_MODE" != "true" ]; then
  source ${GITHUB_WORKSPACE}/build/bin/.env.sh
  source ${GITHUB_WORKSPACE}/build/bin/.functions.sh

  TARGET_DIR=$GITHUB_WORKSPACE/tekton/target

  TASK_FILES=$TARGET_DIR/tasks/*.yaml
  PIPELINE_FILES=$TARGET_DIR/pipelines/*.yaml

  TARGET_FILE=$GITHUB_WORKSPACE/tekton/target/ibm-mas-tekton.yaml
  TARGET_FILE_FVT=$GITHUB_WORKSPACE/tekton/target/ibm-mas-tekton-fvt.yaml
  TARGET_FILE_IN_CLI=$GITHUB_WORKSPACE/image/cli/mascli/templates/ibm-mas-tekton.yaml
  TARGET_FILE_IN_PY=$GITHUB_WORKSPACE/python/src/mas/cli/templates/ibm-mas-tekton.yaml
else
  TARGET_DIR=$DIR/../../tekton/target
  VERSION=${VERSION:-100.0.0-pre.localbuild}

  # Check if we should use OCP internal registry
  if [ "$USE_OCP_REGISTRY" == "true" ]; then
    OCP_PROJECT=${OCP_PROJECT:-$(oc project -q 2>/dev/null)}
    if [ -z "$OCP_PROJECT" ]; then
      echo "Error: Cannot determine OCP project. Please set OCP_PROJECT environment variable or ensure you're logged into OCP."
      exit 1
    fi
    IMAGE_REGISTRY="image-registry.openshift-image-registry.svc:5000"
    IMAGE_REFERENCE="${IMAGE_REGISTRY}/${OCP_PROJECT}/ibmmas-cli:${VERSION}"
    echo "Using OCP internal registry image: ${IMAGE_REFERENCE}"
  else
    IMAGE_REFERENCE="quay.io/ibmmas/cli:${VERSION}"
    echo "Using default image: ${IMAGE_REFERENCE}"
  fi

  TASK_FILES=$TARGET_DIR/tasks/*.yaml
  PIPELINE_FILES=$TARGET_DIR/pipelines/*.yaml

  TARGET_FILE=$DIR/../../tekton/target/ibm-mas-tekton.yaml
  TARGET_FILE_FVT=$DIR/../../tekton/target/ibm-mas-tekton-fvt.yaml
  TARGET_FILE_IN_CLI=$DIR/../../image/cli/mascli/templates/ibm-mas-tekton.yaml
  TARGET_FILE_IN_PY=$DIR/../../python/src/mas/cli/templates/ibm-mas-tekton.yaml
fi


# 1. Generate tasks and pipelines
# -----------------------------------------------------------------------------
if [[ "$1" == "tasks" ]] || [[ "$1" == "" ]]; then
  ansible-playbook tekton/generate-tekton-tasks.yml || exit 1
fi
if [[ "$1" == "pipelines" ]] || [[ "$1" == "" ]]; then
  ansible-playbook tekton/generate-tekton-pipelines.yml || exit 1
fi

# 2. Generate ibm-mas-tekton.yaml and ibm-mas-tekton-fvt.yaml
# -----------------------------------------------------------------------------
echo "Creating tekton installers"

# Determine the image reference to use
if [ "$DEV_MODE" == "true" ] && [ "$USE_OCP_REGISTRY" == "true" ]; then
  IMAGE_REFERENCE="${IMAGE_REGISTRY}/${OCP_PROJECT}/ibmmas-cli:${VERSION}"
  echo "Updating image references to: ${IMAGE_REFERENCE}"
else
  IMAGE_REFERENCE="quay.io/ibmmas/cli:$VERSION"
fi

echo "" > $TARGET_FILE
echo "" > $TARGET_FILE_FVT

function addToFile() {
  src_file=$1
  dst_file=$2
  printf '[%-23s] %s\n' $(basename $dst_file) $(basename $src_file)

  # Update the file in-place, then add to combined file
  sed -i "s#quay.io/ibmmas/cli:latest#${IMAGE_REFERENCE}#g" "$src_file"

  echo "# --------------------------------------------------------------------------------" >> $dst_file
  echo "# $src_file" >> $dst_file
  echo "# --------------------------------------------------------------------------------" >> $dst_file
  cat $src_file >> $dst_file
}

for FILE in $TASK_FILES; do
  FILE_NAME=$(basename $FILE)
  case "$FILE_NAME" in
    *fvt-*|*ivt-*|aiservice-fvt*|aiservice-launchfvt*)
      addToFile $FILE $TARGET_FILE_FVT
      ;;
    *)
      addToFile $FILE $TARGET_FILE
      ;;
  esac
done

for FILE in $PIPELINE_FILES; do
  FILE_NAME=$(basename $FILE)
  case "$FILE_NAME" in
    *fvt-*|*ivt-*|aiservice-fvt*)
      addToFile $FILE $TARGET_FILE_FVT
      ;;
    *)
      addToFile $FILE $TARGET_FILE
      ;;
  esac
done

cp $TARGET_FILE $TARGET_FILE_IN_CLI
cp $TARGET_FILE $TARGET_FILE_IN_PY

# Extra debug for Travis builds
if [ "$DEV_MODE" != "true" ]; then
  cat $TARGET_FILE
fi
