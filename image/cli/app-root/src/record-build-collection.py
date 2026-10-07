#!/usr/bin/env python3

# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

# Initialises the parent collection document for a new catalog build across
# all SaaS staging instances registered in the instance registry file.
#
# Required environment variables:
#   DEVOPS_MONGO_URI       - MongoDB connection string
#   CATALOG_VERSION        - Catalog version string  (e.g. v9-260827-amd64)
#   CATALOG_IMAGE          - Full catalog image path
#   BUILD_ID               - Numeric build identifier
#   INSTANCE_REGISTRY_FILE - Absolute path to the instance registry YAML
#
# The document is upserted using _id = "saas-env-tests:build:<BUILD_ID>"
# so repeated runs for the same build are idempotent (they only overwrite
# fields that are expected to be re-initialised on a re-run).

import os
import sys
import yaml
from datetime import datetime, UTC
from pymongo import MongoClient


def load_registry(registry_file):
    """Load and return the list of instances from the registry YAML."""
    with open(registry_file, "r") as f:
        data = yaml.safe_load(f)
    instances = data.get("instances", [])
    if not instances:
        print(f"WARNING: No instances found in registry file: {registry_file}")
    return instances


def build_instance_entry(instance):
    """Build a single instance sub-document with PENDING status."""
    identity = instance.get("instance_identity", {})
    metadata = instance.get("instance_metadata", {})
    return {
        "instance_identity": {
            "instance_id": identity.get("instance_id", ""),
            "cluster_name": identity.get("cluster_name", ""),
            "cluster_provider": identity.get("cluster_provider", ""),
            "provider_region": identity.get("provider_region", ""),
            "provider_account_id": str(identity.get("provider_account_id", "")),
        },
        "instance_status": {
            "pipeline_run_status": "PENDING",
            "pipeline_run_status_details": "",
            "pipeline_run_overall_test_result_status": "",
            "pipeline_run_started_at": None,
            "pipeline_run_completed_at": None,
        },
        "instance_metadata": {
            "mas_workspace_id": metadata.get("mas_workspace_id", ""),
            "mas_channel": metadata.get("mas_channel", ""),
            "edition": metadata.get("edition", ""),
            "operational_mode": metadata.get("operational_mode", ""),
            "instance_domain": metadata.get("instance_domain", ""),
            "mas_capabilities": metadata.get("mas_capabilities", []),
        },
    }


if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ["DEVOPS_MONGO_URI"] == "":
        print("MongoDB integration disabled (DEVOPS_MONGO_URI not set)")
        sys.exit(0)

    catalogVersion = os.getenv("CATALOG_VERSION", "")
    catalogImage = os.getenv("CATALOG_IMAGE", "")
    buildId = os.getenv("BUILD_ID", "")
    registryFile = os.getenv("INSTANCE_REGISTRY_FILE", "")

    if "" in [catalogVersion, catalogImage, buildId, registryFile]:
        print("ERROR: One or more required env vars are not set:")
        print(f"  CATALOG_VERSION        = '{catalogVersion}'")
        print(f"  CATALOG_IMAGE          = '{catalogImage}'")
        print(f"  BUILD_ID               = '{buildId}'")
        print(f"  INSTANCE_REGISTRY_FILE = '{registryFile}'")
        sys.exit(1)

    print(f"Catalog Version ............ {catalogVersion}")
    print(f"Catalog Image .............. {catalogImage}")
    print(f"Build ID ................... {buildId}")
    print(f"Instance Registry File ..... {registryFile}")

    # Load instance registry
    instances = load_registry(registryFile)
    print(f"Instances found ............ {len(instances)}")
    for inst in instances:
        print(f"  - {inst.get('instance_identity', {}).get('instance_id', 'unknown')}")

    # Build instance sub-documents
    instanceDocs = [build_instance_entry(inst) for inst in instances]

    # Compose the parent document _id
    docId = f"saas-env-tests:build:{buildId}"
    now = datetime.now(UTC)

    print(f"\nWriting parent collection document: {docId}")

    # Connect to MongoDB
    client = MongoClient(os.getenv("DEVOPS_MONGO_URI"))
    db = client.masfvt

    # Upsert the parent document.
    # $setOnInsert: fields set only when the document is first created.
    # $set: fields always refreshed so a re-run resets instance statuses to PENDING.
    result = db.saas_env_test_runs.find_one_and_update(
        {"_id": docId},
        {
            "$setOnInsert": {
                "_id": docId,
                "created_at": now,
            },
            "$set": {
                "build_id": buildId,
                "catalog_version": catalogVersion,
                "catalog_image": catalogImage,
                "updated_at": now,
                "test_results_status": "PENDING",
                "instances": instanceDocs,
            },
        },
        upsert=True,
        return_document=False,
    )

    if result is None:
        print("Parent collection document created successfully (new document)")
    else:
        print("Parent collection document updated successfully (existing document reset)")
