#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# COLOR_RED=`tput setaf 1`
# COLOR_GREEN=`tput setaf 2`
# COLOR_YELLOW=`tput setaf 3`
# COLOR_BLUE=`tput setaf 4`
# COLOR_MAGENTA=`tput setaf 5`
# COLOR_CYAN=`tput setaf 6`
# TEXT_RESET=`tput sgr0`

# tput doesn't work in GitHub actions
# TODO: Integrate properly with GitHub actions to annotate the output as errors etc
COLOR_RED=""
COLOR_GREEN=""
COLOR_YELLOW=""
COLOR_BLUE=""
COLOR_MAGENTA=""
COLOR_CYAN=""
TEXT_RESET=""


function echo_h1() {
  echo "${COLOR_YELLOW}================================================================================"
  echo "${COLOR_YELLOW}$1"
  echo "${COLOR_YELLOW}================================================================================"
}


function echo_h2() {
  echo "${COLOR_YELLOW}$1"
  echo "${COLOR_YELLOW}--------------------------------------------------------------------------------"
}


function echo_warning() {
  echo "${COLOR_RED}$1"
}


function echo_highlight() {
  echo "${COLOR_MAGENTA}$1"
}

#Install buildx for multi-arch
# -----------------------------------------------------------------------------
# Useful links:
# - https://docs.docker.com/engine/reference/commandline/buildx_build/#output
# - https://docs.docker.com/build/building/multi-platform/
# - https://medium.com/@artur.klauser/building-multi-architecture-docker-images-with-buildx-27d80f7e2408
# - https://stackoverflow.com/questions/65365797/docker-buildx-exec-user-process-caused-exec-format-error
function install_buildx() {
 # docker buildx use mybuilder &> /dev/null
  echo "install_buildx"
 # if [ "$?" != "0" ]; then
     echo "inside0 install_buildx"
    mkdir -vp ~/.docker/cli-plugins/
    #https://download.docker.com/linux/rhel/8/x86_64/stable/Packages/docker-buildx-plugin-0.16.1-1.el8.x86_64.rpm
    curl --silent -L "https://github.com/docker/buildx/releases/download/v0.11.2/buildx-v0.11.2.linux-amd64" > ~/.docker/cli-plugins/docker-buildx
    chmod a+x ~/.docker/cli-plugins/docker-buildx
    echo "inside 1 install_buildx"
    sudo apt-get update
    echo "inside 1-1 install_buildx"
    sudo apt-get install -y qemu-user-static
    echo "inside2 install_buildx"
    qemu-aarch64-static --version
    echo "inside3 install_buildx"
    sudo apt-get install -y binfmt-support
    update-binfmts --version
    docker buildx create --name mybuilder
    docker buildx use mybuilder
#  fi
  docker version || exit 1
  docker buildx version || exit 1
  docker buildx inspect --bootstrap || exit 1
}

# These should be loaded already, but just incase!
# ------------------------------------------------
if [[ -z "$BUILD_SYSTEM_ENV_LOADED" ]]; then
  source $DIR/.env.sh
fi


# Upload a file to Artifactory
# -----------------------------------------------------------------------------
# Usage example:
#  artifactory_upload $FILE_PATH $TARGET_URL
#
function artifactory_upload() {
  if [ ! -e $1 ]; then
    echo_warning "Artifactory upload failed - $1 does not exist"
    exit 1
  fi

  md5Value="`md5sum "$1"`"
  md5Value="${md5Value:0:32}"

  sha1Value="`sha1sum "$1"`"
  sha1Value="${sha1Value:0:40}"

  echo "Uploading $1 to $2"
  curl -H "Authorization:Bearer $ARTIFACTORY_TOKEN"  -H "X-Checksum-Md5: $md5Value" -H "X-Checksum-Sha1: $sha1Value" -T $1 $2 || exit 1
}
