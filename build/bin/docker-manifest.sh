#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/.functions.sh

while [[ $# -gt 0 ]]
do
  key="$1"
  shift

  case $key in
    -r|--repo)
    REPOSITORY="$1"
    shift
    ;;

    --target-platforms)
    TARGET_PLATFORMS="${1//,/ }"
    shift
    ;;

    *)
    # unknown option
    ;;
  esac
done

# Generate Manifest
# -----------------------------------------------------------------------------
FQ_IMAGE_WITH_TAG=$REPOSITORY:${DOCKER_TAG}

echo_h1 "Publish Docker Manifest"
echo "REPOSITORY ........ $REPOSITORY"
echo "DOCKER_TAG ........ $DOCKER_TAG"
echo "TARGET_PLATFORMS .. $TARGET_PLATFORMS"

echo_h2 "Publishing manifest to Artifactory ($TARGET_PLATFORMS)"
MANIFEST_CMD="docker manifest create $FQ_IMAGE_WITH_TAG"

for TARGET_PLATFORM in $TARGET_PLATFORMS; do
  echo "- Adding $TARGET_PLATFORM to Manifest"
  MANIFEST_CMD="${MANIFEST_CMD} ${FQ_IMAGE_WITH_TAG}-${TARGET_PLATFORM}"
done
$MANIFEST_CMD

if [[ "$?" != "0" ]]; then
  echo_warning "An error occured generating manifest image ($FQ_IMAGE_WITH_TAG)"
  echo_warning "Command: $MANIFEST_CMD"
  exit 1
fi

# Inspect and Push the Manifest
# -----------------------------------------------------------------------------
docker manifest inspect $FQ_IMAGE_WITH_TAG
docker manifest push --purge $FQ_IMAGE_WITH_TAG
if [[ "$?" != "0" ]]; then
  echo_warning "An error occured pushing manifest image ($FQ_IMAGE_WITH_TAG)"
  exit 1
fi
