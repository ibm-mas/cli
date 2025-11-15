#!/bin/bash

python3 -m pip install pip --upgrade

# We always install the version of the mas-cli package that we just built
python3 -m pip install /tmp/install/mas_cli.tar.gz

if [[ -e /tmp/install/mas_devops.tar.gz ]]; then
    # If we have copied a pre-built version of the mas_devops collection then use that,
    # otherwise we will use the latest version that was installed when we installed the mas-cli package above
    echo "Installing local build of python-devops from archive"
    python3 -m pip install /tmp/install/mas_devops.tar.gz
elif [[ "$GITHUB_REF_NAME" != "master" ]] && [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
    # Otherwise, if this is a non-master branch build, try to install from a matching branch of python-devops
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/ibm-mas/python-devops/branches/${GITHUB_REF_NAME}")

    if [[ "${RESPONSE}" == "200" ]]; then
        echo "Installing development build of python-devops from GitHub branch ${GITHUB_REF_NAME}"
        python3 -m pip install "git+https://github.com/ibm-mas/python-devops.git@${GITHUB_REF_NAME}"
    fi
fi
