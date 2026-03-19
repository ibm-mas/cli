#!/bin/bash

# ==============================================================================
# IBM MAS CLI - Makefile
# ==============================================================================
# This Makefile builds the IBM Maximo Application Suite (MAS) CLI container
# image and associated components including Ansible collections, Python packages,
# and Tekton pipelines.
#
# Prerequisites:
#   - ansible-galaxy (for Ansible collection builds)
#   - docker or podman (for container builds)
#   - oc (OpenShift CLI, for OCP deployments)
#   - Python 3.x with pip
#
# Quick Start:
#   make help      - Show all available targets
#   make all       - Build all components for local development
#   make all-ocp   - Build and push to OpenShift internal registry
#
# ==============================================================================

.PHONY: help ansible-devops python python-devops python-cli tekton tekton-ocp tekton-test docker build-and-push-ocp all all-ocp run clean create delete exec

.DEFAULT_GOAL := help

# ==============================================================================
# Help Target
# ==============================================================================

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ''
	@echo 'Common workflows:'
	@echo '  Local development:  make all'
	@echo '  OCP deployment:     make all-ocp'
	@echo '  Run locally:        make docker && make run'

# ==============================================================================
# Ansible Collection Targets
# ==============================================================================

ansible-devops: ## Build Ansible DevOps collection for MAS
	ansible-galaxy collection build --output-path image/cli/install ../ansible-devops/ibm/mas_devops --force
	mv image/cli/install/ibm-mas_devops-100.0.0.tar.gz image/cli/install/ibm-mas_devops.tar.gz
	# Tip: You can install this built collection using:
	# ansible-galaxy collection install image/cli/install/ibm-mas_devops.tar.gz --force --no-deps

# ==============================================================================
# Python Package Targets
# ==============================================================================

python-cli: ## Build Python CLI package
	cd python && make build
	cp python/dist/mas_cli-100.0.0.tar.gz image/cli/install/mas_cli.tar.gz

python-devops: ## Build Python DevOps package from external repository
	cd ../python-devops && make install build
	cp ../python-devops/dist/mas_devops-100.0.0.tar.gz image/cli/install/mas_devops.tar.gz

python: python-devops python-cli ## Build all Python packages (devops + cli)

# ==============================================================================
# Tekton Pipeline Targets
# ==============================================================================

tekton: ## Generate Tekton pipeline definitions for local use
	DEV_MODE=true build/bin/build-tekton.sh

tekton-ocp: ## Generate Tekton pipelines configured for your OCP internal registry
	@OCP_PROJECT=$$(oc project -q 2>/dev/null); \
	if [ -z "$$OCP_PROJECT" ]; then \
		echo "Error: Not logged into OCP cluster. Please run 'oc login' first."; \
		exit 1; \
	fi; \
	echo "Building Tekton resources for OCP project: $$OCP_PROJECT"; \
	DEV_MODE=true USE_OCP_REGISTRY=true OCP_PROJECT=$$OCP_PROJECT build/bin/build-tekton.sh

tekton-test: tekton ## Run Tekton pipeline tests
	tekton/test.sh

# ==============================================================================
# Container Image Targets
# ==============================================================================

docker: tekton ## Build Docker image locally with Tekton resources
	@echo "$${ARTIFACTORY_TOKEN:-}" > /tmp/.artifactory_token
	@echo "$${ARTIFACTORY_GENERIC_RELEASE_URL:-}" > /tmp/.artifactory_url
	@echo "$${GITHUB_REF_NAME:-local}" > /tmp/.github_ref_name
	@echo "$${GITHUB_REF_TYPE:-branch}" > /tmp/.github_ref_type
	DOCKER_BUILDKIT=1 docker build \
		--secret id=ARTIFACTORY_TOKEN,src=/tmp/.artifactory_token \
		--secret id=ARTIFACTORY_GENERIC_RELEASE_URL,src=/tmp/.artifactory_url \
		--secret id=GITHUB_REF_NAME,src=/tmp/.github_ref_name \
		--secret id=GITHUB_REF_TYPE,src=/tmp/.github_ref_type \
		-t quay.io/ibmmas/cli:100.0.0-pre.local image/cli
	@rm -f /tmp/.artifactory_token /tmp/.artifactory_url /tmp/.github_ref_name /tmp/.github_ref_type

