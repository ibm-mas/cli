FROM quay.io/ibmmas/cli-base:1.1.0-pre.gitops
ARG VERSION_LABEL

# 1. Copy basics
COPY app-root/* ${HOME}/
COPY mascli /mascli
COPY usr/bin/* /usr/bin

# 2. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.9/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1

# 3. Install Ansible collections -- do this last for efficient dev builds
# 4. Set file permissions to be developer (hack) friendly
COPY install-ansible /tmp/install-ansible
RUN umask 0002 && \
    bash /tmp/install-ansible/install-ansible-collections.sh && \
    rm -rf /tmp/install-ansible && \
    chmod -R ug+rwx ${HOME}/env.sh && \
    chmod -R ug+rwx ${HOME}/.ansible && \
    chmod +x ${HOME}/run-playbook.sh && \
    chmod +x ${HOME}/run-role.sh && \
    chmod +x ${HOME}/copy-certificates.sh && \
    chmod -R ug+w /mascli && \
    chmod +x /mascli/mas && \
    chmod +x /mascli/must-gather/* && \
    chmod +x /mascli/backup-restore/* && \
    chmod +x /opt/app-root/src/.bashrc && \
    chmod +x /usr/bin/gather && \
    chmod -R g+w $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops
