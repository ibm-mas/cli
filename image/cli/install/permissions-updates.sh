#!/bin/bash
set -x
set -e

chmod -R ug+rwx /opt/app-root/src/env.sh
chmod -R ug+rwx /opt/app-root/src/.ansible
chmod +x /opt/app-root/src/*.sh
chmod +x /opt/app-root/src/.bashrc
chmod -R ug+w /mascli
chmod +x /mascli/mas
chmod +x /mascli/*.py
chmod +x /mascli/must-gather/*
chmod +x /mascli/backup-restore/*
chmod -R ug+w /masfvt
chmod +x /usr/bin/gather
chmod -R g+w $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops
ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops
