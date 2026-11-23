#!/bin/bash

echo "Install Ansible Collections"
echo "==========================="
echo "GitHub reference = ${GITHUB_REF_TYPE}/${GITHUB_REF_NAME}"
echo "Contents of /tmp/install/:"
ls -l /tmp/install/
echo ""

# Build the ansible-devops collection from the GitHub branch that matches the name of the branch this image is built from.
# The published collection is not identical to what is in git, build-collection.sh substitutes the catalog version
# placeholders, so we run the same script that the ansible-devops CI uses.
# Returns 0 and installs the collection if successful, otherwise returns non-zero and installs nothing.
function installFromBranch() {
    local branch=$1
    local workDir
    workDir=$(mktemp -d)

    echo "Looking for branch ${branch} of ansible-devops on GitHub"
    if ! curl -fsSL "https://github.com/ibm-mas/ansible-devops/archive/refs/heads/${branch}.tar.gz" -o "${workDir}/ansible-devops.tar.gz"; then
        echo "Branch ${branch} of ansible-devops not found"
        rm -rf "${workDir}"
        return 1
    fi

    mkdir "${workDir}/src"
    tar -xzf "${workDir}/ansible-devops.tar.gz" -C "${workDir}/src" --strip-components=1 || { rm -rf "${workDir}"; return 1; }

    if [[ ! -e "${workDir}/src/build/bin/build-collection.sh" || ! -e "${workDir}/src/ibm/mas_devops/galaxy.yml" ]]; then
        echo "Branch ${branch} of ansible-devops does not contain the collection build script"
        rm -rf "${workDir}"
        return 1
    fi

    # Build the collection exactly as ansible-devops CI does, keeping the version that is set in galaxy.yml
    (
        cd "${workDir}/src" || exit 1
        export DEV_MODE=true
        export GITHUB_WORKSPACE="${workDir}/src"
        export VERSION=$(yq '.version' ibm/mas_devops/galaxy.yml)
        bash build/bin/build-collection.sh
    ) || { echo "Failed to build ansible-devops branch ${branch}"; rm -rf "${workDir}"; return 1; }

    ansible-galaxy collection install "${workDir}"/src/ibm/mas_devops/ibm-mas_devops-*.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
    local rc=$?
    rm -rf "${workDir}"
    return $rc
}

# If the local file is present, defer to this
# Otherwise, build the matching branch from GitHub
# Otherwise, install the most recent version from Galaxy
if [[ -e /tmp/install/ibm-mas_devops.tar.gz ]]; then
    echo "Installing local build of ansible-devops from archive"
    ansible-galaxy collection install /tmp/install/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
elif [[ "$GITHUB_REF_TYPE" == "branch" ]] && installFromBranch "${GITHUB_REF_NAME}"; then
    echo "Installed matching branch build (${GITHUB_REF_NAME}) of ansible-devops from GitHub"
elif [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
    echo "Installing release build of ansible-devops from Galaxy (branch build)"
    ansible-galaxy collection install ibm.mas_devops
else
    echo "Installing release build of ansible-devops from Galaxy (tag build)"
    ansible-galaxy collection install ibm.mas_devops
fi
