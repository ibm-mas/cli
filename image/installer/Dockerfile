FROM quay.io/ibmmas/ansible-airgap:1.1.0-pre.master

ARG VERSION_LABEL

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini

COPY bin /installer/bin
COPY .bashrc /opt/app-root/src/.bashrc

RUN chmod +x /tini && \
    chmod +x /installer/bin/mas && \
    chmod +x /opt/app-root/src/.bashrc && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_airgap /installer/airgap && \
    ln -s $ANSIBLE_COLLECTIONS_PATH/ibm/mas_devops /installer/devops

ENV PATH="/installer/bin:${PATH}" \
    VERSION $VERSION_LABEL

WORKDIR /installer
ENTRYPOINT ["/tini", "--"]
CMD bash
