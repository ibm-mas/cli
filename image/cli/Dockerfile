FROM quay.io/ibmmas/ansible-airgap:1.2.0-pre.mirrorwork

ARG VERSION_LABEL

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini

COPY bin /mascli/bin
COPY .bashrc /opt/app-root/src/.bashrc

# ibm.mas_devops 10.1.0 is already installed in the base image, but as we haven't
# updated ansible-airgap to include the newest release of ansible-devops yet
# we want to do an additional install of mas_devops to get the latest fixes
# We won't always need this extra install, only when mas_devops release is newer
# than mas_airgap release.
RUN chmod +x /tini && \
    chmod +x /mascli/bin/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /mascli/airgap && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/devops
#    ansible-galaxy collection install ibm.mas_devops:10.2.0 --no-deps

ENV PATH="/mascli/bin:${PATH}" \
    VERSION=$VERSION_LABEL

WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash
