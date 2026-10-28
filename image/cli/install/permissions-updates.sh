#!/bin/bash
set -x
set -e

chmod -R ug+rwx /opt/app-root/src/env.sh
chmod -R ug+rwx /opt/app-root/src/.ansible
chmod +x /opt/app-root/src/*.sh
chmod +x /opt/app-root/src/.bashrc
chmod -R ug+w /mascli
chmod +x /mascli/mas
chmod +x /mascli/debug/*
chmod +x /mascli/backup-restore/*
# Only chmod /masfvt if it exists
if [ -d /masfvt ]; then
  chmod -R ug+w /masfvt
fi
chmod +x /usr/bin/gather
chmod -R g+w $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops
# The ibmcloud CLI reads & writes its config (including plugins/config.json) on every command, including
# "ibmcloud login".  Pods run as an arbitrary UID in the root group, so the whole tree must be group-writable
if [ -d /opt/app-root/src/.bluemix ]; then
  chgrp -R 0 /opt/app-root/src/.bluemix
  chmod -R g+rwX /opt/app-root/src/.bluemix
fi
ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops
