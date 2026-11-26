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
import base64
import io
import shlex
import sys

import pytest

from mas.cli.common.commandBuilder import (
    CommandArg,
    clipboardAvailable,
    copyToClipboard,
    parserFlagMap,
    paramIsFalse,
    paramIsTrue,
    renderCommand,
)


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
    monkeypatch.delenv("MAS_CLIPBOARD", raising=False)
    assert copyToClipboard("hello") is False


def test_clipboard_available_false_when_no_backend(monkeypatch):
    """GIVEN pyperclip has no backend for this platform
    WHEN clipboardAvailable probes it
    THEN it returns False rather than raising (the container / headless case)
    """
    import pyperclip

    def no_backend():
        raise pyperclip.PyperclipException("no copy/paste mechanism for this system")

    monkeypatch.delenv("MAS_CLIPBOARD", raising=False)
    monkeypatch.setattr(pyperclip, "determine_clipboard", no_backend)
    assert clipboardAvailable() is False


def test_clipboard_available_osc52_mode_follows_tty(monkeypatch):
    """GIVEN MAS_CLIPBOARD=osc52
    WHEN clipboardAvailable is checked
    THEN availability follows whether stdout is a terminal, without touching
        pyperclip
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "osc52")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert clipboardAvailable() is True
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert clipboardAvailable() is False


def test_clipboard_available_off_mode(monkeypatch):
    """GIVEN MAS_CLIPBOARD=off
    WHEN clipboardAvailable is checked
    THEN it reports unavailable regardless of any backend
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "off")
    assert clipboardAvailable() is False


class FakeTTY(io.StringIO):
    """StringIO stand-in for a terminal stdout."""

    def isatty(self):
        return True


def test_copy_to_clipboard_osc52_writes_escape_sequence(monkeypatch):
    """GIVEN MAS_CLIPBOARD=osc52 with a terminal stdout
    WHEN copyToClipboard is called
    THEN the OSC 52 sequence is written, carrying the base64-encoded text
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "osc52")
    fake = FakeTTY()
    monkeypatch.setattr(sys, "stdout", fake)

    assert copyToClipboard("mas update --no-confirm") is True
    written = fake.getvalue()
    assert written.startswith("\x1b]52;c;")
    assert written.endswith("\x07")
    payload = written[len("\x1b]52;c;") : -1]
    assert base64.b64decode(payload).decode("utf-8") == "mas update --no-confirm"


def test_copy_to_clipboard_osc52_wrapped_inside_tmux(monkeypatch):
    """GIVEN MAS_CLIPBOARD=osc52 inside tmux
    WHEN copyToClipboard is called
    THEN the sequence is wrapped in the DCS passthrough tmux requires, with
        the inner sequence recoverable by un-doubling the ESC bytes
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "osc52")
    monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
    fake = FakeTTY()
    monkeypatch.setattr(sys, "stdout", fake)

    assert copyToClipboard("hello") is True
    written = fake.getvalue()
    assert written.startswith("\x1bPtmux;")
    assert written.endswith("\x1b\\")
    inner = written[len("\x1bPtmux;") : -len("\x1b\\")].replace("\x1b\x1b", "\x1b")
    payload = inner[len("\x1b]52;c;") : -1]
    assert base64.b64decode(payload).decode("utf-8") == "hello"


