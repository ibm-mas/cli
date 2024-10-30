#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/.env.sh
source $DIR/.functions.sh

while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        -r|--repo)
        REPOSITORY="$2"
        ;;

        -b|--buildpath)
        BUILDPATH="$2"
        ;;

        -f|--file)
        DOCKERFILE="$2"
        ;;

        --target-platform)
        TARGET_PLATFORM="$2"
        ;;

        *)
        # unknown option, use as additional params directly to docker
        EXTRA_PARAMS="$EXTRA_PARAMS $key $2"
        ;;
    esac
    shift
    shift
done

BUILDPATH="${BUILDPATH:-image}"
DOCKERFILE="${DOCKERFILE:-$BUILDPATH/Dockerfile.$TARGET_PLATFORM}"

# Fallback to $BUILDPATH/Dockerfile if $DOCKERFILE does not exist
if [ ! -e $DOCKERFILE ]; then
  DOCKERFILE="$BUILDPATH/Dockerfile"
fi

LOCAL_TAG=$REPOSITORY:$DOCKER_TAG-$TARGET_PLATFORM

echo_h1 "Build Docker Image"
echo "REPOSITORY ....... $REPOSITORY"
echo "DOCKER_TAG ....... $DOCKER_TAG"
echo "TARGET_PLATFORM .. $TARGET_PLATFORM"
echo "LOCAL_TAG ........ $LOCAL_TAG"
echo
echo "BUILDPATH ........ $BUILDPATH"
echo "DOCKERFILE ....... $DOCKERFILE"
echo "EXTRA_PARAMS ..... $EXTRA_PARAMS"
echo "VERSION_LABEL .... $DOCKER_TAG"
echo "RELEASE_LABEL .... $GITHUB_RUN_ID"
echo "VCS_REF .......... $GITHUB_SHA"
echo "VCS_URL .......... https://github.com/$GITHUB_REPOSITORY"

install_buildx

# Remove expires-after for release builds (only pre-release builds should auto-expire)
if [[ ! "$DOCKER_TAG" == *"-pre."* ]]; then
  echo "Removing quay.expires-after label from Dockerfile"
  sed -i "/quay.expires-after/d" $DOCKERFILE
fi

docker buildx build --progress plain \
  --load \
  --platform linux/$TARGET_PLATFORM \
  --build-arg ARCHITECTURE=$TARGET_PLATFORM \
  --build-arg VERSION_LABEL=$DOCKER_TAG \
  --build-arg RELEASE_LABEL=$GITHUB_RUN_ID \
  --build-arg VCS_REF=$GITHUB_SHA \
  --build-arg VCS_URL=https://github.com/$GITHUB_REPOSITORY \
  -t $LOCAL_TAG $EXTRA_PARAMS -f $DOCKERFILE $BUILDPATH || exit 1
