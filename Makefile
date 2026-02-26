#!/bin/bash

.PHONY: ansible-devops python python-devops python-cli tekton docker run clean create delete exec

.DEFAULT_GOAL := all

ansible-devops:
	ansible-galaxy collection build --output-path image/cli/install ../ansible-devops/ibm/mas_devops --force
	mv image/cli/install/ibm-mas_devops-100.0.0.tar.gz image/cli/install/ibm-mas_devops.tar.gz

# Tip: You can install this built collection using:
# ansible-galaxy collection install image/cli/install/ibm-mas_devops.tar.gz --force --no-deps

python-cli:
	cd python && python -m build
	cp python/dist/mas_cli-100.0.0.tar.gz image/cli/install/mas_cli.tar.gz

python-devops:
	cd ../python-devops && make install build
	cp ../python-devops/dist/mas_devops-100.0.0.tar.gz image/cli/install/mas_devops.tar.gz

python: python-devops python-cli

tekton:
	DEV_MODE=true build/bin/build-tekton.sh

tekton-test: tekton
	tekton/test.sh

docker:
	docker build -t quay.io/ibmmas/cli:100.0.0-pre.local image/cli

all: ansible-devops python tekton docker

run:
	docker run -ti quay.io/ibmmas/cli:100.0.0-pre.local

clean:
	rm image/cli/install/ibm-mas_devops.tar.gz
	rm image/cli/bin/templates/ibm-mas-tekton.yaml

create:
	oc apply -f tmp/deployment.yaml
delete:
	oc delete pod $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}")
exec:
	oc exec -ti $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}") -- bash

.PHONY: detect-secrets
detect-secrets:
	detect-secrets scan --update .secrets.baseline && detect-secrets audit .secrets.baseline
