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

# 3. Install Python packages
# 4. Install Ansible collections
# 5. Set file permissions to be developer (hack) friendly
COPY install /tmp/install
RUN umask 0002 && \
    ls /tmp/install && \
    bash /tmp/install/install-python-packages.sh && \
    bash /tmp/install/install-ansible-collections.sh && \
    bash /tmp/install/permissions-updates.sh && \
    rm -rf /tmp/install
