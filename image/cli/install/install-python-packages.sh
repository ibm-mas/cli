#!/bin/bash

python3 -m pip install pip --upgrade

# We always install the version of the mas-cli package that we just built
python3 -m pip install /tmp/install/mas_cli.tar.gz

# If we have copied a pre-built version of the mas_devops collection then use that,
# otherwise we will use the latest version that was installed when we installed the mas-cli package above
if [[ -e /tmp/install/mas_devops.tar.gz ]]; then
  python3 -m pip install /tmp/install/mas_devops.tar.gz
fi
