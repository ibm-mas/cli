#!/bin/bash

echo "Install Ansible Collections"
echo "==========================="
echo "GitHub reference = ${GITHUB_REF_TYPE}/${GITHUB_REF_NAME}"
echo "Artifactory = ${ARTIFACTORY_GENERIC_RELEASE_URL}"
echo "Contents of /tmp/install/:"
ls -l /tmp/install/
echo ""

# If the local file is present, defer to this
# Otherwise, check for a matching branch name in Artifactory
# Otherwise, install the most recent version from Galaxy
if [[ -e /tmp/install/ibm-mas_devops.tar.gz ]]; then
    echo "Installing local build of ansible-devops from archive"
    ansible-galaxy collection install /tmp/install/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
elif [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
    # Download and validate the archive
    BRANCH_TARGET_URL="${ARTIFACTORY_GENERIC_RELEASE_URL}/ibm-mas/ansible-devops/branches/ibm-mas_devops-${GITHUB_REF_NAME}.tar.gz"
    curl -H "Authorization:Bearer $ARTIFACTORY_TOKEN" $BRANCH_TARGET_URL -o /tmp/install/ibm-mas_devops.tar.gz
    tar -tzf /tmp/install/ibm-mas_devops.tar.gz > /dev/null
    if [[ "$?" == "0" ]]; then
        echo "Installing matching branch build (${GITHUB_REF_NAME}) of ansible-devops from Artifactory"
        ansible-galaxy collection install /tmp/install/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
    else
        echo "Installing release build of ansible-devops from Galaxy (branch build)"
        ansible-galaxy collection install ibm.mas_devops
    fi
else
    echo "Installing release build of ansible-devops from Galaxy (tag build)"
    ansible-galaxy collection install ibm.mas_devops
fi
