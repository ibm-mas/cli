#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/.functions.sh  || exit 1
source ${DIR}/.env.sh || exit 1


function die()
{
    echo "$*" >&2
    exit 1
}

function invalid()
{
    echo -e "$*\n" >&2
    usage
    exit 1
}

function usage()
{
    echo "oscap-docker -- Tool for SCAP evaluation of Docker images and containers."
    echo
    echo "Compliance scan of Docker image:"
    echo "$ sudo oscap-docker [--oscap=<OSCAP_BINARY>] IMAGE_NAME OSCAP_ARGUMENT [OSCAP_ARGUMENT...]"
    echo
    echo "Compliance scan of Docker container:"
    echo "$ sudo oscap-docker [--oscap=<OSCAP_BINARY>] CONTAINER_NAME OSCAP_ARGUMENT [OSCAP_ARGUMENT...]"
    echo
    echo "See \`man oscap\` to learn more about semantics of OSCAP_ARGUMENT options."
}

OSCAP_BINARY=oscap

if [ $# -lt 1 ]; then
    invalid "No arguments provided."
elif [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
    exit 0
elif [[ "$1" == --oscap=* ]] && [ $# -gt 2 ]; then
    OSCAP_BINARY=${1#"--oscap="}
    shift
elif [ "$#" -gt 1 ]; then
    true
else
    invalid "Invalid arguments provided."
fi

if [ "$(id -u)" -ne 0 ]; then
    die "This script cannot run in rootless mode."
fi
if grep -q -- "--remediate" <<< "$@"; then
    die "This script does not support '--remediate' option."
fi

IMAGE_NAME=$(docker image inspect --format "{{.Id}} {{.RepoTags}}" "$1")

# Check if the target of scan is image or container.
CLEANUP=0
if [ -n "$IMAGE_NAME" ]; then
    ID=$(docker create $1 sh) || die "Unable to create a container."
    TARGET="docker-image://$IMAGE_NAME"
    CLEANUP=1
else
    die "Target of the scan not found: '$1'."
fi


MOUNT_TMP=$(mktemp -d)
docker export "$ID" | tar -C "$MOUNT_TMP" -xf - || die "Failed to export container."

DIR="$MOUNT_TMP"
if [ ! -f "$DIR/run/.containerenv" ]; then
    # ubi8-init image does not create .containerenv when running docker init, but we need to make sure that the file is there
    touch "$DIR/run/.containerenv"
fi

ls -l $DIR/run/.containerenv
export OSCAP_CONTAINER_VARS
OSCAP_CONTAINER_VARS=`docker inspect $ID --format '{{join .Config.Env "\n"}}'`

export OSCAP_PROBE_ROOT
OSCAP_PROBE_ROOT="$(cd "$DIR" && pwd)" || die "Unable to change current directory to OSCAP_PROBE_ROOT (DIR)."
export OSCAP_EVALUATION_TARGET="$TARGET"
shift 1

#echo_begingroup "OSCAP scan report for $NAMESPACE/$IMAGE"
$OSCAP_BINARY "$@" | echo
EXIT_CODE=$?
#echo_debug "EXIT_CODE:$EXIT_CODE"
#echo_endgroup

if [ $CLEANUP -eq 1 ]; then
    # docker-rm should handle also unmounting of the container filesystem.
    docker rm "$ID" &> /dev/null || die "Failed to clean up."
    rm -rf "$MOUNT_TMP"
fi
exit $EXIT_CODE

