FROM quay.io/ibmmas/ansible-airgap:1.2.0

ARG VERSION_LABEL

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini

COPY bin /mascli/bin
COPY .bashrc /opt/app-root/src/.bashrc

RUN chmod +x /tini && \
    chmod +x /mascli/bin/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /mascli/airgap && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /mascli/devops && \
    ansible-galaxy collection install /mascli/bin/ibm-mas_devops.tar.gz --force --no-deps && \
    ansible-galaxy collection install /mascli/bin/ibm-mas_airgap.tar.gz --force --no-deps

ENV PATH="/mascli/bin:${PATH}" \
    VERSION=$VERSION_LABEL

WORKDIR /mascli
ENTRYPOINT ["/tini", "--"]
CMD bash
