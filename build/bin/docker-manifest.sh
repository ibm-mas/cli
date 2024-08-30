#!/usr/bin/env bash

# Note: When using this script be sure to specify "--target-platform=amd64" when
# building the amd64 image, otherwise the amd64 image will not have an
# architecture prefix and won't be found.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/.functions.sh

while [[ $# -gt 0 ]]
do
  key="$1"
  shift

  case $key in
    -p|--prefix)
    ICR_PRODUCTION_PREFIX="$1"
    shift
    ;;

    -n|--namespace)
    NAMESPACE="$1"
    shift
    ;;

    -i|--image)
    IMAGE="$1"
    shift
    ;;

    -r|--repository)
    ARTIFACTORY_REPO="$1"
    shift
    ;;

    --manifest-prefix)
    MANIFEST_PREFIX="$1"
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

# =====================================================================================================================
# Generate manifest
# =====================================================================================================================
ARTIFACTORY_REPO=quay.io
FQ_IMAGE_WITH_TAG=$NAMESPACE/$IMAGE:${MANIFEST_PREFIX}${DOCKER_TAG}
ARTIFACTORY_SRC=$ARTIFACTORY_REPO/$NAMESPACE/$IMAGE:${DOCKER_TAG}
ARTIFACTORY_DEST=$ARTIFACTORY_REPO/$FQ_IMAGE_WITH_TAG
echo "SRC "$ARTIFACTORY_SRC
echo "DESC" $ARTIFACTORY_DEST
# Publish manifest to Artifactory
# -----------------------------------------------------------------------------
echo_h2 "Publishing manifest to Artifactory ($TARGET_PLATFORMS)"
MANIFEST_CMD="docker manifest create $ARTIFACTORY_DEST"
#docker login --username "${{ secrets.QUAYIO_USERNAME }}" --password "${{ secrets.QUAYIO_PASSWORD }}" quay.io

for TARGET_PLATFORM in $TARGET_PLATFORMS; do
  echo "Adding $TARGET_PLATFORM"
  MANIFEST_CMD="${MANIFEST_CMD} ${ARTIFACTORY_SRC}-${TARGET_PLATFORM}"
  echo $MANIFEST_CMD
done
$MANIFEST_CMD

if [[ "$?" != "0" ]]; then
  echo_warning "An error occured generating manifest image ($ARTIFACTORY_DEST)"
  echo_warning "Command: $MANIFEST_CMD"
  exit 1
fi

docker manifest inspect $ARTIFACTORY_DEST
docker manifest push --purge $ARTIFACTORY_DEST
if [[ "$?" != "0" ]]; then
  echo_warning "An error occured pushing manifest image ($ARTIFACTORY_DEST)"
  exit 1
fi
