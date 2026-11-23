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
  mkdir -vp ~/.docker/cli-plugins/
  curl --silent -L "https://github.com/docker/buildx/releases/download/v0.31.1/buildx-v0.31.1.linux-amd64" > ~/.docker/cli-plugins/docker-buildx
  chmod a+x ~/.docker/cli-plugins/docker-buildx

  sudo apt-get update
  sudo apt-get install -y qemu-user-binfmt binfmt-support || sudo apt-get install -y qemu-user-static binfmt-support
  if command -v qemu-aarch64-static &> /dev/null; then
    qemu-aarch64-static --version
  fi
  if command -v update-binfmts &> /dev/null; then
    update-binfmts --version
  fi

  docker version || exit 1
  docker buildx version || exit 1
  docker buildx inspect --bootstrap || exit 1
}

# These should be loaded already, but just incase!
# ------------------------------------------------
if [[ -z "$BUILD_SYSTEM_ENV_LOADED" ]]; then
  source $DIR/.env.sh
fi


# install oscap tools
function install_oscap() {
  sudo apt-get install -y openscap-scanner
}
