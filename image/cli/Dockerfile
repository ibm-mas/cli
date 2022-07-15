FROM quay.io/ibmmas/ansible-airgap:latest

ARG VERSION_LABEL

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini

COPY bin /mascli/bin
COPY .bashrc /opt/app-root/src/.bashrc

RUN chmod +x /tini && \
    chmod +x /mascli/bin/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /mascli/airgap && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/devops

# Add this when we need to install a newer version of mas_devops than is contained in the newest version of ansible-airgap
# RUN ansible-galaxy collection install ibm.mas_devops:10.6.0 --no-deps

ENV PATH="/mascli/bin:${PATH}" \
    VERSION=$VERSION_LABEL

WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash
