#!/bin/bash

ansible-galaxy collection install -r /tmp/install-ansible/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

if [[ -e /tmp/install-ansible/ibm-mas_devops.tar.gz ]]; then
    ansible-galaxy collection install /tmp/install-ansible/ibm-mas_devops.tar.gz -p $ANSIBLE_COLLECTIONS_PATH
elif [[ "${GITHUB_REF_TYPE}" == "branch" ]]; then
    ANSIBLE_COLLECTION_FILE=ibm-mas_devops-13.7.0-pre.improve-build-system.tar.gz
    echo $ANSIBLE_COLLECTION_FILE
    wget --header="Authorization:Bearer $ARTIFACTORY_TOKEN" $ARTIFACTORY_GENERIC_RELEASE_URL/ibm-mas/ansible-devops/$ANSIBLE_COLLECTION_FILE
    ansible-galaxy collection install $ANSIBLE_COLLECTION_FILE -p $ANSIBLE_COLLECTIONS_PATH
    # mv $ANSIBLE_COLLECTION_FILE $ANSIBLE_COLLECTIONS_PATH/ibm-mas_devops.tar.gz 
    # ansible-galaxy collection install $ANSIBLE_COLLECTIONS_PATH/ibm-mas_devops.tar.gz
else
    ansible-galaxy collection install ibm.mas_devops
fi
