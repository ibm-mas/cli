#!/bin/bash

.PHONY: ansible-build ansible-install ansible tekton docker run clean create delete exec

.DEFAULT_GOAL := all

ansible-build:
	ansible-galaxy collection build --output-path image/cli/install-ansible ../ansible-devops/ibm/mas_devops --force
	ansible-galaxy collection build --output-path image/cli/install-ansible ../ansible-airgap/ibm/mas_airgap --force
	mv image/cli/install-ansible/ibm-mas_devops-11.0.0.tar.gz image/cli/install-ansible/ibm-mas_devops.tar.gz
	mv image/cli/install-ansible/ibm-mas_airgap-3.0.0.tar.gz image/cli/install-ansible/ibm-mas_airgap.tar.gz
ansible-install:
	ansible-galaxy collection install image/cli/install-ansible/ibm-mas_devops.tar.gz --force --no-deps
	ansible-galaxy collection install image/cli/install-ansible/ibm-mas_airgap.tar.gz --force --no-deps
ansible: ansible-build ansible-install

tekton:
	DEV_MODE=true build/bin/build-tekton.sh

docker:
	docker build -t quay.io/ibmmas/cli:local image/cli

all: ansible tekton docker

run:
	docker run -ti cli:local

clean:
	rm image/cli/install-ansible/ibm-mas_devops.tar.gz
	rm image/cli/install-ansible/ibm-mas_airgap.tar.gz
	rm image/cli/bin/templates/ibm-mas-tekton.yaml

create:
	oc -n default apply -f deployment.yaml
delete:
	oc -n default delete pod $(shell oc -n default get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}")
exec:
	oc -n default exec -ti $(shell oc -n default get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}") -- bash
