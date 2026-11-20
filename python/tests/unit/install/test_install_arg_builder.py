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
Round-trip tests for the non-interactive install command generator.

The interactive install wizard ends by printing an equivalent non-interactive
command (installArgBuilderMixin.buildCommand).  These tests build the command
from a scenario of wizard state, feed it through shlex and the *real*
install argument parser, and assert that the parsed result matches the
scenario - so any drift between the builder and the parser fails here.

  GIVEN a basic wizard scenario
  WHEN buildCommand output is parsed by the real install argument parser
  THEN every emitted flag round-trips to the scenario value and no secrets
      appear in plaintext

  GIVEN ECK with logstash and a remote Elasticsearch is configured
  WHEN the command is generated and parsed
  THEN the flags are correctly separated and the ES password is env-masked

  GIVEN an AWS MSK Kafka scenario with distinct per-AZ CIDRs
  WHEN the command is generated and parsed
  THEN each --msk-cidr-azN flag carries its own CIDR

  GIVEN Grafana skip / pre-check skip / Slack / Manage options are set
  WHEN the command is generated and parsed
  THEN the corresponding store_true flags and values round-trip, and every
      referenced $VAR has an export placeholder line
"""

import shlex
from unittest.mock import MagicMock

from mas.cli.displayMixins import SENSITIVE_PARAMS
from mas.cli.install.app import InstallApp
from mas.cli.install.argParser import installArgParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_PARAMS = {
    "mas_catalog_version": "9.2.x",
    "mas_channel": "9.2.x",
    "mas_instance_id": "inst1",
    "mas_workspace_id": "ws1",
    "mas_workspace_name": "My Workspace",
    "storage_class_rwo": "rwo-sc",
    "storage_class_rwx": "rwx-sc",
    "dro_contact_email": "admin@example.com",
    "dro_contact_firstname": "Ada",
    "dro_contact_lastname": "Lovelace",
}

BASE_ATTRS = {
    "operationalMode": 1,
    "mas_admin_mode": "",
    "devMode": False,
    "skipGrafanaInstall": False,
    "useCliDigest": False,
    "cliDigest": None,
    "localConfigDir": None,
    "podTemplatesKeyword": None,
    "manualCertsDir": None,
    "pipelineStorageClass": "pipeline-sc",
    "pipelineStorageAccessMode": "ReadWriteMany",
    "slsLicenseFileLocal": None,
    "db2LicenseFileLocal": None,
    "facilitiesPropertiesFileLocal": None,
    "aiserviceTenantSchedulingConfigFileLocal": None,
    "aiserviceTenantOperatorConfigFileLocal": None,
    "installAssist": False,
    "installIoT": False,
    "installMonitor": False,
    "installManage": False,
    "installOptimizer": False,
    "installPredict": False,
    "installInspection": False,
    "installFacilities": False,
    "installAIService": False,
    "installMcpi": False,
    "installArcgis": False,
}


def make_app(params=None, **attrs):
    """Build a minimal InstallApp whose state buildCommand can render."""
    app = InstallApp.__new__(InstallApp)
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
    the real install argument parser, the set of exported variable names, the
    set of $VAR references found in the command, and the substituted argv.
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
    assert tokens[1] == "install", f"expected 'install' subcommand, got {tokens[1]!r}"

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

    return installArgParser.parse_args(argv), exports, referenced_vars, argv


def assert_no_plaintext_secrets(app, script):
    """No SENSITIVE_PARAMS value may appear verbatim in the generated script."""
    for param, value in app.params.items():
        if param in SENSITIVE_PARAMS and value:
            assert value not in script, f"sensitive param {param} leaked into the generated command"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_round_trip_basic():
    """GIVEN a basic wizard scenario
    WHEN the generated command is parsed by the real parser
    THEN every value round-trips and the entitlement key is env-masked
    """
    app = make_app()
    script = app.buildCommand()
    args, exports, referenced, argv = parse_generated_command(script)

    assert args.mas_catalog_version == "9.2.x"
    assert args.mas_channel == "9.2.x"
    assert args.mas_instance_id == "inst1"
    assert args.mas_workspace_id == "ws1"
    assert args.mas_workspace_name == "My Workspace"
    assert args.storage_class_rwo == "rwo-sc"
    assert args.storage_class_rwx == "rwx-sc"
    assert args.storage_pipeline == "pipeline-sc"
    assert args.storage_accessmode == "ReadWriteMany"
    assert args.dro_contact_email == "admin@example.com"
    assert args.dro_contact_firstname == "Ada"
    assert args.dro_contact_lastname == "Lovelace"

    assert "IBM_ENTITLEMENT_KEY" in referenced
    assert args.ibm_entitlement_key == "secret-ibm_entitlement_key"
    assert "None" not in argv
    assert_no_plaintext_secrets(app, script)


def test_round_trip_eck_with_logstash():
    """GIVEN ECK install with logstash and remote Elasticsearch credentials
    WHEN the generated command is parsed
    THEN the flags are correctly separated and the ES password is env-masked
    """
    app = make_app(
        params={
            "eck_action": "install",
            "eck_enable_logstash": "true",
            "eck_remote_es_hosts": "es.example.com:9200",
            "eck_remote_es_username": "esuser",
            "eck_remote_es_password": "es-supersecret",  # pragma: allowlist secret
        }
    )
    script = app.buildCommand()
    args, _, referenced, _ = parse_generated_command(script)

    assert args.eck_action == "install"
    assert args.eck_enable_logstash is True
    assert args.eck_remote_es_hosts == "es.example.com:9200"
    assert args.eck_remote_es_username == "esuser"
    assert args.eck_remote_es_password == "secret-es_password"
    assert "ES_PASSWORD" in referenced
    assert "es-supersecret" not in script  # pragma: allowlist secret


def test_round_trip_msk_cidrs():
    """GIVEN an AWS MSK scenario with distinct per-AZ CIDRs
    WHEN the generated command is parsed
    THEN each --msk-cidr-azN flag carries its own CIDR
    """
    app = make_app(
        params={
            "kafka_provider": "aws",
            "aws_msk_instance_type": "kafka.m5.large",
            "aws_msk_instance_number": "3",
            "aws_msk_volume_size": "100",
            "aws_msk_cidr_az1": "10.0.1.0/24",
            "aws_msk_cidr_az2": "10.0.2.0/24",
            "aws_msk_cidr_az3": "10.0.3.0/24",
            "aws_msk_egress_cidr": "0.0.0.0/0",
            "aws_msk_ingress_cidr": "10.0.0.0/16",
        }
    )
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert args.kafka_provider == "aws"
    assert args.aws_msk_instance_type == "kafka.m5.large"
    assert args.aws_msk_instance_number == "3"
    assert args.aws_msk_volume_size == "100"
    assert args.aws_msk_cidr_az1 == "10.0.1.0/24"
    assert args.aws_msk_cidr_az2 == "10.0.2.0/24"
    assert args.aws_msk_cidr_az3 == "10.0.3.0/24"
    # The broker node count and volume size must be carried as values, not
    # emitted as empty strings (the builder used to read params that don't exist)
    assert "--msk-instance-nodes" in argv
    assert argv[argv.index("--msk-instance-nodes") + 1] == "3"


def test_round_trip_skip_flags():
    """GIVEN grafana install and pre-check are skipped
    WHEN the generated command is parsed
    THEN both store_true flags round-trip
    """
    app = make_app(params={"skip_pre_check": "true"}, skipGrafanaInstall=True)
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.skip_grafana_install is True
    assert args.skip_pre_check is True


def test_round_trip_slack():
    """GIVEN Slack notifications are configured
    WHEN the generated command is parsed
    THEN the channel round-trips and the token is env-masked with an export
    """
    app = make_app(params={"slack_channel": "#mas", "slack_token": "xoxb-token"})
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.slack_channel == "#mas"
    assert args.slack_token == "secret-slack_token"
    assert "SLACK_TOKEN" in referenced
    assert "SLACK_TOKEN" in exports
    assert "xoxb-token" not in script


def test_round_trip_db2_without_license_file():
    """GIVEN in-cluster Db2 is installed but no license file was provided
    WHEN the generated command is parsed
    THEN no --db2-license-file "None" is emitted
    """
    app = make_app(params={"db2_action_system": "install"}, db2LicenseFileLocal=None)
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert "None" not in argv
    assert args.db2_license_file is None


def test_round_trip_manage_options():
    """GIVEN Manage is installed with an online upgrade type and JMS enabled
    WHEN the generated command is parsed
    THEN the manage flags round-trip
    """
    app = make_app(
        params={
            "mas_appws_upgrade_type": "onlineUpgrade",
            "mas_app_settings_default_jms": "true",
            "mas_appws_bindings_jdbc_manage": "system",
            "mas_appws_components": "all",
        },
        installManage=True,
    )
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.mas_appws_upgrade_type == "onlineUpgrade"
    assert args.mas_app_settings_default_jms == "true"
    assert args.mas_appws_bindings_jdbc_manage == "system"
    assert args.mas_appws_components == "all"


def test_round_trip_sensitive_params_masked():
    """GIVEN a scenario with many sensitive params set
    WHEN the command is generated
    THEN no plaintext secret appears and every $VAR has an export line
    """
    app = make_app(
        params={
            "dns_provider": "cis",
            "cis_apikey": "cis-apikey-secret",  # pragma: allowlist secret
            "cis_subdomain": "mas",
            "cis_crn": "crn:123",
            "cis_email": "dns@example.com",
            "kafka_provider": "strimzi",
            "kafka_username": "kafkauser",
            "kafka_password": "kafka-secret",  # pragma: allowlist secret
            "mas_superuser_username": "superuser",
            "mas_superuser_password": "super-secret",  # pragma: allowlist secret
            "mas_manage_encryptionsecret_crypto_key": "crypto-secret",  # pragma: allowlist secret
            "mas_appws_bindings_jdbc_manage": "system",
            "mas_appws_components": "all",
        },
        installManage=True,
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.cis_apikey == "secret-cis_apikey"
    assert args.kafka_password == "secret-kafka_password"
    assert args.mas_superuser_password == "secret-superuser_password"
    for var in ("CIS_APIKEY", "KAFKA_PASSWORD", "SUPERUSER_PASSWORD", "CRYPTO_KEY"):
        assert var in referenced and var in exports
    assert_no_plaintext_secrets(app, script)


def test_round_trip_shell_escaping():
    """GIVEN values containing spaces and quotes
    WHEN the generated command is parsed
    THEN the values round-trip intact (shlex-safe quoting)
    """
    app = make_app(
        params={
            "mas_workspace_name": 'My "Workspace" name',
            "mas_domain": "mas.example.com",
            "mas_cluster_issuer": "inst1'issuer",
        }
    )
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.mas_workspace_name == 'My "Workspace" name'
    assert args.mas_domain == "mas.example.com"
    assert args.mas_cluster_issuer == "inst1'issuer"


def test_round_trip_ingress_controller_name():
    """GIVEN a custom ingress controller is configured for path-based routing
    WHEN the generated command is parsed
    THEN --ingress-controller-name round-trips (the builder used to emit
        --ingress-controller, which the parser rejects)
    """
    app = make_app(params={"mas_ingress_controller_name": "custom-controller"})
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert args.mas_ingress_controller_name == "custom-controller"
    assert "--ingress-controller " not in " ".join(argv)


def test_round_trip_eventstreams():
    """GIVEN IBM Event Streams is used as the Kafka provider
    WHEN the generated command is parsed
    THEN the eventstreams flags round-trip (the builder used to gate this
        block on a parameter that is never set)
    """
    app = make_app(
        params={
            "kafka_provider": "ibm",
            "eventstreams_resourcegroup": "rg-1",
            "eventstreams_name": "eventstreams-inst1",
            "eventstreams_location": "us-south",
        }
    )
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.eventstreams_resourcegroup == "rg-1"
    assert args.eventstreams_name == "eventstreams-inst1"
    assert args.eventstreams_location == "us-south"


def test_spec_flags_resolve_in_parser():
    """GIVEN the declarative install command spec
    WHEN every entry is resolved against the real argument parser
    THEN each dest maps to a flag (no typos, no flags the parser rejects)
    """
    from mas.cli.common.commandBuilder import parserFlagMap
    from mas.cli.install.argBuilder import INSTALL_COMMAND_ARGS

    flags = parserFlagMap(installArgParser)
    for arg in INSTALL_COMMAND_ARGS:
        assert arg.dest in flags, f"dest '{arg.dest}' has no flag in installArgParser"


def _run_interactive_grafana_prompt(answer):
    """Run configGrafana as the interactive wizard does, answering the
    "Install Grafana" prompt with the given value."""
    app = make_app()
    app.architecture = "amd64"
    app.isInteractiveMode = True
    app.showAdvancedOptions = False
    app._dynClient = MagicMock()
    app.yesOrNo = MagicMock(return_value=answer)
    app.configGrafana()
    return app


def test_round_trip_interactive_grafana_declined():
    """GIVEN the user answers No to "Install Grafana" in the interactive wizard
    WHEN the generated command is parsed
    THEN it carries --skip-grafana-install, so a non-interactive run of it
        does not install Grafana either
    """
    app = _run_interactive_grafana_prompt(False)
    assert app.getParam("grafana_action") == "none"

    args, _, _, _ = parse_generated_command(app.buildCommand())

    assert args.skip_grafana_install is True


def test_round_trip_interactive_grafana_accepted():
    """GIVEN the user answers Yes to "Install Grafana" in the interactive wizard
    WHEN the generated command is parsed
    THEN it does not carry --skip-grafana-install
    """
    app = _run_interactive_grafana_prompt(True)
    assert app.getParam("grafana_action") == "install"

    args, _, _, _ = parse_generated_command(app.buildCommand())

    assert args.skip_grafana_install is False
