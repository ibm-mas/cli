FROM quay.io/ibmmas/cli-base:latest
ARG VERSION_LABEL

# Auto-expire the image in quay.io after 3 weeks
LABEL quay.expires-after=3w

# 1. Copy basics
COPY app-root/src/ /opt/app-root/src/
COPY rbac/ /opt/app-root/src/rbac/
COPY mascli/ /mascli/
COPY masfvt/ /masfvt/
COPY usr/bin/ /usr/bin/

# 2. Set up Environment
# VIRTUAL_ENV_DISABLE_PROMPT will stop built-in PS1 munging, we already set it to what we want
# MAS_CLIPBOARD=osc52 makes the interactive wizards copy generated commands via the OSC 52
# terminal escape sequence, which the host terminal emulator turns into a clipboard write --
# a container has no clipboard of its own. Override with -e MAS_CLIPBOARD=off where the
# terminal does not support OSC 52.
# TEXTUAL_COLOR_SYSTEM=truecolor makes the TUI emit 24-bit colour escape sequences instead of
# downsampling to the terminal's detected colour system: container sessions (oc rsh / docker
# exec) lose the COLORTERM hint and often carry a plain TERM, so detection falls back to the
# 256-colour cube and renders the theme palette duller than the same terminal does locally.
# The sequences pass through the container's pty untouched, so the host terminal's capability
# is what matters. Override with -e TEXTUAL_COLOR_SYSTEM=256 (or NO_COLOR) where needed.
ENV ANSIBLE_COLLECTIONS_PATH=/opt/app-root/lib64/python3.12/site-packages/ansible_collections \
    ANSIBLE_CONFIG=/opt/app-root/src/ansible.cfg \
    MAS_CLIPBOARD=osc52 \
    PATH="/mascli:${PATH}" \
    TEXTUAL_COLOR_SYSTEM=truecolor \
    VERSION=${VERSION_LABEL:-x.y.z} \
    VIRTUAL_ENV_DISABLE_PROMPT=1 \
    PYTHONWARNINGS="ignore:Unverified HTTPS request"

# 3. Install Python packages
# 4. Install Ansible collections
# 5. Copy the Pre-Install RBAC files that are bundled in the mas-cli package into /opt/app-root/rbac
# 6. Disable ibmcloud cli's new version check
# 7. Set file permissions to be developer (hack) friendly (must run after ibmcloud config so ~/.bluemix is covered)
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
    cp -r /opt/app-root/lib/python3.12/site-packages/mas/cli/rbac/preinstall/. /opt/app-root/rbac/ && \
    ibmcloud config --check-version=false && \
    bash /tmp/install/permissions-updates.sh && \
    ln -s /opt/app-root/lib/python3.12/site-packages /mascli/site-packages && \
    rm -rf /tmp/install
