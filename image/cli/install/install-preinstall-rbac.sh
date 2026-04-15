#!/bin/bash

set -e

# This script clones the pre-install repository and copies ALL versioned operator RBAC files
# into the CLI image during build time. The CLI copies all MAS versions so it can
# support different MAS releases.
#
# Structure in pre-install (grouped by MAS version):
#   operators/<mas_version>/<operator>/rbac/clusterroles/
#   operators/<mas_version>/<operator>/rbac/roles/essential/
#   operators/<mas_version>/<operator>/rbac/roles/non-essential/
#
# Structure in CLI image (preserves MAS version structure):
#   /opt/app-root/rbac/operators/<mas_version>/<operator>/rbac/clusterroles/
#   /opt/app-root/rbac/operators/<mas_version>/<operator>/rbac/roles/essential/
#   /opt/app-root/rbac/operators/<mas_version>/<operator>/rbac/roles/non-essential/
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
  
  # Use ds.rbac branch for RBAC files
  PREINSTALL_BRANCH="ds.rbac"
  echo "Using pre-install branch: ${PREINSTALL_BRANCH}"
  
  # Clone the repository
  cd /tmp/install
  if git clone --depth 1 --branch "${PREINSTALL_BRANCH}" https://github.com/ibm-mas/pre-install.git 2>/dev/null; then
    echo "Successfully cloned pre-install repository (branch: ${PREINSTALL_BRANCH})"
  else
    echo "Branch ${PREINSTALL_BRANCH} not found, falling back to master branch"
    git clone --depth 1 --branch master https://github.com/ibm-mas/pre-install.git
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

# Copy all versioned RBAC files
for VERSION_DIR in "$OPERATORS_SOURCE"/*/; do
  if [ -d "$VERSION_DIR" ]; then
    VERSION_NAME=$(basename "$VERSION_DIR")
    
    # Skip non-version directories (only process directories like 9.2, 9.3, etc.)
    if [[ ! "$VERSION_NAME" =~ ^[0-9]+\.[0-9]+$ ]]; then
      continue
    fi
    
    VERSIONS_COPIED+=("$VERSION_NAME")
    
    # Process each operator in this version
    for OPERATOR_DIR in "$VERSION_DIR"/*/; do
      if [ -d "$OPERATOR_DIR" ] && [ -d "$OPERATOR_DIR/rbac" ]; then
        OPERATOR_NAME=$(basename "$OPERATOR_DIR")
        DEST_PATH="$RBAC_DEST/$VERSION_NAME/$OPERATOR_NAME/rbac"
        mkdir -p "$DEST_PATH"
        cp -r "$OPERATOR_DIR/rbac"/* "$DEST_PATH/"
      fi
    done
  fi
done

echo "RBAC files copied successfully for versions: ${VERSIONS_COPIED[*]}"
