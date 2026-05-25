#!/bin/bash

# Quick script to generate a single pipeline
# Usage: ./generate-pipeline.sh mas-fvt-launcher

if [ -z "$1" ]; then
    echo "Usage: $0 <pipeline-name>"
    echo ""
    echo "Examples:"
    echo "  $0 mas-fvt-launcher"
    echo "  $0 mas-install"
    echo "  $0 mas-fvt-core"
    echo ""
    echo "To generate all pipelines, run:"
    echo "  ansible-playbook generate-tekton-pipelines.yml"
    exit 1
fi

ansible-playbook generate-tekton-pipelines.yml -e pipeline_name=$1
