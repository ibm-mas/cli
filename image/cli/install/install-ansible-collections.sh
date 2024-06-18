#!/bin/bash

ansible-galaxy collection install -r /tmp/install/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

if [[ -e /tmp/install/ibm-mas_devops.tar.gz ]]
then ansible-galaxy collection install /tmp/install/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
else ansible-galaxy collection install ibm.mas_devops
fi
