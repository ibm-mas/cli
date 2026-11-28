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
Generic, data-driven builder for the non-interactive commands that the
interactive wizards print at the end of a run.

A command is described as an ordered list of :class:`CommandArg` entries.
Each entry names the argparse ``dest`` it maps to -- the flag spelling is
looked up from the real argument parser, so the flag inventory is maintained
in one place only.  Entries carry only what argparse cannot express:

- ``value``/``param``: where the value comes from (a wizard instance
  attribute or a params key, which is usually the dest itself)
- ``env_var``: the value is a secret, so the command references ``$ENV_VAR``
  and the renderer emits a matching ``export ENV_VAR=x`` placeholder line
- ``const``: the flag is emitted alone (``store_true`` / ``store_const``)
- ``when``: the condition under which the flag is emitted
- ``required``: always emitted, even when the value is empty

The renderer owns quoting (``shlex.quote``), spacing, and line wrapping
uniformly, and generates the export block from the same entries that
reference the variables, so a referenced-but-not-exported secret is
impossible by construction.
"""

import base64
import logging
import os
import shlex
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

logger = logging.getLogger(__name__)

# Any object providing getParam(name) -> str plus the wizard instance
# attributes referenced by value/when callables (in practice: a BaseApp).
AppLike = Any


@dataclass(frozen=True)
class CommandArg:
    """
    One flag of a generated non-interactive command.

    Args:
        dest: the argparse destination this arg maps to; the flag spelling
            (``--dest-with-dashes``) is resolved from the real parser
        param: the params key the value is read from, when it differs from dest
        value: callable returning the value from a wizard instance attribute,
            as an alternative to reading a params key
        env_var: emit ``--flag $ENV_VAR`` (and an export placeholder) instead
            of the value, for sensitive parameters
        extra_exports: additional environment variables to export alongside
            env_var (e.g. ARTIFACTORY_TOKEN alongside ARTIFACTORY_USERNAME)
        const: emit the flag alone, with no value
        when: additional emission condition (the value being non-empty is
            still required unless const/required)
        required: always emit, even when the value is empty
    """

    dest: str
    param: Optional[str] = None
    value: Optional[Callable[[AppLike], object]] = None
    env_var: Optional[str] = None
    extra_exports: tuple = ()
    const: bool = False
    when: Optional[Callable[[AppLike], bool]] = None
    required: bool = False


def boolValue(value: object) -> bool:
    """
    Normalize a wizard parameter value to a boolean.

    Interactive runs store boolean answers as the strings 'true'/'false', but
    non-interactive runs copy argparse's native True/False (from store_true
    actions) into params, so both representations must be handled.
    """
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.lower() == "true"


def paramIsTrue(param: str) -> Callable[[AppLike], bool]:
    """Condition: the wizard parameter is set to true (string or bool)."""
    return lambda app: boolValue(app.getParam(param))


def paramIsFalse(param: str) -> Callable[[AppLike], bool]:
    """
    Condition: the wizard parameter is explicitly set to false (string or
    bool).  An unset parameter is not false: the "disable" flags must not be
    triggered just because a parameter was never answered.
    """
    return lambda app: app.getParam(param) != "" and not boolValue(app.getParam(param))


def parserFlagMap(parser: Any) -> dict:
    """
    Map every optional action of an argparse parser to its primary flag.

    Returns a dict of dest -> flag (the first long-form option), which is how
    the builder derives flag spellings instead of re-spelling them by hand.
    """
    flags = {}
    for action in parser._actions:
        options = [option for option in action.option_strings if option.startswith("--")]
        if options:
            flags.setdefault(action.dest, options[0])
    return flags


def renderCommand(prog: str, args: Sequence[CommandArg], app: AppLike, parser: Any) -> str:
    """
    Render the non-interactive script for a wizard run.

    Args:
        prog: the command prefix (e.g. "mas install")
        args: the ordered list of CommandArg entries describing the command
        app: the wizard app instance (provides getParam and instance attrs)
        parser: the command's real argparse parser, used to resolve flags

    Returns:
        A shell script: export placeholder lines for the secrets the command
        references, followed by the command with one flag per continuation
        line.
    """
    flags = parserFlagMap(parser)
    unknown = sorted({arg.dest for arg in args if arg.dest not in flags})
    if unknown:
        raise ValueError(f"No --flag found for dest(s) {', '.join(unknown)} in the {prog} argument parser")
    exports: list = []
    tokens: list = []

    for arg in args:
        if arg.when is not None and not arg.when(app):
            continue

        if arg.value is not None:
            value = arg.value(app)
        else:
            value = app.getParam(arg.param if arg.param is not None else arg.dest)

        if not arg.const and not arg.required and (value is None or str(value) == ""):
            continue

        flag = flags[arg.dest]

        if arg.env_var is not None:
            tokens.append(f"{flag} ${arg.env_var}")
            for var in (arg.env_var, *arg.extra_exports):
                if var not in exports:
                    exports.append(var)
        elif arg.const:
            tokens.append(flag)
        else:
            tokens.append(f"{flag} {shlex.quote(str(value))}")

    lines = [f"export {var}=x" for var in exports]
    lines.append(f"{prog} \\")
    for token in tokens[:-1]:
        lines.append(f"  {token} \\")
    if tokens:
        lines.append(f"  {tokens[-1]}")
    return "\n".join(lines) + "\n"


def clipboardAvailable() -> bool:
    """
    Whether a clipboard mechanism is usable in this environment.

    Selected by the ``MAS_CLIPBOARD`` environment variable:

    - ``off``: clipboard features are suppressed (never available).  For
        scripted runs that must not show clipboard prompts at all.
    - ``osc52``: the OSC 52 terminal escape sequence is used instead of
        pyperclip (see :func:`_copyOsc52`) -- available whenever stdout is a
        terminal.  This is how copying works inside containers and SSH
        sessions: the terminal emulator on the user's workstation owns the
        clipboard.
    - unset / any other value: available when pyperclip finds a backend for
        this platform.  On Linux that needs xclip/xsel and a display, so
        containers and headless machines report unavailable.

    Availability is a hint, not a guarantee: on the default mode the probe
    can succeed while the actual copy later fails (e.g. xclip is installed
    but ``DISPLAY`` is not set), which is why :func:`copyToClipboard` keeps
    its own failure branch.
    """
    mode = os.environ.get("MAS_CLIPBOARD", "").strip().lower()
    if mode == "off":
        return False
    if mode == "osc52":
        return sys.stdout.isatty()
    try:
        import pyperclip

        # Importing pyperclip never fails on a missing backend -- the first
        # copy would.  determine_clipboard() raises PyperclipException when
        # no backend exists for this platform, without touching the
        # clipboard, making it a safe availability probe.
        pyperclip.determine_clipboard()
        return True
    except Exception as e:
        logger.debug(f"Clipboard is not available: {e}")
        return False


def _copyOsc52(text: str) -> bool:
    """
    Copy text using the OSC 52 terminal escape sequence.

    The host terminal emulator (Windows Terminal, iTerm2, kitty, wezterm, ...)
    interprets the sequence and writes to its own system clipboard, so this
    works through ``docker exec -it`` and SSH sessions where the process has
    no access to any clipboard.  Inside tmux the sequence is wrapped in the
    DCS passthrough tmux requires (and tmux itself must have
    ``set-clipboard on``).

    Returns True when the sequence was written to a terminal.
    """
    try:
        if not sys.stdout.isatty():
            return False
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        sequence = f"\x1b]52;c;{payload}\x07"
        if os.environ.get("TMUX"):
            # tmux DCS passthrough: inner ESC bytes must be doubled
            sequence = "\x1bPtmux;" + sequence.replace("\x1b", "\x1b\x1b") + "\x1b\\"
        sys.stdout.write(sequence)
        sys.stdout.flush()
        return True
    except Exception as e:
        logger.debug(f"OSC 52 clipboard copy failed: {e}")
        return False


def copyToClipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.

    Returns True when the copy succeeded.  The mechanism is selected by the
    ``MAS_CLIPBOARD`` environment variable (see :func:`clipboardAvailable`):
    ``osc52`` writes the OSC 52 escape sequence for containers/SSH, ``off``
    disables copying, and the default uses pyperclip.  Clipboard support is
    optional: when pyperclip is not installed (or has no backend for this
    platform) this quietly returns False rather than disrupting the wizard.
    """
    mode = os.environ.get("MAS_CLIPBOARD", "").strip().lower()
    if mode == "off":
        return False
    if mode == "osc52":
        return _copyOsc52(text)
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.debug(f"Clipboard copy is not available: {e}")
        return False


