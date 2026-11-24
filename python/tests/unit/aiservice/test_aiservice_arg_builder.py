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

"""
Round-trip tests for the non-interactive aiservice-install command generator.

The interactive `mas aiservice-install` wizard ends by printing an equivalent
non-interactive command (aiServiceInstallArgBuilderMixin.buildCommand).
These tests build the command from a scenario of wizard state, feed it
through shlex and the *real* aiservice-install argument parser, and assert
that the parsed result matches the scenario - so any drift between the
builder and the parser fails here.
"""

import shlex

from mas.cli.aiservice.install.app import AiServiceInstallApp
from mas.cli.aiservice.install.argBuilder import AISERVICE_INSTALL_COMMAND_ARGS
from mas.cli.aiservice.install.argParser import aiServiceinstallArgParser
from mas.cli.common.commandBuilder import parserFlagMap
from mas.cli.displayMixins import SENSITIVE_PARAMS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_PARAMS = {
    "mas_catalog_version": "9.2.x",
    "aiservice_instance_id": "inst1",
    "aiservice_channel": "8.x",
    "storage_class_rwo": "rwo-sc",
    "storage_class_rwx": "rwx-sc",
    "dro_contact_email": "admin@example.com",
    "dro_contact_firstname": "Ada",
    "dro_contact_lastname": "Lovelace",
}

BASE_ATTRS = {
    "devMode": False,
    "localConfigDir": None,
    "pipelineStorageClass": "pipeline-sc",
    "pipelineStorageAccessMode": "ReadWriteMany",
    "slsLicenseFileLocal": None,
    "db2LicenseFileLocal": None,
    "aiserviceTenantSchedulingConfigFileLocal": None,
    "aiserviceTenantOperatorConfigFileLocal": None,
}


def make_app(params=None, **attrs):
    """Build a minimal AiServiceInstallApp whose state buildCommand can render."""
    app = AiServiceInstallApp.__new__(AiServiceInstallApp)
    app.params = dict(BASE_PARAMS)
    app.params.update(params or {})
    for key, value in BASE_ATTRS.items():
        setattr(app, key, value)
    for key, value in attrs.items():
        setattr(app, key, value)
    return app


def parse_generated_command(script):
    """
    Split a generated script into its export placeholders and command argv.

    Returns (args, exports, referenced_vars, argv): the namespace produced by
    the real aiservice-install argument parser, the set of exported variable
    names, the set of $VAR references found in the command, and the
    substituted argv.
    """
    exports = set()
    command_lines = []
    for line in script.splitlines():
        if line.startswith("export "):
            exports.add(line[len("export ") :].split("=")[0])
        else:
            command_lines.append(line)

    command = "\n".join(command_lines)
    command = command.replace(" \\\n", " ").replace("\\\n", " ")
    tokens = shlex.split(command)
    assert tokens[0] == "mas", f"expected script to start with 'mas', got {tokens[0]!r}"
    assert tokens[1] == "aiservice-install", f"expected 'aiservice-install' subcommand, got {tokens[1]!r}"

    referenced_vars = set()
    argv = []
    for token in tokens[2:]:
        if token.startswith("$"):
            var = token[1:]
            referenced_vars.add(var)
            argv.append(f"secret-{var.lower()}")
        else:
            argv.append(token)

    for var in sorted(referenced_vars):
        assert var in exports, f"${var} is referenced in the command but never exported"

    return aiServiceinstallArgParser.parse_args(argv), exports, referenced_vars, argv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_round_trip_basic():
    """GIVEN a basic aiservice-install wizard scenario
    WHEN the generated command is parsed by the real parser
    THEN every value round-trips and the entitlement key is env-masked
    """
    app = make_app()
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.mas_catalog_version == "9.2.x"
    assert args.aiservice_instance_id == "inst1"
    assert args.aiservice_channel == "8.x"
    assert args.storage_class_rwo == "rwo-sc"
    assert args.storage_class_rwx == "rwx-sc"
    assert args.storage_pipeline == "pipeline-sc"
    assert args.storage_accessmode == "ReadWriteMany"
    assert args.dro_contact_email == "admin@example.com"

    assert "IBM_ENTITLEMENT_KEY" in referenced
    assert args.ibm_entitlement_key == "secret-ibm_entitlement_key"
    assert "IBM_ENTITLEMENT_KEY" in exports


def test_round_trip_dedicated_sls():
    """GIVEN the SLS namespace follows the dedicated pattern for the instance
    WHEN the generated command is parsed
    THEN --dedicated-sls is set and --sls-namespace is not emitted
    """
    app = make_app(params={"sls_namespace": "mas-inst1-sls"})
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.dedicated_sls is True
    assert args.sls_namespace == "ibm-sls"  # parser default: --sls-namespace is not emitted


def test_round_trip_custom_sls_namespace():
    """GIVEN a custom SLS namespace
    WHEN the generated command is parsed
    THEN --sls-namespace round-trips
    """
    app = make_app(params={"sls_namespace": "custom-sls"})
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.dedicated_sls is False
    assert args.sls_namespace == "custom-sls"


