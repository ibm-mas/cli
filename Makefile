#!/bin/bash

.PHONY: ansible-build ansible-install ansible python-build python-build-devops python-build-cli tekton docker run clean create delete exec

.DEFAULT_GOAL := all

ansible-build:
	ansible-galaxy collection build --output-path image/cli/install ../ansible-devops/ibm/mas_devops --force
	mv image/cli/install/ibm-mas_devops-100.0.0.tar.gz image/cli/install/ibm-mas_devops.tar.gz
ansible-install:
	ansible-galaxy collection install image/cli/install/ibm-mas_devops.tar.gz --force --no-deps
ansible: ansible-build ansible-install

python-build-cli:
	cd python && python3 -m build
	cp python/dist/mas_cli-100.0.0.tar.gz image/cli/install/mas_cli.tar.gz

python-build-devops:
	cd ../python-devops && python3 -m build
	cp ../python-devops/dist/mas_devops-100.0.0.tar.gz image/cli/install/mas_devops.tar.gz

python-build: python-build-devops python-build-cli

tekton:
	DEV_MODE=true build/bin/build-tekton.sh

docker:
	docker build -t quay.io/ibmmas/cli:local image/cli

all: ansible tekton docker

run:
	docker run -ti cli:local

clean:
	rm image/cli/install/ibm-mas_devops.tar.gz
	rm image/cli/bin/templates/ibm-mas-tekton.yaml

create:
	oc apply -f tmp/deployment.yaml
delete:
	oc delete pod $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}")
exec:
	oc exec -ti $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}") -- bash