def writeCommandScript(filename: str, command: str) -> None:
    """
    Write a generated non-interactive command to a shell script file.

    The single owner of the on-disk format (shebang + provenance comment +
    command), shared by the interactive wizard's save-as-script prompt and
    the Textual TUI's Save Script button.

    Args:
        filename: Path of the script to write.
        command: The rendered command (as returned by renderCommand).

    Raises:
        OSError: When the file cannot be written (the caller decides how to
            report it).
    """
    with open(filename, "w") as f:
        f.write("#!/bin/bash\n# Generated by the MAS CLI interactive wizard\n\n" + command)


def offerCommandScript(app: AppLike, command: str, defaultFilename: str) -> None:
    """
    Interactive helpers for a generated non-interactive command.

    Offers to copy the command to the clipboard and to save it as a shell
    script, so it is not lost in the console scrollback.  Uses the wizard's
    own prompt methods (yesOrNo / promptForString / printDescription).  The
    clipboard offer is only made when :func:`clipboardAvailable` reports a
    usable clipboard, so environments without one (containers, headless
    machines) are not asked a question they cannot act on.
    """
    if clipboardAvailable() and app.yesOrNo("Copy this command to your clipboard"):
        if copyToClipboard(command):
            app.printDescription(["Command copied to clipboard"])
        else:
            app.printDescription(["Clipboard is not available in this environment"])

    if app.yesOrNo("Save this command as a script file"):
        filename = app.promptForString("Script file name", default=defaultFilename)
        if filename == "":
            filename = defaultFilename
        try:
            writeCommandScript(filename, command)
            app.printDescription([f"Command saved to {filename}"])
        except OSError as e:
            app.printDescription([f"Failed to save command to {filename}: {e}"])
