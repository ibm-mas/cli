#!/bin/bash

ansible-galaxy collection install -r /tmp/install-ansible/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

if [[ -e /tmp/install/ibm-mas-devops.tar.gz ]]
then ansible-galaxy collection install /tmp/install-ansible/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
else ansible-galaxy collection install ibm.mas_devops -p $ANSIBLE_COLLECTIONS_PATH
fi

if [[ -e /tmp/install/ibm-mas-airgap.tar.gz ]]
then ansible-galaxy collection install /tmp/install-ansible/ibm-mas_airgap.tar.gz --force --no-deps -p $ANSIBLE_COLLECTIONS_PATH
else ansible-galaxy collection install ibm.mas_airgap -p $ANSIBLE_COLLECTIONS_PATH
fi
