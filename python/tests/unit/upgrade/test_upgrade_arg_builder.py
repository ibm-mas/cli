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
Round-trip tests for the non-interactive upgrade command generator.

The interactive `mas upgrade` wizard prints an equivalent non-interactive
command before the review settings screen (upgradeArgBuilderMixin.buildCommand).
These tests build the command from a scenario of wizard state, feed it
through shlex and the *real* upgrade argument parser, and assert that the
parsed result matches the scenario - so any drift between the builder and
the parser fails here.
"""

import shlex

from mas.cli.common.commandBuilder import parserFlagMap
from mas.cli.displayMixins import SENSITIVE_PARAMS
from mas.cli.upgrade.app import UpgradeApp
from mas.cli.upgrade.argBuilder import UPGRADE_COMMAND_ARGS
from mas.cli.upgrade.argParser import upgradeArgParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_ATTRS = {
    "masInstanceId": "inst1",
    "nextChannel": "9.1.x",
    "pipelineStorageClass": "pipeline-sc",
    "pipelineStorageAccessMode": "ReadWriteMany",
    "skipPreCheck": False,
    "devMode": False,
    "licenseAccepted": False,
}


def make_app(params=None, **attrs):
    """Build a minimal UpgradeApp whose state buildCommand can render."""
    app = UpgradeApp.__new__(UpgradeApp)
    app.params = params or {}
    for key, value in BASE_ATTRS.items():
        setattr(app, key, value)
    for key, value in attrs.items():
        setattr(app, key, value)
    return app


def parse_generated_command(script):
    """
    Split a generated script into its export placeholders and command argv.

    Returns (args, exports, referenced_vars, argv): the namespace produced by
    the real upgrade argument parser, the set of exported variable names, the
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
    assert tokens[1] == "upgrade", f"expected 'upgrade' subcommand, got {tokens[1]!r}"

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

    return upgradeArgParser.parse_args(argv), exports, referenced_vars, argv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_round_trip_basic():
    """GIVEN a basic upgrade wizard scenario
    WHEN the generated command is parsed by the real parser
    THEN the instance id, channel and storage settings round-trip
    """
    app = make_app()
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.mas_instance_id == "inst1"
    assert args.next_channel == "9.1.x"
    assert args.storage_pipeline == "pipeline-sc"
    assert args.storage_accessmode == "ReadWriteMany"
    assert args.accept_license is True
    assert args.no_confirm is True


def test_round_trip_unknown_channel_not_emitted():
    """GIVEN the next channel could not be detected from the cluster
    WHEN the generated command is parsed
    THEN --next-channel is not emitted (the placeholder value would be
        rejected as an invalid upgrade path on re-run)
    """
    app = make_app(nextChannel="Unknown")
    script = app.buildCommand()
    args, _, _, argv = parse_generated_command(script)

    assert args.next_channel == ""  # parser default: --next-channel is not emitted
    assert "--next-channel" not in argv


def test_round_trip_storage_classes():
    """GIVEN storage classes were detected for the Manage Foundation Db2 instances
    WHEN the generated command is parsed
    THEN the storage classes round-trip
    """
    app = make_app(params={"storage_class_rwo": "rwo-sc", "storage_class_rwx": "rwx-sc"})
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.storage_class_rwo == "rwo-sc"
    assert args.storage_class_rwx == "rwx-sc"


def test_round_trip_flags():
    """GIVEN skip-pre-check and dev mode are enabled
    WHEN the generated command is parsed
    THEN both store_true flags round-trip
    """
    app = make_app(skipPreCheck=True, devMode=True)
    script = app.buildCommand()
    args, _, _, _ = parse_generated_command(script)

    assert args.skip_pre_check is True
    assert args.dev_mode is True


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


def test_no_plaintext_sensitive_params():
    """GIVEN a scenario with sensitive params set
    WHEN the command is generated
    THEN no SENSITIVE_PARAMS value appears verbatim in the script
    """
    app = make_app(params={"slack_token": "xoxb-token"})  # pragma: allowlist secret
    script = app.buildCommand()
    for param, value in app.params.items():
        if param in SENSITIVE_PARAMS and value:
            assert value not in script, f"sensitive param {param} leaked into the generated command"


def test_spec_flags_resolve_in_parser():
    """GIVEN the declarative upgrade command spec
    WHEN every entry is resolved against the real argument parser
    THEN each dest maps to a flag (no typos, no flags the parser rejects)
    """
    flags = parserFlagMap(upgradeArgParser)
    for arg in UPGRADE_COMMAND_ARGS:
        assert arg.dest in flags, f"dest '{arg.dest}' has no flag in upgradeArgParser"