def test_round_trip_cis():
    """GIVEN CIS is the DNS provider with enhanced security options
    WHEN the generated command is parsed
    THEN the CIS flags round-trip and the API key is env-masked
    """
    app = make_app(
        params={
            "dns_provider": "cis",
            "cis_apikey": "cis-apikey-secret",  # pragma: allowlist secret
            "cis_subdomain": "mas",
            "cis_crn": "crn:123",
            "cis_email": "dns@example.com",
            "cis_enhanced_security": "true",
            "cis_service_name": "cis-service",
            "update_dns_entries": "true",
        }
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.dns_provider == "cis"
    assert args.cis_apikey == "secret-cis_apikey"
    assert args.cis_enhanced_security == "true"
    assert args.cis_service_name == "cis-service"
    assert args.update_dns_entries == "true"
    assert "CIS_APIKEY" in referenced and "CIS_APIKEY" in exports
    assert "cis-apikey-secret" not in script  # pragma: allowlist secret


def test_round_trip_db2():
    """GIVEN in-cluster Db2 is installed with a license file
    WHEN the generated command is parsed
    THEN --db2-aiservice and the license file round-trip
    """
    app = make_app(
        params={"db2_action_aiservice": "install", "db2_channel": "v1.0"},
        db2LicenseFileLocal="/tmp/db2/license",
    )
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert args.db2_action_aiservice == "install"
    assert args.db2_channel == "v1.0"
    assert args.db2_license_file == "/tmp/db2/license"


def test_round_trip_external_database():
    """GIVEN an external database is used
    WHEN the generated command is parsed
    THEN the JDBC URL round-trips and the credentials stay env-masked
    """
    app = make_app(
        params={
            "aiservice_db_jdbc_url": "jdbc:db2://db.example.com:50000/ai",
            "aiservice_db_username": "dbuser",  # pragma: allowlist secret
            "aiservice_db_password": "db-secret",  # pragma: allowlist secret
        }
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.aiservice_db_jdbc_url == "jdbc:db2://db.example.com:50000/ai"
    assert args.aiservice_db_username == "secret-aiservice_db_username"
    assert args.aiservice_db_password == "secret-aiservice_db_password"
    for var in ("AISERVICE_DB_USERNAME", "AISERVICE_DB_PASSWORD"):
        assert var in referenced and var in exports
    for param in ("aiservice_db_username", "aiservice_db_password"):
        if app.params.get(param):
            assert app.params[param] not in script


def test_round_trip_ceph_vs_s3():
    """GIVEN install_ceph=true is set
    WHEN the generated command is parsed
    THEN --install-ceph is emitted and the external S3 flags are not emitted
    """
    app = make_app(params={"install_ceph": "true"})
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.install_ceph == "true"
    assert args.aiservice_s3_accesskey is None
    assert args.aiservice_s3_secretkey is None
    assert "AISERVICE_S3_ACCESSKEY" not in referenced


def test_round_trip_external_s3():
    """GIVEN an external S3-compatible object store (not ceph)
    WHEN the generated command is parsed
    THEN the S3 flags round-trip and the keys stay env-masked
    """
    app = make_app(
        params={
            "aiservice_s3_accesskey": "s3-key",  # pragma: allowlist secret
            "aiservice_s3_secretkey": "s3-secret",  # pragma: allowlist secret
            "aiservice_s3_host": "s3.example.com",
            "aiservice_s3_port": "443",
            "aiservice_s3_ssl": "true",
        }
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.install_ceph is None  # not emitted: --install-ceph only when install_ceph=true
    assert args.aiservice_s3_accesskey == "secret-aiservice_s3_accesskey"
    assert args.aiservice_s3_host == "s3.example.com"
    assert args.aiservice_s3_port == "443"
    assert "AISERVICE_S3_ACCESSKEY" in referenced and "AISERVICE_S3_ACCESSKEY" in exports


def test_round_trip_watsonx():
    """GIVEN watsonx.ai is configured
    WHEN the generated command is parsed
    THEN the watsonx flags round-trip and the API key stays env-masked
    """
    app = make_app(
        params={
            "aiservice_watsonxai_apikey": "wxai-secret",  # pragma: allowlist secret
            "aiservice_watsonxai_url": "https://wxai.example.com",
            "aiservice_watsonxai_project_id": "proj-1",
        }
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.aiservice_watsonxai_apikey == "secret-aiservice_watsonxai_apikey"
    assert args.aiservice_watsonxai_url == "https://wxai.example.com"
    assert args.aiservice_watsonxai_project_id == "proj-1"
    assert "AISERVICE_WATSONXAI_APIKEY" in referenced and "AISERVICE_WATSONXAI_APIKEY" in exports
    assert "wxai-secret" not in script  # pragma: allowlist secret


def test_round_trip_shell_escaping():
    """GIVEN values containing spaces and quotes
    WHEN the generated command is parsed
    THEN the values round-trip intact (shlex-safe quoting)
    """
    app = make_app(params={"aiservice_domain": 'My "Domain" name'})
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.aiservice_domain == 'My "Domain" name'


def test_no_plaintext_sensitive_params():
    """GIVEN a scenario with sensitive params set
    WHEN the command is generated
    THEN no SENSITIVE_PARAMS value appears verbatim in the script
    """
    app = make_app(
        params={
            "ibmcloud_apikey": "ibmcloud-secret",  # pragma: allowlist secret
            "aiservice_watsonxai_apikey": "wxai-secret",  # pragma: allowlist secret
            "artifactory_username": "art-user",  # pragma: allowlist secret
        }
    )
    script = app.buildCommand()
    for param, value in app.params.items():
        if param in SENSITIVE_PARAMS and value:
            assert value not in script, f"sensitive param {param} leaked into the generated command"


def test_spec_flags_resolve_in_parser():
    """GIVEN the declarative aiservice-install command spec
    WHEN every entry is resolved against the real argument parser
    THEN each dest maps to a flag (no typos, no flags the parser rejects)
    """
    flags = parserFlagMap(aiServiceinstallArgParser)
    for arg in AISERVICE_INSTALL_COMMAND_ARGS:
        assert arg.dest in flags, f"dest '{arg.dest}' has no flag in aiServiceinstallArgParser"
