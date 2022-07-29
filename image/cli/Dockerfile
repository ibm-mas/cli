FROM registry.access.redhat.com/ubi8/python-39 AS release_build

ARG VERSION_LABEL
ARG FOO
# ----- Start as "default" user -----------------------------------------------
# Running as userId = default
# HOME=/opt/app-root

# ----- Switch to root user ---------------------------------------------------
# If we switch back to the "default" user then mounts in /workspace/xxx are
# not writeable, there may be a way to fix this so that we don't have to leave
# the active user as root, haven't looked into this yet.
USER root

# 1. Upgrade system packages
RUN dnf update -y --skip-broken --nobest &&\
    dnf upgrade -y --skip-broken --nobest &&\
    dnf install nano -y &&\
    dnf clean all

# 2. Upgrade pip, install wheel, then install Python modules
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel &&\
    python3 -m pip install --no-cache-dir -r requirements.txt

# 3. Install required tools
COPY install /tmp/install
RUN chmod u+x /tmp/install/*.sh && \
    /tmp/install/install-oc.sh && \
    /tmp/install/install-ibmcloud.sh && \
    /tmp/install/install-skopeo.sh && \
    rm -rf /tmp/install

# 4. Install tini
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

# 5. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
COPY app-root/* ${HOME}/
COPY bin /mascli/bin
COPY .bashrc /opt/app-root/src/.bashrc
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.9/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli/bin:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1

# 6. Install Ansible Collections
RUN ansible-galaxy collection install -r ${HOME}/requirements.yml -p $ANSIBLE_COLLECTIONS_PATH

# 7. Set file permissions in /opt/app-root & setup symlink to our collection
RUN chmod -R ug+rwx ${HOME}/env.sh &&\
    chmod -R ug+rwx ${HOME}/.ansible &&\
    chmod +x ${HOME}/run-playbook.sh &&\
    chmod +x ${HOME}/run-role.sh &&\
    chmod +x ${HOME}/clear-mustgather-workspace.sh && \
    chmod +x /mascli/bin/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /opt/app-root/devops && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /opt/app-root/airgap

# 8. Setup working environment
WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash

FROM release_build as dev_build

COPY ibm-mas_devops.tar.gz /tmp
COPY ibm-mas_airgap.tar.gz /tmp
RUN ansible-galaxy collection install /tmp/ibm-mas_devops.tar.gz --force --no-deps
RUN ansible-galaxy collection install /tmp/ibm-mas_airgap.tar.gz --force --no-deps
