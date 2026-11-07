# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for secret collection and sanitization in must-gather."""

import json
import os
from unittest.mock import Mock

import yaml

from mas.cli.must_gather.common.sanitize import LAST_APPLIED_ANNOTATION, stripLastAppliedConfiguration
from mas.cli.must_gather.common.secrets import _writeYaml, collectSecrets

PASSWORD_B64 = "c3VwZXJzZWNyZXQ="
PASSWORD_PLAIN = "supersecret"
LAST_APPLIED = json.dumps({"data": {"password": PASSWORD_B64}, "stringData": {"password": PASSWORD_PLAIN}})


def _secret(name="creds", annotations=None):
    if annotations is None:
        annotations = {LAST_APPLIED_ANNOTATION: LAST_APPLIED, "keep": "me"}
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": "mas-inst1-core", "annotations": annotations},
        "type": "Opaque",
        "data": {"password": PASSWORD_B64},
    }


class TestStripLastAppliedConfiguration:
    """Test removal of the last-applied-configuration annotation."""

    def test_removes_annotation_and_keeps_other_annotations(self):
        """Test annotation removal keeps other annotations.

        GIVEN a secret with last-applied-configuration and another annotation
        WHEN stripLastAppliedConfiguration is called
        THEN only last-applied-configuration is removed.
        """
        cleaned = stripLastAppliedConfiguration(_secret())

        assert LAST_APPLIED_ANNOTATION not in cleaned["metadata"]["annotations"]
        assert cleaned["metadata"]["annotations"]["keep"] == "me"

    def test_does_not_modify_input(self):
        """Test the input dict is left untouched.

        GIVEN a secret with last-applied-configuration
        WHEN stripLastAppliedConfiguration is called
        THEN the original dict still has the annotation.
        """
        original = _secret()

        stripLastAppliedConfiguration(original)

        assert LAST_APPLIED_ANNOTATION in original["metadata"]["annotations"]

    def test_removes_empty_annotations_block(self):
        """Test empty annotations block is dropped.

        GIVEN a secret whose only annotation is last-applied-configuration
        WHEN stripLastAppliedConfiguration is called
        THEN the annotations key is removed from metadata.
        """
        cleaned = stripLastAppliedConfiguration(_secret(annotations={LAST_APPLIED_ANNOTATION: LAST_APPLIED}))

        assert "annotations" not in cleaned["metadata"]

    def test_handles_secret_without_annotations_or_metadata(self):
        """Test secrets with missing metadata or annotations.

        GIVEN secrets with no annotations and no metadata
        WHEN stripLastAppliedConfiguration is called
        THEN they are returned unchanged without error.
        """
        noAnnotations = {"metadata": {"name": "x"}, "data": {}}
        noMetadata = {"kind": "Secret"}

        assert stripLastAppliedConfiguration(noAnnotations) == noAnnotations
        assert stripLastAppliedConfiguration(noMetadata) == noMetadata


class TestSecretWriteYaml:
    """Test secret YAML output contains no credentials."""

    def test_removes_data_and_last_applied_annotation(self, tmp_path):
        """Test written secret has no credential values.

        GIVEN a secret with data and a last-applied-configuration annotation
        WHEN _writeYaml is called
        THEN the file contains neither the base64 nor the plain text password.
        """
        outputFile = tmp_path / "creds.yaml"

        _writeYaml(_secret(), str(outputFile))

        content = outputFile.read_text()
        assert PASSWORD_B64 not in content
        assert PASSWORD_PLAIN not in content
        assert LAST_APPLIED_ANNOTATION not in content

    def test_keeps_non_sensitive_fields(self, tmp_path):
        """Test metadata is preserved.

        GIVEN a secret with data and annotations
        WHEN _writeYaml is called
        THEN name, type and other annotations are still written.
        """
        outputFile = tmp_path / "creds.yaml"

        _writeYaml(_secret(), str(outputFile))

        written = yaml.safe_load(outputFile.read_text())
        assert written["metadata"]["name"] == "creds"
        assert written["type"] == "Opaque"
        assert written["metadata"]["annotations"] == {"keep": "me"}
        assert "data" not in written

    def test_does_not_modify_input(self, tmp_path):
        """Test the caller's dict is not mutated.

        GIVEN a secret dict
        WHEN _writeYaml is called
        THEN the original dict still has data and the annotation.
        """
        original = _secret()

        _writeYaml(original, str(tmp_path / "creds.yaml"))

        assert "data" in original
        assert LAST_APPLIED_ANNOTATION in original["metadata"]["annotations"]


class TestCollectSecrets:
    """Test end to end secret collection."""

    def test_collect_secrets_writes_no_credentials(self, tmp_path):
        """Test collected secret files hold no credentials.

        GIVEN a namespace with secrets carrying data and last-applied-configuration
        WHEN collectSecrets is called
        THEN no file under the output directory contains the password in any form.
        """
        secrets = {"items": [_secret("creds"), _secret("other")]}
        coreV1 = Mock()
        coreV1.list_namespaced_secret.return_value = Mock(data=json.dumps(secrets))

        success, count = collectSecrets(coreV1, "mas-inst1-core", str(tmp_path))

        assert success is True
        assert count == 2
        secretsDir = tmp_path / "resources" / "mas-inst1-core" / "secrets"
        assert sorted(os.listdir(secretsDir)) == ["creds.yaml", "other.yaml"]
        for root, _, files in os.walk(tmp_path):
            for fileName in files:
                content = open(os.path.join(root, fileName)).read()
                assert PASSWORD_B64 not in content
                assert PASSWORD_PLAIN not in content
                assert LAST_APPLIED_ANNOTATION not in content

    def test_collect_secrets_failure_returns_false(self, tmp_path):
        """Test API errors are handled.

        GIVEN the Kubernetes API raises an exception
        WHEN collectSecrets is called
        THEN it returns (False, 0).
        """
        coreV1 = Mock()
        coreV1.list_namespaced_secret.side_effect = Exception("boom")

        assert collectSecrets(coreV1, "mas-inst1-core", str(tmp_path)) == (False, 0)
