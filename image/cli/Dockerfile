FROM registry.access.redhat.com/ubi8/python-39
ARG VERSION_LABEL
# ----- Start as "default" user -----------------------------------------------
# Running as userId = default
# HOME=/opt/app-root

# ----- Switch to root user ---------------------------------------------------
# If we switch back to the "default" user then mounts in /workspace/xxx are
# not writeable, there may be a way to fix this so that we don't have to leave
# the active user as root, haven't looked into this yet.

# 1. Upgrade system packages
USER root
RUN dnf update -y --skip-broken --nobest &&\
    dnf upgrade -y --skip-broken --nobest &&\
    dnf install nano jq -y &&\
    dnf clean all

# 2. Upgrade pip, install wheel, then install Python modules
USER default
COPY --chown=default:root install /tmp/install
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel &&\
    python3 -m pip install --no-cache-dir -r /tmp/install/requirements.txt

# 3. Install required tools & Ansible collections
USER root
RUN umask 0002 && \
    bash /tmp/install/install-oc.sh && \
    bash /tmp/install/install-ibmpak.sh && \
    bash /tmp/install/install-ibmcloud.sh && \
    bash /tmp/install/install-skopeo.sh && \
    rm -rf /tmp/install

# 4. Install tini
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

# 5. Copy basics
USER default
COPY --chown=default:root app-root/* ${HOME}/
COPY --chown=default:root mascli /mascli
COPY --chown=default:root .bashrc /opt/app-root/src/.bashrc

# 6. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.9/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1

# 7. Install Ansible collections -- do this last for efficient dev builds
COPY --chown=default:root install-ansible /tmp/install-ansible
RUN umask 0002 && \
    bash /tmp/install-ansible/install-ansible-collections.sh && \
    rm -rf /tmp/install-ansible

# 8. Set file permissions in /opt/app-root & /mascli & setup symlink to our collection
RUN chmod -R ug+rwx ${HOME}/env.sh &&\
    chmod -R ug+rwx ${HOME}/.ansible &&\
    chmod +x ${HOME}/run-playbook.sh &&\
    chmod +x ${HOME}/run-role.sh &&\
    chmod +x ${HOME}/clear-mustgather-workspace.sh && \
    chmod +x /mascli/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /mascli/ansible-airgap

# 8. Setup working environment
WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash
