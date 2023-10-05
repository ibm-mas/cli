#!/bin/bash

ansible-galaxy collection install -r /tmp/install-ansible/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

git clone -b MASCORE-24 https://github.com/yuvraj-vansure/ansible-devops.git
export ANSIBLE_DEVOPS_PATH=ansible-devops/ibm/mas_devops

cd $ANSIBLE_DEVOPS_PATH
ansible-galaxy collection build
ansible-galaxy collection install ibm-mas_devops-*.tar.gz --ignore-certs --force

rm ibm-mas_devops-*.tar.gz
#if [[ -e /tmp/install-ansible/ibm-mas_devops.tar.gz ]]
#then ansible-galaxy collection install /tmp/install-ansible/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
#else ansible-galaxy collection install ibm.mas_devops
#fi