build-and-push-ocp: ## Build image for OCP architecture and push to internal registry
	@echo "Detecting OCP cluster platform..."
	@OCP_ARCH=$$(oc get nodes -o jsonpath='{.items[0].status.nodeInfo.architecture}' 2>/dev/null); \
	if [ -z "$$OCP_ARCH" ]; then \
		echo "Error: Could not detect OCP cluster architecture"; \
		exit 1; \
	fi; \
	echo "OCP cluster architecture: $$OCP_ARCH"; \
	LOCAL_ARCH=$$(uname -m); \
	if [ "$$LOCAL_ARCH" = "x86_64" ]; then \
		LOCAL_ARCH="amd64"; \
	elif [ "$$LOCAL_ARCH" = "aarch64" ]; then \
		LOCAL_ARCH="arm64"; \
	fi; \
	echo "Local architecture: $$LOCAL_ARCH"; \
	CONTAINER_TOOL=$$(command -v podman 2>/dev/null || command -v docker 2>/dev/null); \
	if [ -z "$$CONTAINER_TOOL" ]; then \
		echo "Error: Neither podman nor docker found"; \
		exit 1; \
	fi; \
	echo "Building image for OCP platform linux/$$OCP_ARCH..."; \
	echo "$${ARTIFACTORY_TOKEN:-}" > /tmp/.artifactory_token; \
	echo "$${ARTIFACTORY_GENERIC_RELEASE_URL:-}" > /tmp/.artifactory_url; \
	echo "$${GITHUB_REF_NAME:-local}" > /tmp/.github_ref_name; \
	echo "$${GITHUB_REF_TYPE:-branch}" > /tmp/.github_ref_type; \
	DOCKER_BUILDKIT=1 $$CONTAINER_TOOL build \
		--platform linux/$$OCP_ARCH \
		--no-cache \
		--secret id=ARTIFACTORY_TOKEN,src=/tmp/.artifactory_token \
		--secret id=ARTIFACTORY_GENERIC_RELEASE_URL,src=/tmp/.artifactory_url \
		--secret id=GITHUB_REF_NAME,src=/tmp/.github_ref_name \
		--secret id=GITHUB_REF_TYPE,src=/tmp/.github_ref_type \
		-t quay.io/ibmmas/cli:100.0.0-pre.local image/cli || { echo "Error: Failed to build image"; exit 1; }; \
	rm -f /tmp/.artifactory_token /tmp/.artifactory_url /tmp/.github_ref_name /tmp/.github_ref_type; \
	echo "Pushing image to OCP internal registry..."; \
	OCP_REGISTRY=$$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}' 2>/dev/null); \
	if [ -z "$$OCP_REGISTRY" ]; then \
		echo "Error: Could not find OCP internal registry route. Exposing registry..."; \
		oc patch configs.imageregistry.operator.openshift.io/cluster --patch '{"spec":{"defaultRoute":true}}' --type=merge; \
		echo "Waiting for registry route to be created..."; \
		sleep 10; \
		OCP_REGISTRY=$$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}'); \
	fi; \
	if [ -z "$$OCP_REGISTRY" ]; then \
		echo "Error: Failed to get OCP registry route"; \
		exit 1; \
	fi; \
	echo "OCP Registry: $$OCP_REGISTRY"; \
	OCP_PROJECT=$$(oc project -q); \
	echo "Current project: $$OCP_PROJECT"; \
	CONTAINER_TOOL=$$(command -v podman 2>/dev/null || command -v docker 2>/dev/null); \
	if [ -z "$$CONTAINER_TOOL" ]; then \
		echo "Error: Neither podman nor docker found"; \
		exit 1; \
	fi; \
	TOOL_NAME=$$(basename $$CONTAINER_TOOL); \
	echo "Using container tool: $$TOOL_NAME"; \
	echo "Logging into OCP registry..."; \
	OCP_TOKEN=$$(oc whoami -t 2>/dev/null); \
	if [ -z "$$OCP_TOKEN" ]; then \
		echo "Error: Failed to get OCP token. Please ensure you are logged into the cluster with 'oc login'"; \
		exit 1; \
	fi; \
	echo "Authenticating with OCP token..."; \
	if [ "$$TOOL_NAME" = "podman" ]; then \
		echo "Using podman with --tls-verify=false for all operations"; \
		echo "$$OCP_TOKEN" | $$CONTAINER_TOOL login --tls-verify=false -u unused --password-stdin $$OCP_REGISTRY || { \
			echo "Error: Failed to login to OCP registry with token"; \
			echo "Trying alternative method with kubeadmin user..."; \
			$$CONTAINER_TOOL login --tls-verify=false -u kubeadmin -p "$$OCP_TOKEN" $$OCP_REGISTRY || { echo "Error: Failed to login to OCP registry"; exit 1; }; \
		}; \
	else \
		echo "$$OCP_TOKEN" | $$CONTAINER_TOOL login -u unused --password-stdin $$OCP_REGISTRY || { \
			echo "Error: Failed to login to OCP registry with token"; \
			echo "Trying alternative method with kubeadmin user..."; \
			$$CONTAINER_TOOL login -u kubeadmin -p "$$OCP_TOKEN" $$OCP_REGISTRY || { echo "Error: Failed to login to OCP registry"; exit 1; }; \
		}; \
	fi; \
	echo "Tagging image for OCP registry..."; \
	$$CONTAINER_TOOL tag quay.io/ibmmas/cli:100.0.0-pre.local $$OCP_REGISTRY/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild || { echo "Error: Failed to tag image"; exit 1; }; \
	echo "Pushing image to OCP registry..."; \
	if [ "$$TOOL_NAME" = "podman" ]; then \
		$$CONTAINER_TOOL push --tls-verify=false $$OCP_REGISTRY/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild || { echo "Error: Failed to push image"; exit 1; }; \
	else \
		echo "Using docker - attempting push..."; \
		if ! $$CONTAINER_TOOL push $$OCP_REGISTRY/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild 2>&1; then \
			echo "Docker push failed due to TLS verification, trying with skopeo..."; \
			if command -v skopeo >/dev/null 2>&1; then \
				skopeo copy --dest-tls-verify=false \
					docker-daemon:$$OCP_REGISTRY/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild \
					docker://$$OCP_REGISTRY/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild || { echo "Error: Failed to push image with skopeo"; exit 1; }; \
			else \
				echo "Error: Failed to push image and skopeo is not available"; \
				echo "Please either:"; \
				echo "  1. Use podman instead of docker (podman supports --tls-verify=false)"; \
				echo "  2. Install skopeo for TLS-verification-free push"; \
				echo "  3. Add $$OCP_REGISTRY to Docker's insecure-registries and restart Docker daemon"; \
				echo "  4. Add the OCP registry CA certificate to Docker's trusted certificates"; \
				exit 1; \
			fi; \
		fi; \
	fi; \
	echo "Image pushed successfully to:"; \
	echo "  image-registry.openshift-image-registry.svc:5000/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild" \
	echo ""

