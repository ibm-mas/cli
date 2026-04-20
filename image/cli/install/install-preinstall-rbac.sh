#!/bin/bash

set -e

# This script clones the pre-install repository and copies operator RBAC files
# into the CLI image during build time in a single RBAC root.
#
# Structures in pre-install:
#   catalogs/maximo-operator-catalog/operators/<operator>/rbac/<mas_version>/*.yml
#   catalogs/redhat-operator-catalog/operators/<operator>/rbac/<mas_version>/*.yml
#   openshift-platform/operators/<operator>/rbac/<mas_version>/*.yml
#
# Structure in CLI image:
#   /opt/app-root/rbac/maximo-operator-catalog/operators/<operator>/rbac/<mas_version>/*.yml
#   /opt/app-root/rbac/redhat-operator-catalog/operators/<operator>/rbac/<mas_version>/*.yml
#   /opt/app-root/rbac/openshift-platform/operators/<operator>/rbac/<mas_version>/*.yml
export GITHUB_REF_NAME="${GITHUB_REF_NAME:-ds.rbac}"
export GITHUB_REF_TYPE="${GITHUB_REF_TYPE:-branch}"
echo "========================================"
echo "Installing Operator RBAC Files"
echo "========================================"
echo "GitHub reference = ${GITHUB_REF_TYPE}/${GITHUB_REF_NAME}"
echo "Contents of /tmp/install/:"
ls -l /tmp/install/
echo ""

# Destination root directory in CLI image
RBAC_DEST="/opt/app-root/rbac"

# Create destination directory
mkdir -p "$RBAC_DEST"

# If the local tar.gz file is present, extract and use it
# Otherwise, clone from GitHub
if [[ -e /tmp/install/pre-install.tar.gz ]]; then
  echo "Installing local build of pre-install from archive"
  cd /tmp/install
  tar -xzf pre-install.tar.gz
  PREINSTALL_SOURCE="/tmp/install/pre-install"
else
  # Clone pre-install repository
  echo "Cloning pre-install repository from GitHub..."
  
  # Determine which branch/tag to use
  if [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
    PREINSTALL_BRANCH="${GITHUB_REF_NAME}"
    echo "Attempting to clone matching branch: ${PREINSTALL_BRANCH}"
  else
    # For tag builds, use main branch
    PREINSTALL_BRANCH="main"
    echo "Using main branch for tag build"
  fi
  
  # Clone the repository
  cd /tmp/install
  if git clone --depth 1 --branch "${PREINSTALL_BRANCH}" https://github.com/ibm-mas/pre-install.git 2>/dev/null; then
    echo "Successfully cloned pre-install repository (branch: ${PREINSTALL_BRANCH})"
  else
    echo "Branch ${PREINSTALL_BRANCH} not found, falling back to main branch"
    git clone --depth 1 --branch main https://github.com/ibm-mas/pre-install.git
  fi
  
  PREINSTALL_SOURCE="/tmp/install/pre-install"
fi

MAXIMO_OPERATORS_SOURCE="$PREINSTALL_SOURCE/catalogs/maximo-operator-catalog/operators"
REDHAT_OPERATORS_SOURCE="$PREINSTALL_SOURCE/catalogs/redhat-operator-catalog/operators"
OPENSHIFT_PLATFORM_OPERATORS_SOURCE="$PREINSTALL_SOURCE/openshift-platform/operators"

COPY_SOURCES=(
  "$MAXIMO_OPERATORS_SOURCE"
  "$REDHAT_OPERATORS_SOURCE"
  "$OPENSHIFT_PLATFORM_OPERATORS_SOURCE"
)

echo "Copying RBAC files into $RBAC_DEST"

VERSIONS_COPIED=()
COPIED_SOURCE_ROOTS=()

copy_operator_rbac() {
  local SOURCE_ROOT="$1"
  local DEST_ROOT="$2"

  if [ ! -d "$SOURCE_ROOT" ]; then
    echo "Skipping missing source: $SOURCE_ROOT"
    return
  fi

  COPIED_SOURCE_ROOTS+=("$SOURCE_ROOT")

  for OPERATOR_DIR in "$SOURCE_ROOT"/*/; do
    if [ -d "$OPERATOR_DIR" ] && [ -d "$OPERATOR_DIR/rbac" ]; then
      OPERATOR_NAME=$(basename "$OPERATOR_DIR")
      DEST_PATH="$DEST_ROOT/$OPERATOR_NAME/rbac"
      mkdir -p "$DEST_PATH"

      if compgen -G "$OPERATOR_DIR/rbac/*" > /dev/null; then
        cp -r "$OPERATOR_DIR/rbac"/* "$DEST_PATH/"
      fi

      for VERSION_DIR in "$OPERATOR_DIR/rbac"/*/; do
        if [ -d "$VERSION_DIR" ]; then
          VERSION_NAME=$(basename "$VERSION_DIR")
          if [[ "$VERSION_NAME" =~ ^[0-9]+\.[0-9]+$ ]]; then
            VERSIONS_COPIED+=("$VERSION_NAME")
          fi
        fi
      done
    fi
  done
}

copy_operator_rbac "$MAXIMO_OPERATORS_SOURCE" "$RBAC_DEST/maximo-operator-catalog/operators"
copy_operator_rbac "$REDHAT_OPERATORS_SOURCE" "$RBAC_DEST/redhat-operator-catalog/operators"
copy_operator_rbac "$OPENSHIFT_PLATFORM_OPERATORS_SOURCE" "$RBAC_DEST/openshift-platform/operators"

VERSIONS_COPIED=($(printf "%s\n" "${VERSIONS_COPIED[@]}" | sort -u))
echo "RBAC files copied successfully from: ${COPIED_SOURCE_ROOTS[*]}"
echo "RBAC files copied successfully for versions: ${VERSIONS_COPIED[*]}"
