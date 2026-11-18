# Plan: Refactor Non-Interactive Command Generation (install + generic builder)

## Context

Interactive `mas install` ends by printing an equivalent non-interactive command so users can re-run the install without the prompts. The implementation is clunky and buggy, and the same hand-rolled pattern is duplicated for `aiservice-install`. The user wants (a) the install implementation improved and (b) the capability extracted into something reusable for other interactive flows — **delivered on a new branch based on master, entirely independent of the textual-update work**, to be consumed by textual-update later.

## Execution setup

- Working tree on `textual-update` is clean and pushed (verified: `git status -sb` in sync with origin).
- Create branch from master with no upstream: `git checkout --no-track -b install-command-builder master` (per user's global git rules; plain `git push` later must go to a new remote branch of the same name).
- Save this implementation plan to `.bob/plans/2026-11-17-install-command-builder.md` (project convention).
- All test/lint runs via WSL: `wsl bash -lc "cd ... && python -m pytest ..."`. Commits made from WSL (pre-commit hook only resolves there; black may reformat on first attempt).
- **Scope on this branch: Phases 1-3 below.** Phase 4 (TUI wiring: `WorkflowField.cli_flag`, review-screen rendering) is deferred to the textual-update branch, which will consume the generic builder produced here.

## How it works today

- The interactive flow is the **prompt_toolkit wizard** (`InstallApp.interactiveMode()`, [app.py:2125](python/src/mas/cli/install/app.py#L2125)) — not the Textual TUI (which currently only serves `mas update`).
- The command is built by `installArgBuilderMixin.buildCommand()` — a single **~700-line procedural method** at [argBuilder.py:18-714](python/src/mas/cli/install/argBuilder.py#L18-L714): a chain of `if self.getParam("x") != "":` guards appending f-strings, with `newline = " \\\n"` line continuations. Secrets are emitted as `export VAR=x` placeholder lines up front, then referenced as `$VAR`.
- Displayed only as console text before the install summary ([app.py:2936-2943](python/src/mas/cli/install/app.py#L2936-L2943)). No clipboard, no file.
- A near-clone exists for `mas aiservice-install` ([aiservice/install/argBuilder.py](python/src/mas/cli/aiservice/install/argBuilder.py)).
- The flag inventory is maintained **by hand in three places**: the argparse parser ([install/argParser.py](python/src/mas/cli/install/argParser.py), 1769 lines), the builder, and the params validation list ([install/params.py](python/src/mas/cli/install/params.py)).
- **Zero test coverage** — nothing asserts anything about the generated string.

## Verified defects (symptoms of the design)

| Defect | Location |
|---|---|
| `--msk-cidr-az2` / `--msk-cidr-az3` both read `aws_msk_cidr_az1` (copy-paste) | [argBuilder.py:622-624](python/src/mas/cli/install/argBuilder.py#L622-L624) |
| `command += "--eck"` with no leading space → `--eck--eck-enable-logstash` when logstash also set | [argBuilder.py:94-97](python/src/mas/cli/install/argBuilder.py#L94-L97) |
| `if self.getParam("skip_grafana_install") is True:` — `getParam` returns `str`, so this is always False; `--skip-grafana-install` and `--skip-pre-check` are never emitted | [argBuilder.py:259](python/src/mas/cli/install/argBuilder.py#L259), [argBuilder.py:701](python/src/mas/cli/install/argBuilder.py#L701) |
| `--slack-token $SLACK_TOKEN` emitted but no `export SLACK_TOKEN=x` placeholder line exists | [argBuilder.py:694-695](python/src/mas/cli/install/argBuilder.py#L694-L695) |
| `mas_appws_upgrade_type == "true"` compared against upgrade-type values (`regularUpgrade`/`onlineUpgrade`) | [argBuilder.py:358](python/src/mas/cli/install/argBuilder.py#L358) |
| No shell escaping — values naively wrapped in `"`; an embedded quote breaks the script | throughout |
| Assorted spacing glitches (` --allow-special-chars \`, double spaces) | various |

## (a) Improving the install implementation

1. **Fix the listed bugs now** — they're cheap, independent, and users are hitting them today (the msk-az and `is True` ones mean the generated script is simply wrong for those configurations).

2. **Make it data-driven.** Replace the if-chain with a declarative spec — a list of entries like `{flag, param, kind: value|boolean, env_var?, condition?}` — plus a small generic renderer (~50 lines) that handles quoting (`shlex.quote`), spacing, and line wrapping uniformly. The secret handling becomes one `param → env var` map used for both the `export` block and the `$VAR` references, which makes the missing-`SLACK_TOKEN` bug class impossible by construction.

3. **Derive flag names from the parser instead of re-spelling them.** The argparse parser already knows every flag name and its `dest` (which equals the params key). Walk `parser._actions` for names/dests/types and keep a small side-table only for what argparse can't express: emit conditions and secret treatment. This collapses the three-places inventory to ~one. `SENSITIVE_PARAMS` in [displayMixins.py](python/src/mas/cli/displayMixins.py) can seed the secret table.

4. **Add a round-trip test (highest value / lowest effort).** Feed a params scenario into `buildCommand()`, `shlex.split` + env-substitute the output, parse it with the *real* `installArgParser`, and assert the resulting namespace matches the source params. This test would have caught every bug listed above and guards against future drift. Fits naturally in `tests/unit/install/` using the scenario-registry pattern from `tests/scenarios/`.

5. **UX polish:**
   - Print the command again at the *end* of the run so it isn't lost in scrollback.
   - Copy-to-clipboard — `pyperclip` is already a dependency (used in the update TUI launch screen, [tui/screens/launch.py:236](python/src/mas/cli/tui/screens/launch.py#L236)).
   - Offer to save it to a file (e.g. alongside the workspace's config output) rather than only stdout.

## (b) Generalizing to other interactive flows

- **Extract a generic `CommandBuilder`** (e.g. `mas/cli/common/commandBuilder.py`): `render(prog, parser_or_spec, params, secrets)`. Both `install` and `aiservice-install` become thin per-command secret/condition tables over it.
- **Legacy prompt flows get it nearly free.** Every command app (`upgrade`, `backup`, `restore`, `mirror`, …) already has an argparse parser whose dests are the params keys, and writes into the shared `BaseApp.params` dict ([cli.py:429-439](python/src/mas/cli/cli.py#L429-L439)). `backup`/`restore` already maintain `requiredParams`/`optionalParams` lists — the same pattern the generic builder would consume. So `mas upgrade` etc. could grow the same "here's your non-interactive command" feature with a small table each.
- **Wire it into the Textual TUI framework.** Add a `cli_flag` attribute to `WorkflowField` in [tui/models.py](python/src/mas/cli/tui/models.py) (fields already carry `id` → params key, `sensitive`, `default`). Then the generic review screen ([tui/screens/review.py](python/src/mas/cli/tui/screens/review.py)) can render an "equivalent command" section for *any* workflow, and the launch screen already has the clipboard plumbing. Since `serveTuiMode` ([tui/shell.py:342](python/src/mas/cli/tui/shell.py#L342)) resolves any command's TUI by convention, every future TUI flow inherits the feature automatically — `mas update` would be the first consumer.

## Suggested sequencing

### Phase 1 — Bug fixes + round-trip test (protects users immediately, no design change)

1. Fix the verified defects in [argBuilder.py](python/src/mas/cli/install/argBuilder.py):
   - `--msk-cidr-az2`/`--msk-cidr-az3` reading `aws_msk_cidr_az1` (lines 622-624)
   - `--eck` missing leading space → `--eck--eck-enable-logstash` (lines 94-97)
   - `is True` string comparisons killing `--skip-grafana-install` (line 259) and `--skip-pre-check` (line 701) — compare against `"true"` as the wizard stores it
   - missing `export SLACK_TOKEN=x` placeholder (lines 694-695 vs the export block at lines 22-73)
   - `mas_appws_upgrade_type == "true"` compared against upgrade-type values (line 358)
   - spacing glitches (` --allow-special-chars \`, double spaces)
2. Check the same defect classes in [aiservice/install/argBuilder.py](python/src/mas/cli/aiservice/install/argBuilder.py) and fix.
3. Add a **round-trip test** in `python/tests/unit/install/`: build scenarios of `self.params` (+ the loose instance attributes), call `buildCommand()`, `shlex.split` the command portion with env-var placeholders substituted, parse with the real `installArgParser`, assert the resulting namespace matches the source params. Cover at minimum: default install, ECK+logstash, MSK, grafana-skip, slack, secrets present (assert no plaintext secret in output).

### Phase 2 — Data-driven install builder

4. Replace the if-chain with a declarative spec: list of `{flag, param, kind: value|boolean, env_var?, condition?}` entries plus a small renderer (~50 lines) that owns quoting (`shlex.quote`), spacing, and ` \\\n` wrapping uniformly. One `param → env var` map used for both the export block and `$VAR` references.
5. Derive flag names from the parser where possible (`installArgParser._actions` gives flag + dest); the side-table carries only conditions and secret treatment. `SENSITIVE_PARAMS` in [displayMixins.py](python/src/mas/cli/displayMixins.py) seeds the secret table.
6. The round-trip test from Phase 1 must pass unchanged — it's the correctness gate for the refactor.

### Phase 3 — Extract generic CommandBuilder, migrate aiservice-install

7. Move the renderer + spec types to `mas/cli/common/commandBuilder.py`: `render(prog, spec_or_parser, params, secrets)`.
8. Migrate `aiservice/install/argBuilder.py` onto it as a thin table; delete the duplicated if-chain.
9. UX polish in both display sites: reprint the command at end of run (not only before the summary), copy-to-clipboard via `pyperclip` (already a dependency), and offer to save to a file.

### Phase 4 — TUI wiring (DEFERRED to textual-update)

Add `cli_flag` to `WorkflowField` in [tui/models.py](python/src/mas/cli/tui/models.py); generic review screen renders an "equivalent command" section; `mas update` first consumer. Loosely specified here — designed properly on textual-update when it consumes the Phase 3 builder.

## Verification

- Phase 1-3 all gated by the round-trip unit tests (per command), plus new tests: escaping (values with spaces/quotes), secret redaction (no plaintext secret ever in output), boolean flags.
- Run via WSL per project convention; black/flake8 clean; `python -m pytest python/tests` passes (note: on this branch the pilot/update tests from textual-update won't exist — master's suite is the baseline).
- Manual smoke: run the install wizard far enough to see the generated command, or drive `buildCommand()` via a scenario in a REPL.
