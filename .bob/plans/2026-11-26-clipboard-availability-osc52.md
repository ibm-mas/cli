# Clipboard availability pre-check + OSC 52 support for containers

## Context

The interactive wizards end with `offerCommandScript()`, which **unconditionally** asks
"Copy this command to your clipboard? [y/n]" and only discovers afterwards that
`pyperclip` has no backend — printing "Clipboard is not available in this environment"
after the user already answered. This happens in container images and headless Linux:
pyperclip on Linux needs `xclip`/`xsel` plus an X display, none of which exist there.
The TUI has the same problem: Copy buttons are always shown, and
[launch.py:292-296](python/src/mas/cli/tui/screens/launch.py#L292-L296) even shows
"Copied!" when the copy actually failed.

Goals (user-confirmed decisions):

1. Pre-check clipboard availability; only show the prompt / buttons when it's usable.
2. Opt-in env var `MAS_CLIPBOARD=osc52` to make copying work in containers via the
   OSC 52 terminal escape sequence (interpreted by the *host* terminal emulator —
   works through `docker exec -it`, `kubectl exec -it`, SSH; supported by Windows
   Terminal, iTerm2, kitty, wezterm; tmux needs `set-clipboard on`).
3. Also fix the TUI buttons (hide when unavailable, fix false "Copied!").

## New env var: `MAS_CLIPBOARD`

| Value | Behavior |
|---|---|
| unset / `auto` (default) | pyperclip only (unchanged) |
| `osc52` | force OSC 52 copying (container / SSH use) |
| `off` | suppress all clipboard features (scripted runs) |

## Changes

### 1. [commandBuilder.py](python/src/mas/cli/common/commandBuilder.py) (core)

- New `clipboardAvailable() -> bool`:
  - `MAS_CLIPBOARD=off` → `False`
  - `MAS_CLIPBOARD=osc52` → `sys.stdout.isatty()`
  - default → probe `pyperclip.determine_clipboard()` in try/except (importing
    pyperclip never fails; the probe raises `PyperclipException` when no backend
    exists for the platform — exactly the container case)
- New private `_copyOsc52(text) -> bool`:
  - requires `sys.stdout.isatty()`; writes `\x1b]52;c;<base64(text)>\x07`, flushes
  - when `TMUX` is set, wraps in the standard DCS passthrough
    (`\x1bPtmux;` + sequence with inner `\x1b` doubled + `\x1b\\`)
  - returns bool, catches everything
- `copyToClipboard(text)`: dispatch on `MAS_CLIPBOARD` (`off` → `False`,
  `osc52` → `_copyOsc52`) before the existing pyperclip path
- `offerCommandScript()`: gate the prompt —
  `if clipboardAvailable() and app.yesOrNo("Copy this command to your clipboard"):`
  Keep the existing "Clipboard is not available" branch as a fallback for the rare
  probe-passed-but-copy-failed case (e.g. xclip installed but no `DISPLAY`)
- New top-level imports: `os`, `sys`, `base64`
- Export `clipboardAvailable` from [common/\_\_init\_\_.py](python/src/mas/cli/common/__init__.py)
  alongside `copyToClipboard`

### 2. TUI screens

- [review.py](python/src/mas/cli/tui/screens/review.py): in `on_mount`, also hide
  `#btn-copy-command` when `not clipboardAvailable()` (extends the existing
  hide-when-no-builder logic)
- [launch.py](python/src/mas/cli/tui/screens/launch.py):
  - `_show_command_reference()` / `_on_checklist_done()` only reveal the
    Copy Command / Copy URL buttons when `clipboardAvailable()`
  - Copy URL handler: replace the direct `pyperclip.copy()` + silent `except: pass`
    with the shared `copyToClipboard()`; only flash "Copied!" on success, otherwise
    report via the action-bar status (drop the module-level pyperclip import)
  - Copy Command handler: only show "Copied!" when `copyToClipboard` returns `True`

### 3. CLI container image

[image/cli/Dockerfile](image/cli/Dockerfile) — add `MAS_CLIPBOARD=osc52` to the
existing `ENV` block (lines 16-21). A container never has a local X clipboard, so
OSC 52 is the correct default there; users can override per-run
(`docker run -e MAS_CLIPBOARD=off ...`) if their terminal doesn't support it.

## Tests

Per `python/AGENTS.md`: logic → `tests/unit/`, rendering/display → `tests/pilot/`.

**New unit tests** in [test_command_builder.py](python/tests/unit/common/test_command_builder.py):
- `clipboardAvailable()`: False when the pyperclip probe raises (monkeypatch);
  True under `MAS_CLIPBOARD=osc52` with a fake isatty stdout; False for `off`
- `copyToClipboard` OSC 52: monkeypatch `sys.stdout` (isatty True), assert the
  written sequence base64-decodes back to the text; `TMUX` set → passthrough-wrapped;
  non-tty → False
- `offerCommandScript`: clipboard unavailable → `yesOrNo` never called for the copy
  question, no failure message, save-as-script prompt still offered

**Existing tests that must be updated** (CI has no clipboard, so with the new gating
they would otherwise fail — required, not optional):
- [test_command_builder.py](python/tests/unit/common/test_command_builder.py):
  `test_offerCommandScript_saves_via_writeCommandScript` must monkeypatch
  `clipboardAvailable` → True (it already patches `copyToClipboard`)
- [test_review_screen.py](python/tests/pilot/tui/test_review_screen.py): existing
  `#btn-copy-command` display assertions need `clipboardAvailable` (in the review
  module) patched to True; add a case asserting the button is hidden when False
- [test_launch_screen.py](python/tests/pilot/update/test_launch_screen.py): same
  patching for the Copy URL / Copy Command reveal assertions; add a test that the
  button label does **not** become "Copied!" when `copyToClipboard` returns False

**Integration tests need no changes**: the "Copy this command..." handlers in
[prompt_tracker.py](python/tests/integration/utils/prompt_tracker.py)
(`OPTIONAL_PROMPT_DEFAULTS`, uncounted) and the `side_effect` regex handlers in
test_app.py simply never fire when the prompt is skipped.

## Optional (only if a natural home exists)

A short note about `MAS_CLIPBOARD=osc52` for container usage in the relevant
`docs/guides/*.md`. The env var is also documented in the `commandBuilder` docstring
regardless.

## Verification

All via WSL per project convention (`.venv` lives in WSL):

```
wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli/python && \
  .venv/bin/python -m pytest tests/unit/common/test_command_builder.py \
  tests/pilot/tui/test_review_screen.py tests/pilot/update/test_launch_screen.py -v"
```

Then the full suite (pilot included, as CI runs it):

```
wsl bash -lc "cd /mnt/c/Users/097891866/Documents/GitHub/ibm-mas/cli/python && \
  .venv/bin/python -m pytest tests -x -q"
```

Manual end-to-end check in a container (with `MAS_CLIPBOARD=osc52` baked into the
image, the prompt should appear and `y` should copy via OSC 52 in Windows Terminal):

```
docker run -it --rm <mas-cli image> bash
  # inside: mas install ... → clipboard prompt appears; y copies via OSC 52
docker run -it --rm -e MAS_CLIPBOARD=off <mas-cli image> bash
  # inside: clipboard prompt skipped entirely (save-as-script still offered)
```

## Finally

Copy this plan to `.bob/plans/2026-11-26-clipboard-availability-osc52.md` per the
repo's plan-location convention.
