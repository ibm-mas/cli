FROM registry.access.redhat.com/ubi8/ubi-minimal

# Update OS packages
RUN microdnf update && microdnf upgrade -y
RUN microdnf install -y wget nano tar gzip ncurses

# Install OpenShift CLI 4.8.35
RUN wget -q https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.8.35/openshift-client-linux.tar.gz && \
    tar -zxf openshift-client-linux.tar.gz && \
    mv oc /usr/local/bin/ && \
    mv kubectl /usr/local/bin/ && \
    rm -rf openshift-client-linux.tar.gz

COPY bin ${HOME}/installer/bin
RUN chmod u+x ${HOME}/installer/bin/mas
ENV PATH="${HOME}/installer/bin:${PATH}"
CMD mas install
