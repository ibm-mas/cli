FROM quay.io/ibmmas/cli-base:latest
ARG VERSION_LABEL

# Auto-expire the image in quay.io after 3 weeks
LABEL quay.expires-after=3w

# 1. Copy basics
COPY app-root/src/ /opt/app-root/src/
COPY mascli/ /mascli/
COPY masfvt/ /masfvt/
COPY usr/bin/ /usr/bin/

# 2. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.12/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    PATH="/mascli:${PATH}" \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1 \
    PYTHONWARNINGS="ignore:Unverified HTTPS request"

# 3. Install Python packages
# 4. Install Ansible collections
# 5. Disable ibmcloud cli's new version check
# 6. Set file permissions to be developer (hack) friendly
COPY install /tmp/install
RUN --mount=type=secret,id=ARTIFACTORY_TOKEN \
    --mount=type=secret,id=ARTIFACTORY_GENERIC_RELEASE_URL \
    --mount=type=secret,id=GITHUB_REF_NAME \
    --mount=type=secret,id=GITHUB_REF_TYPE \
    umask 0002 && \
    export ARTIFACTORY_TOKEN=$(cat /run/secrets/ARTIFACTORY_TOKEN 2>/dev/null || echo "") && \
    export ARTIFACTORY_GENERIC_RELEASE_URL=$(cat /run/secrets/ARTIFACTORY_GENERIC_RELEASE_URL 2>/dev/null || echo "") && \
    export GITHUB_REF_NAME=$(cat /run/secrets/GITHUB_REF_NAME 2>/dev/null || echo "") && \
    export GITHUB_REF_TYPE=$(cat /run/secrets/GITHUB_REF_TYPE 2>/dev/null || echo "") && \
    ls /tmp/install && \
    bash /tmp/install/install-python-packages.sh && \
    bash /tmp/install/install-ansible-collections.sh && \
    bash /tmp/install/permissions-updates.sh && \
    ibmcloud config --check-version=false && \
    ln -s /opt/app-root/lib/python3.12/site-packages /mascli/site-packages && \
    rm -rf /tmp/install
