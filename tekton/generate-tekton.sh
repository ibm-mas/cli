#!/bin/bash

echo "=============================="
echo "Generate Install pipeline"
echo "=============================="
ansible-playbook generate-install.yml
echo
echo "=============================="
echo "Generate Upgrade Test pipeline"
echo "=============================="
ansible-playbook generate-upgrade-test.yml
