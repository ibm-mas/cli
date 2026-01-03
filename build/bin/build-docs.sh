#!/bin/bash

if [[ "$GITHUB_REF_TYPE" == "branch" ]]; then
  # python-devops main branch is named "stable" rather than "master"
  PYTHON_BRANCH_NAME=$GITHUB_REF_NAME
  if [[ "$GITHUB_REF_NAME" == "master" ]]; then
    PYTHON_BRANCH_NAME=stable
  fi

  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/ibm-mas/python-devops/branches/${PYTHON_BRANCH_NAME}")

  if [[ "${RESPONSE}" == "200" ]]; then
    echo "Installing development build of python-devops from GitHub branch ${PYTHON_BRANCH_NAME}"
  else
    echo "Branch ${PYTHON_BRANCH_NAME} not found, defaulting to stable"
    PYTHON_BRANCH_NAME=stable
  fi

  python3 -m pip install "git+https://github.com/ibm-mas/python-devops.git@${PYTHON_BRANCH_NAME}"
else
  echo "Installing latest release of mas-devops from PyPi"
  python3 -m pip install mas-devops
fi


#Fetch CLI repo version
CLI_LATEST_VERSION=$(curl -s https://api.github.com/repos/ibm-mas/cli/releases/latest | jq -r '.name')

# Fetch all amd64 catalog files
LATEST_CATALOG=$(curl -s "https://api.github.com/repos/ibm-mas/cli/contents/catalogs?ref=master" \
  | jq -r '[.[] | select(.name | endswith("amd64.yaml")) | .name | sub("\\.yaml$"; "")] | sort | .[-1]')
PREVIOUS_CATALOG=$(curl -s "https://api.github.com/repos/ibm-mas/cli/contents/catalogs?ref=master" \
  | jq -r '[.[] | select(.name | endswith("amd64.yaml")) | .name | sub("\\.yaml$"; "")] | sort | .[-2]')

# Static Variables for channel versioning
MAS_LATEST_CHANNEL="9.1.x"
MAS_PREVIOUS_CHANNEL="9.0.x"

# Logging values
echo "CLI_LATEST_VERSION:     $CLI_LATEST_VERSION"
echo "LATEST_CATALOG:         $LATEST_CATALOG"
echo "PREVIOUS_CATALOG:       $PREVIOUS_CATALOG"
echo "MAS_LATEST_CHANNEL:     $MAS_LATEST_CHANNEL"
echo "MAS_PREVIOUS_CHANNEL:   $MAS_PREVIOUS_CHANNEL"

# Automated Versioning Search
find docs -type f -name '*.md' -exec sed -i \
  -e "s/@@CLI_LATEST_VERSION@@/$CLI_LATEST_VERSION/g" \
  -e "s/@@MAS_PREVIOUS_CHANNEL@@/$MAS_PREVIOUS_CHANNEL/g" \
  -e "s/@@MAS_PREVIOUS_CATALOG@@/$PREVIOUS_CATALOG/g" \
  -e "s/@@MAS_LATEST_CHANNEL@@/$MAS_LATEST_CHANNEL/g" \
  -e "s/@@MAS_LATEST_CHANNEL_MANAGE@@/$MAS_LATEST_CHANNEL/g" \
  -e "s/@@MAS_LATEST_CATALOG@@/$LATEST_CATALOG/g" \
  {} +

python -m pip install -q mkdocs mkdocs-carbon mkdocs-glightbox mkdocs-redirects
python -m pip install -e mkdocs_plugins
mkdocs build --clean --strict
