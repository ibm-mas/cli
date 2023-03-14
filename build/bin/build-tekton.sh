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
  TARGET_FILE_IN_CLI=$GITHUB_WORKSPACE/image/cli/mascli/templates/ibm-mas-tekton.yaml
else
  TARGET_DIR=$DIR/../../tekton/target
  VERSION=3.13.0-pre.rel

  TASK_FILES=$TARGET_DIR/tasks/*.yaml
  PIPELINE_FILES=$TARGET_DIR/pipelines/*.yaml

  TARGET_FILE=$DIR/../../tekton/target/ibm-mas-tekton.yaml
  TARGET_FILE_IN_CLI=$DIR/../../image/cli/mascli/templates/ibm-mas-tekton.yaml
fi

ansible-playbook tekton/generate-tekton-tasks.yml
ansible-playbook tekton/generate-tekton-pipelines.yml
ansible-playbook tekton/generate-tekton-pipelineruns.yml

# Special case, has extra non-standard build logic
ansible-playbook tekton/generate-tekton-upgrade-with-fvt.yml


echo "" > $TARGET_FILE

echo "Creating tekton installer ($TARGET_FILE)"
for FILE in $TASK_FILES; do
  echo " - Adding Task: $FILE"
  echo "# --------------------------------------------------------------------------------" >> $TARGET_FILE
  echo "# $FILE" >> $TARGET_FILE
  echo "# --------------------------------------------------------------------------------" >> $TARGET_FILE
  cat $FILE >> $TARGET_FILE
done

for FILE in $PIPELINE_FILES; do
  echo " - Adding Pipeline: $FILE"
  echo "# --------------------------------------------------------------------------------" >> $TARGET_FILE
  echo "# $FILE" >> $TARGET_FILE
  echo "# --------------------------------------------------------------------------------" >> $TARGET_FILE
  cat $FILE >> $TARGET_FILE
done

sed "s/cli:latest/cli:$VERSION/g" $TARGET_FILE > $TARGET_FILE.txt

rm $TARGET_FILE
mv $TARGET_FILE.txt $TARGET_FILE
cp $TARGET_FILE $TARGET_FILE_IN_CLI

# Extra debug for Travis builds
if [ "$DEV_MODE" != "true" ]; then
  cat $TARGET_FILE
fi
