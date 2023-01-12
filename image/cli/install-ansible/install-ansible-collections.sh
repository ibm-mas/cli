#!/bin/bash

ansible-galaxy collection install -r /tmp/install-ansible/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

if [[ -e /tmp/install-ansible/ibm-mas_devops.tar.gz ]]
then ansible-galaxy collection install /tmp/install-ansible/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
else ansible-galaxy collection install ibm.mas_devops:==12.7.0-pre.jancat
fi
