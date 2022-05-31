FROM quay.io/ibmmas/ansible-airgap:1.1.0-pre.fixtsm

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini

COPY bin /installer/bin
COPY .bashrc /opt/app-root/src/.bashrc

RUN chmod +x /tini && \
    chmod u+x /installer/bin/mas && \
    chmod u+x /opt/app-root/src/.bashrc && \
    ln -s /opt/app-root/lib/python3.8/site-packages/ansible_collections/ibm/mas_airgap /installer/airgap && \
    ln -s /opt/app-root/lib/python3.8/site-packages/ansible_collections/ibm/mas_devops /installer/devops

ENV PATH="/installer/bin:${PATH}"
WORKDIR /installer

ENTRYPOINT ["/tini", "--"]
CMD bash

ARG VERSION_LABEL
ENV VERSION $VERSION_LABEL