# ==============================================================================
# Composite Build Targets
# ==============================================================================

all: ansible-devops python tekton docker ## Build all components for local development (default)

all-ocp: ansible-devops python tekton-ocp build-and-push-ocp ## Build all components and push to your OCP registry
	@echo ""
	@echo "=========================================="
	@echo "Build complete for OCP deployment!"
	@echo "=========================================="
	@echo ""
	@echo "Your Tekton tasks are now configured to use:"
	@OCP_PROJECT=$$(oc project -q); \
	echo "  image-registry.openshift-image-registry.svc:5000/$$OCP_PROJECT/ibmmas-cli:100.0.0-pre.localbuild"
	@echo ""
	@echo "and the image has been pushed your OCP registry."
	@echo ""

# ==============================================================================
# Runtime and Utility Targets
# ==============================================================================

run: ## Run the CLI container image locally
	docker run -ti quay.io/ibmmas/cli:100.0.0-pre.local

clean: ## Remove built artifacts
	rm image/cli/install/ibm-mas_devops.tar.gz
	rm image/cli/bin/templates/ibm-mas-tekton.yaml

# ==============================================================================
# OpenShift Pod Management Targets
# ==============================================================================

create: ## Create MAS CLI pod in OpenShift from deployment manifest
	oc apply -f tmp/deployment.yaml
delete: ## Delete the running MAS CLI pod in OpenShift
	oc delete pod $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}")
exec: ## Execute bash shell in the running MAS CLI pod
	oc exec -ti $(shell oc get pods --selector app=mas-cli -o jsonpath="{.items[0].metadata.name}") -- bash
