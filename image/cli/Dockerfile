FROM quay.io/ibmmas/cli-base:latest
ARG VERSION_LABEL

# 1. Copy basics
COPY app-root/src/ /opt/app-root/src/
COPY mascli/ /mascli/
COPY masfvt/ /masfvt/
COPY usr/bin/ /usr/bin/

# 2. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.9/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1

# 3. Install Ansible collections -- do this last for efficient dev builds
# 4. Set file permissions to be developer (hack) friendly
COPY install-ansible /tmp/install
COPY install-python /tmp/install-python
RUN umask 0002 && \
    ls /tmp/install-python && \
    python3 -m pip install /tmp/install-python/mas_devops-1.0.0.tar.gz && \
    rm -rf /tmp/install-python && \
    bash /tmp/install-ansible/install-ansible-collections.sh && \
    rm -rf /tmp/install-ansible && \
    chmod -R ug+rwx /opt/app-root/src/env.sh && \
    chmod -R ug+rwx /opt/app-root/src/.ansible && \
    chmod +x /opt/app-root/src/*.sh && \
    chmod +x /opt/app-root/src/.bashrc && \
    chmod -R ug+w /mascli && \
    chmod +x /mascli/mas && \
    chmod +x /mascli/*.py && \
    chmod +x /mascli/must-gather/* && \
    chmod +x /mascli/backup-restore/* && \
    chmod -R ug+w /masfvt && \
    chmod +x /usr/bin/gather && \
    chmod -R g+w $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops
