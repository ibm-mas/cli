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
Round-trip tests for the non-interactive update command generator.

The interactive `mas update` wizard prints an equivalent non-interactive
command before the review settings screen (updateArgBuilderMixin.buildCommand).
These tests build the command from a scenario of wizard state, feed it
through shlex and the *real* update argument parser, and assert that the
parsed result matches the scenario - so any drift between the builder and
the parser fails here.
"""

import shlex

from mas.cli.common.commandBuilder import parserFlagMap
from mas.cli.displayMixins import SENSITIVE_PARAMS
from mas.cli.update.app import UpdateApp
from mas.cli.update.argBuilder import UPDATE_COMMAND_ARGS
from mas.cli.update.argParser import updateArgParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_PARAMS = {
    "mas_catalog_version": "v9-261105-amd64",
}

BASE_ATTRS = {
    "devMode": False,
    "db2LicenseFileLocal": None,
}


def make_app(params=None, **attrs):
    """Build a minimal UpdateApp whose state buildCommand can render."""
    app = UpdateApp.__new__(UpdateApp)
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
    the real update argument parser, the set of exported variable names, the
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
    assert tokens[1] == "update", f"expected 'update' subcommand, got {tokens[1]!r}"

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

    return updateArgParser.parse_args(argv), exports, referenced_vars, argv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_round_trip_basic():
    """GIVEN a basic update wizard scenario
    WHEN the generated command is parsed by the real parser
    THEN the catalog version round-trips
    """
    app = make_app()
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.mas_catalog_version == "v9-261105-amd64"
    assert args.no_confirm is True


def test_round_trip_dependency_updates():
    """GIVEN dependency namespaces and confirmed major version upgrades
    WHEN the generated command is parsed
    THEN the namespaces round-trip and the upgrade confirmations are set
    """
    app = make_app(
        params={
            "db2_namespace": "db2ns",
            "db2_v12_upgrade": "true",
            "mongodb_namespace": "mngns",
            "mongodb_v8_upgrade": "true",
            "kafka_namespace": "kafkans",
            "kafka_provider": "strimzi",
        },
        db2LicenseFileLocal="/tmp/db2/license",
    )
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.db2_namespace == "db2ns"
    assert args.db2_v12_upgrade == "true"
    assert args.db2_license_file == "/tmp/db2/license"
    assert args.mongodb_namespace == "mngns"
    assert args.mongodb_v8_upgrade == "true"
    # Confirmations the wizard did not give must not be emitted
    assert args.mongodb_v5_upgrade is None
    assert args.mongodb_v6_upgrade is None
    assert args.mongodb_v7_upgrade is None
    assert args.kafka_namespace == "kafkans"
    assert args.kafka_provider == "strimzi"


def test_round_trip_unconfirmed_upgrades_not_emitted():
    """GIVEN the wizard detected no major version upgrade is needed
    WHEN the generated command is parsed
    THEN the confirmation flags are not emitted
    """
    app = make_app(params={"db2_v12_upgrade": "false", "mongodb_v8_upgrade": "false"})
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert args.db2_v12_upgrade is None
    assert args.mongodb_v8_upgrade is None
    assert "--db2-v12-upgrade" not in argv


def test_round_trip_dev_mode():
    """GIVEN dev mode with artifactory credentials
    WHEN the generated command is parsed
    THEN --dev-mode is set and the credentials stay env-masked
    """
    app = make_app(
        params={
            "artifactory_username": "art-user",  # pragma: allowlist secret
            "artifactory_token": "art-secret",  # pragma: allowlist secret
        },
        devMode=True,
    )
    script = app.buildCommand()
    args, exports, referenced, _ = parse_generated_command(script)

    assert args.dev_mode is True
    assert args.artifactory_username == "secret-artifactory_username"
    assert args.artifactory_token == "secret-artifactory_token"
    for var in ("ARTIFACTORY_USERNAME", "ARTIFACTORY_TOKEN"):
        assert var in referenced and var in exports
    for param in ("artifactory_username", "artifactory_token"):
        assert app.params[param] not in script


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
    assert "SLACK_TOKEN" in referenced and "SLACK_TOKEN" in exports
    assert "xoxb-token" not in script


def test_round_trip_shell_escaping():
    """GIVEN a catalog version containing shell-special characters
    WHEN the generated command is parsed
    THEN the value round-trips intact (shlex-safe quoting)
    """
    app = make_app(params={"mas_catalog_version": "v9-'custom' tag", "image_pull_policy": "IfNotPresent"})
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.mas_catalog_version == "v9-'custom' tag"
    assert args.image_pull_policy == "IfNotPresent"


def test_no_plaintext_sensitive_params():
    """GIVEN a scenario with sensitive params set
    WHEN the command is generated
    THEN no SENSITIVE_PARAMS value appears verbatim in the script
    """
    app = make_app(
        params={
            "slack_token": "xoxb-token",  # pragma: allowlist secret
            "artifactory_token": "art-secret",  # pragma: allowlist secret
        }
    )
    script = app.buildCommand()
    for param, value in app.params.items():
        if param in SENSITIVE_PARAMS and value:
            assert value not in script, f"sensitive param {param} leaked into the generated command"


def test_spec_flags_resolve_in_parser():
    """GIVEN the declarative update command spec
    WHEN every entry is resolved against the real argument parser
    THEN each dest maps to a flag (no typos, no flags the parser rejects)
    """
    flags = parserFlagMap(updateArgParser)
    for arg in UPDATE_COMMAND_ARGS:
        assert arg.dest in flags, f"dest '{arg.dest}' has no flag in updateArgParser"
