#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$DEV_MODE" != "true" ]; then
  source ${GITHUB_WORKSPACE}/build/bin/.env.sh
  source ${GITHUB_WORKSPACE}/build/bin/.functions.sh

  TASK_FILES=$GITHUB_WORKSPACE/tekton/tasks/*.yaml
  PIPELINE_FILES=$GITHUB_WORKSPACE/tekton/pipelines/*.yaml
  TARGET_FILE=$GITHUB_WORKSPACE/image/cli/mascli/templates/ibm-mas-tekton.yaml
else
  TASK_FILES=$DIR/../../tekton/tasks/*.yaml
  PIPELINE_FILES=$DIR/../../tekton/pipelines/*.yaml
  TARGET_FILE=$DIR/../../image/cli/mascli/templates/ibm-mas-tekton.yaml
fi

ansible-playbook tekton/generate-pipelines.yml

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

# Extra debug for Travis builds
if [ "$DEV_MODE" != "true" ]; then
  cat $TARGET_FILE
fi
