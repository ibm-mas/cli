#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from utils import UpdateTestConfig, UpdateTestHelper
import sys
import os

# Add test directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PARAM = "aiservice_s3_migration_instance_ids"


def aiservice(name, s3Url):
    return {
        "metadata": {"name": name},
        "status": {"versions": {"reconciled": "9.2.0"}},
        "spec": {"settings": {"s3": {"url": s3Url}}},
    }


MINIO_URL = "http://minio-service.minio.svc.cluster.local:9000"
CEPH_URL = "https://s3.openshift-storage.svc:443"


def runUpdate(tmpdir, instances, argv, prompt_handlers=None):
    config = UpdateTestConfig(
        prompt_handlers=prompt_handlers or {},
        aiservice_instances=instances,
        argv=argv,
        timeout_seconds=30,
    )
    helper = UpdateTestHelper(tmpdir, config)
    helper.run_update_test()
    return helper.app.getParam(PARAM)


def test_non_interactive_with_flag_migrates_instances_on_minio(tmpdir):
    """--migrate-minio-to-ceph selects only the instances that use MinIO"""
    instances = [aiservice("onminio", MINIO_URL), aiservice("onceph", CEPH_URL)]
    selected = runUpdate(tmpdir, instances, ["--catalog", "v9-260129-amd64", "--no-confirm", "--migrate-minio-to-ceph"])
    assert selected == "onminio"


def test_non_interactive_without_flag_leaves_minio_alone(tmpdir):
    """Without the flag nothing is migrated, MinIO users are only warned"""
    instances = [aiservice("onminio", MINIO_URL)]
    selected = runUpdate(tmpdir, instances, ["--catalog", "v9-260129-amd64", "--no-confirm"])
    assert selected == ""


def test_non_interactive_nothing_on_minio(tmpdir):
    """The flag does nothing when no instance uses MinIO"""
    instances = [aiservice("onceph", CEPH_URL)]
    selected = runUpdate(tmpdir, instances, ["--catalog", "v9-260129-amd64", "--no-confirm", "--migrate-minio-to-ceph"])
    assert selected == ""


def test_interactive_answer_yes_migrates(tmpdir):
    """Answering y to the MinIO to Ceph prompt selects the instances"""
    handlers = {
        ".*Proceed with this cluster.*": lambda msg: "y",
        ".*Select catalog version.*": lambda msg: "1",
        ".*from MinIO to Ceph.*": lambda msg: "y",
        ".*Proceed with these settings.*": lambda msg: "y",
    }
    selected = runUpdate(tmpdir, [aiservice("onminio", MINIO_URL)], [], handlers)
    assert selected == "onminio"


def test_interactive_answer_no_skips(tmpdir):
    """Answering n to the MinIO to Ceph prompt migrates nothing"""
    handlers = {
        ".*Proceed with this cluster.*": lambda msg: "y",
        ".*Select catalog version.*": lambda msg: "1",
        ".*from MinIO to Ceph.*": lambda msg: "n",
        ".*Proceed with these settings.*": lambda msg: "y",
    }
    selected = runUpdate(tmpdir, [aiservice("onminio", MINIO_URL)], [], handlers)
    assert selected == ""
