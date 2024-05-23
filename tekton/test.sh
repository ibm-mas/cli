#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

TASK_FILES=$DIR/target/tasks/*.yaml
PIPELINE_FILES=$DIR/target/pipelines/*.yaml

# Tasks
if [[ "$1" == "tasks" ]] || [[ "$1" == "" ]]; then
  for FILE in $TASK_FILES; do
    echo " - Adding Task: $FILE"
    oc apply -f $FILE
  done
fi

# Pipelines
if [[ "$1" == "pipelines" ]] || [[ "$1" == "" ]]; then
  for FILE in $PIPELINE_FILES; do
    echo " - Adding Pipeline: $FILE"
    oc apply -f $FILE
  done
fi
