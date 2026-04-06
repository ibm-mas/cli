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

# Check if pre-install directory already exists (local development)
if [ -d "/tmp/install/pre-install/maximo-operator-catalog/operators" ]; then
  echo "Using local pre-install directory"
  PREINSTALL_SOURCE="/tmp/install/pre-install/maximo-operator-catalog"
else
  # Clone pre-install repository
  echo "Cloning pre-install repository..."
  
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

echo ""
echo "Copying RBAC for all MAS versions..."
echo "Source: $OPERATORS_SOURCE"
echo ""

# Track what we copied
VERSION_COUNT=0
OPERATOR_COUNT=0
TOTAL_FILES=0

# Copy RBAC for all MAS versions
for VERSION_DIR in "$OPERATORS_SOURCE"/*/; do
  if [ -d "$VERSION_DIR" ]; then
    VERSION_NAME=$(basename "$VERSION_DIR")
    
    # Skip non-version directories (like README.md parent dir)
    if [[ ! "$VERSION_NAME" =~ ^[0-9]+\.[0-9]+$ ]]; then
      continue
    fi
    
    echo "=== MAS Version: $VERSION_NAME ==="
    VERSION_OPERATOR_COUNT=0
    
    # Process each operator in this version
    for OPERATOR_DIR in "$VERSION_DIR"/*/; do
      if [ -d "$OPERATOR_DIR" ]; then
        OPERATOR_NAME=$(basename "$OPERATOR_DIR")
        
        # Skip non-operator directories
        if [ "$OPERATOR_NAME" == "ibm-operator-catalog" ]; then
          continue
        fi
        
        # Check if operator has RBAC directory
        if [ -d "$OPERATOR_DIR/rbac" ]; then
          echo "  ✓ $OPERATOR_NAME"
          
          # Destination: /opt/app-root/rbac/operators/<version>/<operator>/rbac/
          DEST_PATH="$RBAC_DEST/$VERSION_NAME/$OPERATOR_NAME/rbac"
          mkdir -p "$DEST_PATH"
          
          # Copy clusterroles if they exist
          if [ -d "$OPERATOR_DIR/rbac/clusterroles" ]; then
            cp -r "$OPERATOR_DIR/rbac/clusterroles" "$DEST_PATH/"
            CR_COUNT=$(find "$DEST_PATH/clusterroles" -type f \( -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | wc -l | tr -d ' ')
            if [ "$CR_COUNT" -gt 0 ]; then
              echo "    - ClusterRoles: $CR_COUNT"
              TOTAL_FILES=$((TOTAL_FILES + CR_COUNT))
            fi
          fi
          
          # Copy roles if they exist
          if [ -d "$OPERATOR_DIR/rbac/roles" ]; then
            cp -r "$OPERATOR_DIR/rbac/roles" "$DEST_PATH/"
            
            # Count essential roles
            if [ -d "$DEST_PATH/roles/essential" ]; then
              ESS_COUNT=$(find "$DEST_PATH/roles/essential" -type f \( -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | wc -l | tr -d ' ')
              if [ "$ESS_COUNT" -gt 0 ]; then
                echo "    - Essential: $ESS_COUNT"
                TOTAL_FILES=$((TOTAL_FILES + ESS_COUNT))
              fi
            fi
            
            # Count non-essential roles
            if [ -d "$DEST_PATH/roles/non-essential" ]; then
              NON_ESS_COUNT=$(find "$DEST_PATH/roles/non-essential" -type f \( -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | wc -l | tr -d ' ')
              if [ "$NON_ESS_COUNT" -gt 0 ]; then
                echo "    - Non-Essential: $NON_ESS_COUNT"
                TOTAL_FILES=$((TOTAL_FILES + NON_ESS_COUNT))
              fi
            fi
          fi
          
          VERSION_OPERATOR_COUNT=$((VERSION_OPERATOR_COUNT + 1))
          OPERATOR_COUNT=$((OPERATOR_COUNT + 1))
        fi
      fi
    done
    
    if [ $VERSION_OPERATOR_COUNT -gt 0 ]; then
      echo "  Total operators in $VERSION_NAME: $VERSION_OPERATOR_COUNT"
      VERSION_COUNT=$((VERSION_COUNT + 1))
    fi
    echo ""
  fi
done

# Summary
if [ $VERSION_COUNT -eq 0 ]; then
  echo "WARNING: No versioned RBAC found"
  echo "Expected structure: operators/<version>/<operator>/rbac/"
else
  echo "========================================="
  echo "RBAC Installation Summary:"
  echo "  - MAS versions copied: $VERSION_COUNT"
  echo "  - Total operators: $OPERATOR_COUNT"
  echo "  - Total RBAC files: $TOTAL_FILES"
  echo "  - Installation directory: $RBAC_DEST"
  echo "========================================="
fi

echo ""
echo "Note: User-facing RBAC (admin/readonly roles) remain in"
echo "      pre-install and are applied via kustomize, not by CLI."
echo ""
echo "Directory structure (first 50 lines):"
if [ -d "$RBAC_DEST" ]; then
  ls -R "$RBAC_DEST" | head -50
else
  echo "  (No RBAC directory created yet)"
fi
