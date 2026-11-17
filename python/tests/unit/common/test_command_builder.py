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
Unit tests for the generic command builder (mas.cli.common.commandBuilder).

These tests exercise the renderer in isolation with a minimal parser and a
fake wizard app: quoting, secret env-masking, export placeholders, const
flags, and error handling for unknown dests.
"""

import argparse
import shlex

import pytest

from mas.cli.common.commandBuilder import CommandArg, copyToClipboard, parserFlagMap, paramIsFalse, paramIsTrue, renderCommand


class FakeApp:
    """The minimal app surface the renderer needs: getParam plus attrs."""

    def __init__(self, params=None, **attrs):
        self.params = params or {}
        for key, value in attrs.items():
            setattr(self, key, value)

    def getParam(self, param):
        return self.params.get(param) if self.params.get(param) is not None else ""


def makeParser():
    parser = argparse.ArgumentParser(prog="mas test-cmd")
    parser.add_argument("--entitlement-key", dest="ibm_entitlement_key")
    parser.add_argument("--name", dest="name")
    parser.add_argument("--token", dest="token")
    parser.add_argument("--extra-token", dest="extra_token")
    parser.add_argument("--force", dest="force", action="store_true")
    parser.add_argument("--mode", dest="mode", const="special", action="store_const")
    return parser


ARGS = [
    CommandArg(dest="ibm_entitlement_key", env_var="IBM_ENTITLEMENT_KEY", required=True),
    CommandArg(dest="name"),
    CommandArg(dest="token", env_var="TOKEN", extra_exports=("EXTRA_TOKEN",)),
    CommandArg(dest="extra_token", env_var="EXTRA_TOKEN", when=lambda app: app.getParam("token") != ""),
    CommandArg(dest="force", const=True, when=lambda app: getattr(app, "force", False)),
    CommandArg(dest="mode", const=True, when=lambda app: app.getParam("mode") == "special"),
]


def render(app):
    return renderCommand("mas test-cmd", ARGS, app, makeParser())


def split_script(script):
    """Return (exports, argv) for a rendered script, substituting $VARS."""
    exports = []
    command_lines = []
    for line in script.splitlines():
        if line.startswith("export "):
            exports.append(line[len("export ") :].split("=")[0])
        else:
            command_lines.append(line)
    command = "\n".join(command_lines).replace(" \\\n", " ")
    argv = [f"secret-{token[1:].lower()}" if token.startswith("$") else token for token in shlex.split(command)]
    return exports, argv


def test_values_are_shell_quoted():
    """GIVEN a value containing spaces and quotes
    WHEN the command is rendered and shlex-split
    THEN the value round-trips intact
    """
    script = render(FakeApp({"name": 'My "Workspace" name'}))
    _, argv = split_script(script)
    assert argv[argv.index("--name") + 1] == 'My "Workspace" name'


def test_secret_is_env_masked_with_export():
    """GIVEN a sensitive parameter
    WHEN the command is rendered
    THEN the value never appears, the flag references $VAR, and an export
        placeholder line exists for it
    """
    script = render(FakeApp({"token": "super-secret", "name": "n"}))  # pragma: allowlist secret
    assert "super-secret" not in script  # pragma: allowlist secret
    exports, argv = split_script(script)
    assert "--token" in argv
    assert argv[argv.index("--token") + 1] == "secret-token"
    assert "TOKEN" in exports


def test_extra_exports_follow_their_trigger_arg():
    """GIVEN an entry with extra_exports
    WHEN the triggering entry is emitted
    THEN the extra variables are exported too
    """
    script = render(FakeApp({"token": "t"}))
    exports, _ = split_script(script)
    assert "TOKEN" in exports and "EXTRA_TOKEN" in exports

    # ... and when it is not emitted, neither export appears
    script = render(FakeApp({}))
    exports, _ = split_script(script)
    assert "TOKEN" not in exports and "EXTRA_TOKEN" not in exports


def test_required_secret_always_exported():
    """GIVEN a required secret entry
    WHEN the parameter is not set
    THEN the flag and its export placeholder are still emitted
    """
    script = render(FakeApp({}))
    exports, argv = split_script(script)
    assert argv[argv.index("--entitlement-key") + 1] == "secret-ibm_entitlement_key"
    assert "IBM_ENTITLEMENT_KEY" in exports


def test_empty_values_are_skipped():
    """GIVEN an unset value parameter
    WHEN the command is rendered
    THEN no flag is emitted for it
    """
    script = render(FakeApp({}))
    _, argv = split_script(script)
    assert "--name" not in argv


def test_const_flags():
    """GIVEN const entries with satisfied conditions
    WHEN the command is rendered
    THEN the flags are emitted without values
    """
    script = render(FakeApp({"mode": "special"}, force=True))
    _, argv = split_script(script)
    assert "--force" in argv
    # --mode is store_const: emitted without a value, as the final argv element
    assert argv[-1] == "--mode"


def test_unresolvable_dest_raises():
    """GIVEN an entry whose dest has no flag in the parser
    WHEN the command is rendered
    THEN a ValueError identifies the bad dest
    """
    with pytest.raises(ValueError, match="no-such-dest"):
        renderCommand("mas test-cmd", [CommandArg(dest="no-such-dest")], FakeApp({}), makeParser())


def test_value_from_instance_attribute():
    """GIVEN an entry reading a wizard instance attribute
    WHEN the attribute is set
    THEN the attribute value is rendered
    """
    args = [CommandArg(dest="name", value=lambda app: app.customName)]
    script = renderCommand("mas test-cmd", args, FakeApp({}, customName="from-attr"), makeParser())
    _, argv = split_script(script)
    assert argv[argv.index("--name") + 1] == "from-attr"


def test_parser_flag_map_prefers_long_option():
    """GIVEN a parser action with short and long options
    WHEN the flag map is built
    THEN the long option is used
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", dest="name")
    assert parserFlagMap(parser)["name"] == "--name"


def test_boolean_conditions_accept_string_and_native_bool():
    """GIVEN wizard params holding either 'true'/'false' strings (interactive)
        or native booleans (non-interactive, from argparse store_true)
    WHEN boolean conditions are evaluated
    THEN both representations are understood, and an unset parameter is
        neither true nor false
    """
    app = FakeApp({"as_string": "true", "as_native": True, "off_string": "false", "off_native": False})
    assert paramIsTrue("as_string")(app) is True
    assert paramIsTrue("as_native")(app) is True
    assert paramIsTrue("off_string")(app) is False
    assert paramIsTrue("unset")(app) is False
    assert paramIsFalse("off_string")(app) is True
    assert paramIsFalse("off_native")(app) is True
    # An unset parameter must not trigger the "disable" flags
    assert paramIsFalse("unset")(app) is False
    assert paramIsFalse("as_string")(app) is False


def test_copy_toClipboard_without_backend_returns_false(monkeypatch):
    """GIVEN pyperclip is not importable
    WHEN copyToClipboard is called
    THEN it returns False rather than raising
    """
    import builtins

    real_import = builtins.__import__

    def no_pyperclip(name, *args, **kwargs):
        if name == "pyperclip":
            raise ImportError("No module named 'pyperclip'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pyperclip)
    assert copyToClipboard("hello") is False
