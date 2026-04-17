#!/bin/bash

set -e

# This script clones the pre-install repository and copies ALL operator RBAC files
# into the CLI image during build time. The CLI copies the flattened RBAC structure
# so suite_rbac can auto-detect RBAC files by filename prefix for each MAS version.
#
# Structure in pre-install:
#   operators/<operator>/rbac/<mas_version>/*.yml
#
# Structure in CLI image:
#   /opt/app-root/rbac/operators/<operator>/rbac/<mas_version>/*.yml
export GITHUB_REF_NAME="${GITHUB_REF_NAME:-ds.rbac}"
export GITHUB_REF_TYPE="${GITHUB_REF_TYPE:-branch}"
echo "========================================"
echo "Installing Operator RBAC Files"
echo "========================================"
echo "GitHub reference = ${GITHUB_REF_TYPE}/${GITHUB_REF_NAME}"
echo "Contents of /tmp/install/:"
ls -l /tmp/install/
echo ""

# Destination directory in CLI image
RBAC_DEST="/opt/app-root/rbac/operators"

# Create destination directory
mkdir -p "$RBAC_DEST"

# If the local tar.gz file is present, extract and use it
# Otherwise, clone from GitHub
if [[ -e /tmp/install/pre-install.tar.gz ]]; then
  echo "Installing local build of pre-install from archive"
  cd /tmp/install
  tar -xzf pre-install.tar.gz
  PREINSTALL_SOURCE="/tmp/install/pre-install/maximo-operator-catalog"
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
  
  PREINSTALL_SOURCE="/tmp/install/pre-install/maximo-operator-catalog"
fi

OPERATORS_SOURCE="$PREINSTALL_SOURCE/operators"

if [ ! -d "$OPERATORS_SOURCE" ]; then
  echo "ERROR: Operators directory not found: $OPERATORS_SOURCE"
  exit 1
fi

echo "Copying RBAC files from $OPERATORS_SOURCE to $RBAC_DEST"

VERSIONS_COPIED=()

# Copy flattened operator RBAC files
for OPERATOR_DIR in "$OPERATORS_SOURCE"/*/; do
  if [ -d "$OPERATOR_DIR" ] && [ -d "$OPERATOR_DIR/rbac" ]; then
    OPERATOR_NAME=$(basename "$OPERATOR_DIR")
    DEST_PATH="$RBAC_DEST/$OPERATOR_NAME/rbac"
    mkdir -p "$DEST_PATH"
    cp -r "$OPERATOR_DIR/rbac"/* "$DEST_PATH/"

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

VERSIONS_COPIED=($(printf "%s\n" "${VERSIONS_COPIED[@]}" | sort -u))
echo "RBAC files copied successfully for versions: ${VERSIONS_COPIED[*]}"