def test_copy_to_clipboard_osc52_requires_a_tty(monkeypatch):
    """GIVEN MAS_CLIPBOARD=osc52 but stdout is not a terminal
    WHEN copyToClipboard is called
    THEN it returns False and writes nothing (no escape garbage in pipes)
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "osc52")
    fake = io.StringIO()
    fake.isatty = lambda: False
    monkeypatch.setattr(sys, "stdout", fake)
    assert copyToClipboard("hello") is False
    assert fake.getvalue() == ""


def test_copy_to_clipboard_off_mode(monkeypatch):
    """GIVEN MAS_CLIPBOARD=off
    WHEN copyToClipboard is called
    THEN it returns False without attempting any copy
    """
    monkeypatch.setenv("MAS_CLIPBOARD", "off")
    assert copyToClipboard("hello") is False


def test_writeCommandScript_writes_header_and_command(tmp_path):
    """GIVEN a rendered command
    WHEN writeCommandScript writes it to a file
    THEN the file contains the shebang and provenance comment followed by
        the command — the single on-disk format shared by the interactive
        wizard's save prompt and the TUI's Save Script button
    """
    from mas.cli.common.commandBuilder import writeCommandScript

    command = "mas update \\n  --mas-catalog-version v9-261102-amd64 \\n  --no-confirm\n"
    target = tmp_path / "mas-update-v9-261102-amd64.sh"
    writeCommandScript(str(target), command)

    content = target.read_text()
    assert content.startswith("#!/bin/bash\n# Generated by the MAS CLI interactive wizard\n\n")
    assert content.endswith(command)


def test_offerCommandScript_saves_via_writeCommandScript(tmp_path, monkeypatch):
    """GIVEN a wizard app that answers yes to copying and yes to saving
    WHEN offerCommandScript runs
    THEN the command is copied to the clipboard and written to the chosen
        file with the shared script header
    """
    from mas.cli.common import commandBuilder

    copied = []
    monkeypatch.setattr(commandBuilder, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(commandBuilder, "copyToClipboard", lambda text: copied.append(text) or True)

    class PromptApp:
        def yesOrNo(self, _prompt):
            return True

        def promptForString(self, _prompt, default=None):
            return str(tmp_path / "chosen.sh")

        def printDescription(self, _lines):
            pass

    commandBuilder.offerCommandScript(PromptApp(), "mas update --no-confirm", "default.sh")
    assert copied == ["mas update --no-confirm"]
    content = (tmp_path / "chosen.sh").read_text()
    assert content.startswith("#!/bin/bash\n# Generated by the MAS CLI interactive wizard\n\n")
    assert "mas update --no-confirm" in content


def test_offerCommandScript_skips_clipboard_prompt_when_unavailable(tmp_path, monkeypatch):
    """GIVEN an environment with no usable clipboard (container / headless)
    WHEN offerCommandScript runs
    THEN the copy prompt is never asked and no failure message is printed,
        while the save-as-script offer is still made
    """
    from mas.cli.common import commandBuilder

    def unexpected_copy(text):
        raise AssertionError("copyToClipboard must not be called when unavailable")

    monkeypatch.setattr(commandBuilder, "clipboardAvailable", lambda: False)
    monkeypatch.setattr(commandBuilder, "copyToClipboard", unexpected_copy)

    prompts = []

    class PromptApp:
        def yesOrNo(self, prompt):
            prompts.append(prompt)
            return prompt.startswith("Save this command")

        def promptForString(self, _prompt, default=None):
            return str(tmp_path / "chosen.sh")

        def printDescription(self, lines):
            prompts.extend(lines)

    commandBuilder.offerCommandScript(PromptApp(), "mas update --no-confirm", "default.sh")
    assert not any("clipboard" in prompt.lower() for prompt in prompts)
    assert any("Save this command as a script file" in prompt for prompt in prompts)


def test_offerCommandScript_reports_failed_copy(monkeypatch):
    """GIVEN the availability probe passes but the copy itself fails
    WHEN offerCommandScript runs
    THEN the failure message is still shown -- availability is a hint, not a
        guarantee (e.g. xclip installed but no DISPLAY)
    """
    from mas.cli.common import commandBuilder

    monkeypatch.setattr(commandBuilder, "clipboardAvailable", lambda: True)
    monkeypatch.setattr(commandBuilder, "copyToClipboard", lambda text: False)

    printed = []

    class PromptApp:
        def yesOrNo(self, prompt):
            # Accept the clipboard offer only, so no script file is written
            return prompt.startswith("Copy this command")

        def promptForString(self, _prompt, default=None):
            return ""

        def printDescription(self, lines):
            printed.extend(lines)

    commandBuilder.offerCommandScript(PromptApp(), "mas update --no-confirm", "default.sh")
    assert any("Clipboard is not available in this environment" in line for line in printed)
