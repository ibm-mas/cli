#!/bin/bash

.PHONY: ansible-build ansible-install ansible tekton docker run clean create delete exec

.DEFAULT_GOAL := all

ansible-build:
	ansible-galaxy collection build --output-path image/cli/install-ansible ../ansible-devops/ibm/mas_devops --force
	mv image/cli/install-ansible/ibm-mas_devops-13.0.0.tar.gz image/cli/install-ansible/ibm-mas_devops.tar.gz
ansible-install:
	ansible-galaxy collection install image/cli/install-ansible/ibm-mas_devops.tar.gz --force --no-deps
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
	rm image/cli/bin/templates/ibm-mas-tekton.yml

create:
	oc apply -f tmp/deployment.yml
delete:
	oc delete pod $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}")
exec:
	oc exec -ti $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}") -- bash
