#!/bin/bash
set -e

# Bundles the operator RBAC manifests from the ibm-mas/pre-install repository into the mas-cli python package
# so that `mas-cli pre-install` works when installed with uvx / uv tool, where /opt/app-root/rbac does not exist.
#
# The container image copies this same bundled tree into /opt/app-root/rbac (see image/cli/Dockerfile):
#   catalogs/maximo-operator-catalog/operators/<operator>/rbac/**  ->  <DEST>/maximo-operator-catalog/operators/<operator>/rbac/**
#   openshift-platform/operators/<operator>/rbac/**                ->  <DEST>/openshift-platform/operators/<operator>/rbac/**
#
# Source selection (first match wins):
#   1. image/cli/install/pre-install.tar.gz, a local archive of the pre-install repository
#   2. a clone of the branch matching GITHUB_REF_NAME (branch builds only)
#   3. a clone of the master branch
#
# A SOURCE.json recording the repository, branch, commit and manifest count is written next to the manifests
# so that it is always possible to say which RBAC a given mas-cli release ships.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE="${GITHUB_WORKSPACE:-$( cd "$DIR/../.." && pwd )}"

export GITHUB_REF_NAME="${GITHUB_REF_NAME:-master}"
export GITHUB_REF_TYPE="${GITHUB_REF_TYPE:-branch}"

DEST="$WORKSPACE/python/src/mas/cli/rbac/preinstall"
LOCAL_ARCHIVE="$WORKSPACE/image/cli/install/pre-install.tar.gz"
REPO_URL="https://github.com/ibm-mas/pre-install.git"

echo "========================================"
echo "Bundling pre-install RBAC into mas-cli"
echo "========================================"
echo "GitHub reference = ${GITHUB_REF_TYPE}/${GITHUB_REF_NAME}"
echo "Destination      = ${DEST}"

WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

if [[ -e "$LOCAL_ARCHIVE" ]]; then
  echo "Using local build of pre-install from archive $LOCAL_ARCHIVE"
  tar -xzf "$LOCAL_ARCHIVE" -C "$WORK_DIR"
  # An archive carries no trustworthy git metadata, so say so rather than guessing
  SOURCE_BRANCH="local-archive"
  SOURCE_COMMIT="local-archive"
else
  if [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
    PREINSTALL_BRANCH="$GITHUB_REF_NAME"
  else
    # For tag builds, use master branch
    PREINSTALL_BRANCH="master"
  fi

  echo "Cloning ${REPO_URL} (branch: ${PREINSTALL_BRANCH})"
  if ! git clone --quiet --depth 1 --branch "$PREINSTALL_BRANCH" "$REPO_URL" "$WORK_DIR/pre-install" 2>/dev/null; then
    echo "Branch ${PREINSTALL_BRANCH} not found, falling back to master branch"
    PREINSTALL_BRANCH="master"
    rm -rf "$WORK_DIR/pre-install"
    git clone --quiet --depth 1 --branch master "$REPO_URL" "$WORK_DIR/pre-install"
  fi
  SOURCE_BRANCH="$PREINSTALL_BRANCH"
  SOURCE_COMMIT=$(git -C "$WORK_DIR/pre-install" rev-parse HEAD)
fi

SOURCE="$WORK_DIR/pre-install"
if [[ ! -d "$SOURCE" ]]; then
  echo "Error: expected a 'pre-install' directory in the source but none was found"
  exit 1
fi

# Always start from a clean destination so that operators removed upstream do not linger
rm -rf "$DEST"
mkdir -p "$DEST"

copyOperatorRBAC() {
  local SOURCE_ROOT="$1"
  local DEST_ROOT="$2"

  if [[ ! -d "$SOURCE_ROOT" ]]; then
    echo "Skipping missing source: $SOURCE_ROOT"
    return
  fi

  for OPERATOR_DIR in "$SOURCE_ROOT"/*/; do
    if [[ -d "${OPERATOR_DIR}rbac" ]]; then
      OPERATOR_NAME=$(basename "$OPERATOR_DIR")
      mkdir -p "$DEST_ROOT/$OPERATOR_NAME/rbac"
      cp -r "${OPERATOR_DIR}rbac/." "$DEST_ROOT/$OPERATOR_NAME/rbac/"
    fi
  done
}

copyOperatorRBAC "$SOURCE/catalogs/maximo-operator-catalog/operators" "$DEST/maximo-operator-catalog/operators"
copyOperatorRBAC "$SOURCE/openshift-platform/operators" "$DEST/openshift-platform/operators"

# Fail the build rather than shipping a package that silently has no manifests
MANIFEST_COUNT=$(find "$DEST" -type f \( -name "*.yml" -o -name "*.yaml" \) | wc -l | tr -d ' ')
if [[ "$MANIFEST_COUNT" -eq 0 ]]; then
  echo "Error: no RBAC manifests were bundled into $DEST"
  exit 1
fi

# Record provenance
cat > "$DEST/SOURCE.json" <<EOF
{
  "repository": "$REPO_URL",
  "branch": "$SOURCE_BRANCH",
  "commit": "$SOURCE_COMMIT",
  "manifestCount": $MANIFEST_COUNT
}
EOF

echo "Bundled ${MANIFEST_COUNT} RBAC manifests into ${DEST} (branch: ${SOURCE_BRANCH}, commit: ${SOURCE_COMMIT})"
