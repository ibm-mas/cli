FROM registry.access.redhat.com/ubi8/python-39
ARG VERSION_LABEL
# ----- Start as "default" user ----------------------------------------------
# Running as userId = default
# HOME=/opt/app-root

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
    bash /tmp/install/install-aws.sh && \
    bash /tmp/install/install-helm.sh && \
    rm -rf /tmp/install && \
    rm /opt/app-root/src/.wget-hsts /opt/app-root/src/README.md /opt/app-root/src/LICENSE

# 4. Install tini
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini


# 6. Copy basics
USER default
COPY --chown=default:root app-root/* ${HOME}/
COPY --chown=default:root mascli /mascli
COPY --chown=default:root usr/bin/* /usr/bin

# 7. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.9/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1

# 8. Install Ansible collections -- do this last for efficient dev builds
COPY --chown=default:root install-ansible /tmp/install-ansible
RUN umask 0002 && \
    bash /tmp/install-ansible/install-ansible-collections.sh && \
    rm -rf /tmp/install-ansible

# 9. Set file permissions to be developer (hack) friendly
RUN chmod -R ug+rwx ${HOME}/env.sh && \
    chmod -R ug+rwx ${HOME}/.ansible && \
    chmod +x ${HOME}/run-playbook.sh && \
    chmod +x ${HOME}/run-role.sh && \
    chmod -R ug+w /mascli && \
    chmod +x /mascli/mas && \
    chmod +x /mascli/must-gather/* && \
    chmod +x /opt/app-root/src/.bashrc && \
    chmod +x /usr/bin/gather && \
    chmod -R g+w $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/ansible-devops 


# 10. Switch to root user
# Running an non-root user makes using the container with docker run and mounted volumes
# more difficult, users have to add -u root anyway, so just leave the active user as root
USER root

# 11. Setup working environment
WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash
