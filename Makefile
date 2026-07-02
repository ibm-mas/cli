.DEFAULT_GOAL := all

# Set TEST=no to skip tests, e.g.: make python TEST=no
# Set CLEAN=no to skip clean, e.g.: make python CLEAN=no
TEST ?= yes
CLEAN ?= yes


# Clean everything
# -----------------------------------------------------------------------------
.PHONY: clean
clean: clean-python clean-tekton


# Build everything
# -----------------------------------------------------------------------------
.PHONY: all
all: python tekton


# Python Package
# -----------------------------------------------------------------------------
.PHONY: clean-python
clean-python:
ifeq ($(CLEAN),yes)
	rm -rf dist
endif

.PHONY: python
python: clean-python pytest dist/mas_cli-100.0.0.tar.gz

.PHONY: pytest
pytest:
ifeq ($(TEST),yes)
	.venv/bin/pytest python/tests
endif

dist/mas_cli-100.0.0.tar.gz:
	.venv/bin/python -m build


# Python Package Documentation
# -----------------------------------------------------------------------------
.venv-docs:
# We need to install the python-devops and cli packages because we generate documentation from their code using mkdocs directives
	uv venv .venv-docs
	uv pip install --python .venv-docs/bin/python setuptools
	uv pip install --python .venv-docs/bin/python -e ../python-devops -e .
# Install mkdocs and the various plugins that we use, including our custom plugins
	uv pip install --python .venv-docs/bin/python -q mkdocs properdocs mkdocs-carbon mkdocs-glightbox mkdocs-redirects
	uv pip install --python .venv-docs/bin/python -e ./mkdocs_plugins

.PHONY: mkdocs-serve
mkdocs-serve: .venv-docs
	.venv-docs/bin/mkdocs serve --livereload --dev-addr localhost:9010


# Tekton Definitions
# -----------------------------------------------------------------------------
.PHONY: tekton
tekton: clean-tekton tekton/target pytest-tekton

.PHONY: clean-tekton
clean-tekton:
ifeq ($(CLEAN),yes)
	rm -rf tekton/target
	rm -f python/src/mas/cli/templates/ibm-mas-tekton.yaml
endif

tekton/target:
	DEV_MODE=true build/bin/build-tekton.sh

.PHONY: pytest-tekton
pytest-tekton:
ifeq ($(TEST),yes)
	.venv/bin/pytest tekton/test_schema.py -v
endif


# Development aid
# -----------------------------------------------------------------------------
.PHONY: run
run:
	podman run --rm -it -e IBM_ENTITLEMENT_KEY --pull Always quay.io/ibmmas/cli:master bash
