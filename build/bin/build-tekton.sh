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
  VERSION=${VERSION:-11.3.0-pre.uninstallDRO}

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
echo "" > $TARGET_FILE
echo "" > $TARGET_FILE_FVT


function addToFile() {
  src_file=$1
  dst_file=$2
  printf '[%-23s] %s\n' $(basename $dst_file) $(basename $src_file)
  echo "# --------------------------------------------------------------------------------" >> $dst_file
  echo "# $src_file" >> $dst_file
  echo "# --------------------------------------------------------------------------------" >> $dst_file
  cat $src_file >> $dst_file

}

for FILE in $TASK_FILES; do
  FILE_NAME=$(basename $FILE)

  if [[ "$FILE_NAME" == fvt-* ]] || [[ "$FILE_NAME" == ivt-* ]] || [[ "$FILE_NAME" == launchfvt-* ]] || [[ "$FILE_NAME" == launchivt-* ]]
  then addToFile $FILE $TARGET_FILE_FVT
  else addToFile $FILE $TARGET_FILE
  fi
done

for FILE in $PIPELINE_FILES; do
  FILE_NAME=$(basename $FILE)

  if [[ "$FILE_NAME" == fvt-* ]] || [[ "$FILE_NAME" == ivt-* ]] || [[ "$FILE_NAME" == *-after-install.yaml ]] || [[ "$FILE_NAME" == *-with-fvt.yaml ]]
  then addToFile $FILE $TARGET_FILE_FVT
  else addToFile $FILE $TARGET_FILE
  fi
done

# What a very long winded way of doing in-place sed! I'm sure someone did it this way for a reason?
sed "s#quay.io/ibmmas/cli:latest#quay.io/ibmmas/cli:$VERSION#g" $TARGET_FILE > $TARGET_FILE.txt
sed "s#quay.io/ibmmas/cli:latest#quay.io/ibmmas/cli:$VERSION#g" $TARGET_FILE_FVT > $TARGET_FILE_FVT.txt
rm $TARGET_FILE
rm $TARGET_FILE_FVT
mv $TARGET_FILE.txt $TARGET_FILE
mv $TARGET_FILE_FVT.txt $TARGET_FILE_FVT

cp $TARGET_FILE $TARGET_FILE_IN_CLI
cp $TARGET_FILE $TARGET_FILE_IN_PY

# Extra debug for Travis builds
if [ "$DEV_MODE" != "true" ]; then
  cat $TARGET_FILE
fi
