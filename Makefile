#!/bin/bash

.PHONY: ansible-build ansible-install ansible-all docker-build docker-run docker-all clean

.DEFAULT_GOAL := all

ansible-build:
	ansible-galaxy collection build --output-path image/cli ../ansible-devops/ibm/mas_devops --force
	ansible-galaxy collection build --output-path image/cli ../ansible-airgap/ibm/mas_airgap --force
	mv image/cli/ibm-mas_devops-11.0.0.tar.gz image/cli/ibm-mas_devops.tar.gz
	mv image/cli/ibm-mas_airgap-2.0.0.tar.gz image/cli/ibm-mas_airgap.tar.gz
ansible-install:
	ansible-galaxy collection install image/cli/ibm-mas_devops.tar.gz --force --no-deps
	ansible-galaxy collection install image/cli/ibm-mas_airgap.tar.gz --force --no-deps
ansible-all: ansible-build ansible-install

docker-build:
	DEV_MODE=true VERSION=local build/bin/build-tekton.sh
	docker build -t quay.io/ibmmas/cli:local image/cli
docker-run:
	docker run -ti cli:local
docker-all: docker-build docker-run

all: ansible-all docker-all

clean:
	rm image/cli/bin/ibm-mas_devops.tar.gz
	rm image/cli/bin/ibm-mas_airgap.tar.gz
