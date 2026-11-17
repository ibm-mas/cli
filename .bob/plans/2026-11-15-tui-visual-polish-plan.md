# TUI Visual Polish Plan

**Status:** phase 1 + 2 implemented (November 2026) · phases 3–5 pending · **Branch:** `textual-update` · **Date:** November 2026

> **Implementation notes (phase 2, landed November 2026):**
>
> - Content measure: **tried and reverted** — panels were capped at
>   `max-width: 100`, but on review the capped left-aligned column read
>   worse than a full-width content area, so the RHS now expands to fill
>   all horizontal space again (guarded by
>   `test_step_panel_fills_content_area`). The wrap rules added for the
>   capped layout (`.connect-url`, `.connect-error`) are kept — long
>   URLs still fold on terminals narrower than the URL.
> - `#action-dialog` / `#params-dialog` gained `max-width: 100` (kept —
>   dialogs ballooning across 200 columns still looked bad).
> - Minimum terminal size: Textual 8.2.8 (the latest release — the
>   dependency is unpinned, nothing newer to upgrade to) has no
>   `App.MIN_WIDTH` / `MIN_HEIGHT`, so the shell implements it itself:
>   `MIN_WIDTH = 70` / `MIN_HEIGHT = 20` class attributes plus an
>   `on_resize` handler that pushes/pops a blocking
>   `TerminalTooSmallScreen` modal (new `tui/screens/size_notice.py`,
>   `width: 44` dialog with `max-width/max-height: 100%` so it fits even
>   at tiny sizes). If the terminal recovers while another modal sits
>   above the notice, the notice is marked stale and pops itself on
>   `ScreenResume`. The app-level `q` binding still works while shown.
> - Responsive: `TextualShell.HORIZONTAL_BREAKPOINTS = [(0, "-narrow"),
>   (100, "-normal")]` plus a `Screen.-narrow #sidebar { display: none }`
>   rule hides the sidebar below 100 columns. Note this also hides it at
>   the pilot default 80×24 — existing sidebar queries still pass because
>   display:none widgets remain in the DOM.
> - Regression tests: `tests/unit/tui/test_tui_shell_sizing.py` (notice
>   shown / removed on recovery / not shown at normal size; sidebar hidden
>   below the breakpoint and visible above it; panel and params-dialog
>   width caps at 160 cols). Full TUI unit + pilot suites green
>   (227 passed), black and flake8 clean.
> - Follow-up fix (same day): the content cap clipped long unbreakable
>   strings — the connect screen's reuse-connection URL (117 chars) was
>   cut off at the panel edge because `.connect-url` had `width: auto`
>   and no wrap. `.connect-url` and `.connect-error` now carry
>   `width: 100%; text-wrap: wrap` (Textual folds words longer than the
>   line, so the URL wraps onto two lines and stays fully visible).
>   Audited the other long-value widgets — `.context-value`,
>   `#pipeline-url`, `.description-para`, checklist items, and the review
>   screen's Markdown paragraphs all already fold. Regression test:
>   `test_long_console_url_wraps` in `pilot/update/test_connect_screen.py`
>   (228 passed total).
> - Second follow-up: ctrl+click on a *folded* plain-text URL only
>   selected the line fragment under the cursor. New
>   `tui/links.py::linkText(url, prefix="")` builds a Rich `Text` whose
>   URL portion carries a `link` style — Textual renders Rich link styles
>   as OSC 8 terminal hyperlinks (verified end-to-end: every folded line
>   is wrapped in an escape pointing at the full URL), so ctrl+click now
>   opens the complete URL. Applied to the connect reuse URL and the
>   launch pipeline URL; both pilot tests assert the link span. This
>   partially delivers phase 4's "Clickable URLs" item (the two
>   interactive URLs are done; rendering description paragraphs through
>   `Markdown` for autolinkified doc links remains open).

> **Implementation notes (phase 1, landed November 2026):**
>
> - All four screens' heading Labels now carry `classes="step-heading"`;
>   `.description-para` is `$text-muted`. One deviation from the hierarchy
>   table: field labels keep normal `$text` (Textual has no "slightly
>   muted" variable between `$text` and `$text-muted`) — muted
>   descriptions, normal labels, full-contrast input values reads clean.
> - Glyphs: `○` pending, `◐` active, `✓` done, `✗` failed, everywhere
>   (sidebar, dep/launch checklists, error prefixes). All button icons
>   removed ("Confirm & Continue", "Abort Update", "Copy URL", "Done",
>   "Dismiss", "Quit", "Reset", "Copied!"); `Next →` keeps its arrow.
> - Sidebar is `width: 34` with `border-right: solid $primary-darken-3`;
>   `#step-content` switched from `75%` to `1fr`. Dialogs use
>   `border: round $primary-darken-2`.
> - The active-step glyph is a static `◐` everywhere: a sidebar
>   `set_interval` spinner (cycling `◐◓◑◒`) was tried and removed the same
>   day — the constant motion next to steady text read as noise. Textual
>   8.2.8 has no `Spinner` widget, so an animated variant would have to be
>   timer-driven; revisit only with a calmer cadence or a screen-level
>   (not sidebar-level) activity indicator.
> - Tests updated to the new glyphs: `unit/update/
>   test_update_auto_run_screen.py`, `pilot/update/test_launch_screen.py`
>   (button-label tests select by widget id, so label changes needed no
>   test edits). Full TUI unit + pilot suites green (216 passed), black
>   and flake8 clean.

> Design review of the Textual TUI (`mas update` vertical slice) for
> appearance / quality / professional finish. No changes made yet — this
> document records the findings and a phased plan of action. Sizes and
> values given are starting points to be eyeballed in
> `textual run --dev mas.cli.tui.dev` (hot-reloads
> `tui/styles/app.tcss`).

## Background

The TUI's architecture is sound: single consolidated stylesheet, Textual
theme variables (no hardcoded colors), worker threads for blocking work,
inline validation instead of modal error popups. The gaps are all in the
"finish" layer — typography hierarchy, icon consistency, spacing
uniformity, and a handful of UX niceties. Items are grouped into phases by
impact; phase 1 alone accounts for most of the perceived jump from
"functional" to "polished".

## Phase 1 — High-impact visual fixes (~half day)

### 1.1 Style the step headings (biggest single win)

Every screen yields `Label(step.heading, id=f"heading-{step.id}")`, but
**no CSS rule matches those ids** — headings currently render as plain
body text. Add a shared class on the heading Labels (e.g.
`classes="step-heading"`) plus:

```css
.step-heading {
    text-style: bold;
    color: $text;
    margin-bottom: 1;
}
```

Then establish a text hierarchy across all screens:

| Role | Treatment |
|---|---|
| Step heading | bold, full-contrast `$text` |
| Description paragraphs | `$text-muted` |
| Field labels | normal, slightly muted |
| Body / values | normal `$text` |

`.description-para` has margins but no color treatment today, so
everything reads at the same volume. Differentiating text "loudness"
via mutedness is the core of a designed-looking TUI.

Files: all screens in `tui/screens/` + `tui/styles/app.tcss`.

### 1.2 Replace emoji state icons with monochrome glyphs + color

Current icons: ⬜ ⏳ ✅ ❌ 📋 ↺. Problems:

- Colored emoji (✅ ❌ 📋) **ignore CSS colors** and render differently
  per terminal/font (sometimes double-width, sometimes with a background
  square) — the classic "looks fine on my machine" trap.
- State is double-encoded: glyph *and* CSS class both say "done"
  (`step-completed` = `$success` green).

Target: monochrome glyphs + CSS color does the talking:

| State | Glyph | Color |
|---|---|---|
| Pending | `○` | `$text-muted` |
| In progress | `◐` (or animated spinner, see 1.4) | `$accent` |
| Done | `●` or `✓` | `$success` |
| Failed | `✗` | `$error` |

Files: `shell.py` (sidebar updates), `auto_run.py`, `launch.py`
(`_pending_label`, `_mark_active`, `_mark_done`, `_mark_error`),
`review.py` / `confirm_upgrades.py` button labels.

### 1.3 Button label cleanup

`📋 Copy URL`, `✓ Confirm & Launch`, `✕ Abort Update`, `↺ Reset`, `Next →`
mix color emoji, dingbats, and arrows. Go nearly icon-free on buttons:
"Confirm & Continue", "Copy URL", "Reset", "Quit". Keep the `→` in
"Next →" at most. Consistency beats decoration.

### 1.4 Sidebar: fixed width + softer border

- Replace `width: 25%` with a fixed width (start at `width: 34`, tune to
  longest heading + icon). 25% is 20 chars on an 80-col terminal
  (headings wrap) and 50 chars on a 200-col monitor (absurdly wide).
- Replace `border-right: solid $primary` (a loud saturated stripe) with
  `border-right: solid $panel-lighten-2` or `$primary-darken-3`.
  Reserve `$primary` saturation for things that mean something.
- Optional polish: an animated in-progress glyph (spinning `◐◓◑◒`) for
  the active sidebar step — Textual `Spinner` widget or CSS animation.

### 1.5 Soften dialog borders

`#action-dialog` and `#params-dialog` use `border: thick $primary` —
heavy. Use `border: round $primary-darken-2` or `$panel-lighten-2`.

## Phase 2 — Sizing and layout constraints (~2–3 hours)

Keep the shell **fluid full-screen** (fixed-size floating window looks
more amateur, not less) but constrain the internals:

- **Content pane max-width:** paragraphs stretching across 140+ columns
  on wide monitors hurt readability. Give scrollable content
  `max-width: 100` (tune; ~100–120), left-aligned or centered.
- **Dialog max-width:** `#action-dialog` / `#params-dialog` are
  `width: 70%` — add `max-width: 100` so they don't balloon on wide
  terminals.
- **Minimum terminal size:** set `App.MIN_WIDTH` / `App.MIN_HEIGHT`
  class attributes on `TextualShell` so Textual shows its
  "terminal too small" notice instead of a broken layout. One-liner.
- **Responsive (nice-to-have):** Textual screen breakpoints
  (`App.breakpoints`) — hide the sidebar below ~100 columns via a
  `.-narrow` CSS variant. Only if cheap.

## Phase 3 — Consistency and component extraction (~1 day)

### 3.1 Unify content padding and footer patterns

Two distinct levels of consistency are in play here, and it's worth
naming them separately:

1. **Consistent framework** — the shell-level chrome (Header, step
   sidebar, Footer keybinding bar, mounted once in
   `TextualShell.compose()`). This is *already* persistent across every
   screen and must stay that way; nothing in this phase should touch it.
2. **Consistent screen layout** — the pattern *inside* `#step-content`.
   Today this splits into two camps: `auto_run` / `launch` / `review`
   each hand-roll a pinned footer (`#dep-footer` / `#launch-footer` /
   `#review-footer`, all `height: auto`), while `StepScreen` and
   `ConfirmUpgradesScreen` have no action bar at all — their "Next →"
   button and validator error trail the scrollable content, so the
   button's position depends on how many fields the step has and can
   scroll out of view. `ConnectStepScreen` is a hybrid: buttons live
   inside the scrollable sub-screens (like StepScreen) while only the
   busy indicator and error label are pinned below.

The goal for level 2 is **not** "every screen must have an action bar" —
future screen types may legitimately not need one (a read-only
interstitial, a log viewer, etc.). The goal is that **if a screen needs
an action bar, there is a single way to achieve it**, and the result is
pixel-identical across screens:

```
------------------------- header --------------------------
[LHS sidebar] | [scrollable step content]
              | --------------------------------------------
              | [status message row — reserved, may be empty]
              | [action buttons — always the same row]
------------------------- menu -----------------------------
```

Concretely:

- **Content padding:** currently `1 2` (StepScreen,
  ConfirmUpgradesScreen), `1` (ConnectStepScreen, `#dep-content`,
  `#launch-content`), and `0` (`#review-content` inner). The gutter
  changing width between steps reads as inconsistent. Pick one
  (`padding: 1 2`) and give every screen's scrollable content the same
  class/id.
- **Action bar height:** fixed, not `height: auto` — the
  content/action-bar boundary must sit at the same row on every screen.
- **Reserved status row:** the prompt/error label keeps its row even
  when empty or hidden, so revealing an error message or a button never
  shifts the layout. (Today `#dep-footer` grows when `dep-error` appears,
  pushing the content area up.)
- **StepScreen / ConfirmUpgradesScreen conversion:** move "Next →" and
  the validator error label out of the scrollable content and into the
  shared action bar (see 3.2), so their buttons sit at the same position
  as every other screen's.

### 3.2 Extract a shared `StepChecklist` widget

`auto_run.py` and `launch.py` each duplicate `_pending_label`,
`_label_to_id`, `_mark_active`, `_mark_done`, `_mark_error`, `reset`;
`app.tcss` carries three copies of the "strip ListView highlighting"
block. Extract one `StepChecklist` widget (list + state machine + one
CSS block): ~150 lines removed, and the two screens are guaranteed to
look identical forever.

Extract a shared **`ActionBar`** component alongside it — this is the
mechanism behind 3.1's "single way to get an action bar". One widget
owning the fixed-height bar, the reserved status row (prompt / error /
guidance text), and the button row; one CSS block replacing
`#dep-footer` / `#launch-footer` / `#review-footer` and their per-screen
button/prompt/error rules. Screens declare buttons and status text; the
component guarantees position and styling. Screens that need no action
bar simply don't compose one — the framework (3.1 level 1) is
unaffected either way. This is also where the
StepScreen / ConfirmUpgradesScreen conversion (3.1) lands: their
"Next →" and validator error move into the ActionBar. ConnectStepScreen
converts the same way (its Yes/No/Connect buttons move out of the
scrollable sub-screens into the action bar; the busy indicator and
error label become the status row). Note the action bar stays *inside*
each screen's panel rather than hoisted to the shell — hoisting would
rework how screens communicate actions to the shell for no visible
gain, since the fixed height makes per-screen copies pixel-identical
anyway.

Revisit the phase-3 pilot tests in the pilot-test plan afterwards — they
should largely survive a mechanical extraction.

### 3.3 Header / Footer chrome

Currently both flattened to `$background` (chrome disappears entirely).
Try a very subtle tint (`$surface`) and compare. Defensible either way —
eyeball it.

### 3.4 Custom theme (optional)

Consider registering a Textual 1.x custom `Theme` (brand primary/accent,
or pin a known-good built-in) instead of the default theme variables.
One place to define the palette; enables a dark/light toggle keybinding
later. Only if there's a brand-color mandate — default variables are
otherwise fine.

## Phase 4 — UX niceties (~half day)

- **Confirm before quitting.** `q` and every `✕ Quit` button call
  `app.exit(1)` instantly — one stray keypress destroys a half-completed
  workflow. Push a small confirmation modal ("Quit? Nothing will be
  launched. y/N").
- **`notify()` toasts for transient feedback.** The clipboard feedback in
  `launch.py` hand-rolls a button-label swap + timer;
  `self.notify("Pipeline URL copied to clipboard")` is idiomatic and
  animated.
- **Clickable URLs.** The MongoDB backup docs URL sits in a plain
  `Label` (not ctrl+clickable). Render description paragraphs — or at
  least links — through Textual's `Markdown` widget to linkify.
- **Title the action overlay.** `Running…` → `"Running: <step
  heading>"` — mid-flow users shouldn't have to remember what triggered
  a modal.
- **Rename the `p` footer binding.** Footer advertises `p Debug params`
  — dev tooling in production chrome. Rename to "Params" (it's genuinely
  useful) or hide behind an env var.
- **Review screen as a table.** The generic summary renders
  `**Label:** value` markdown lines; a two-column `DataTable` (or
  markdown table) with aligned columns scans better and matches the
  `ParamsOverlay` visual language.
- **Sidebar affordance (defer-able).** Steps are non-clickable
  (`can_focus = False`) but users will try. Either allow read-only
  visits to completed steps (with a Back control) or add a muted hint.
  Reset-on-review covers the need today; lowest priority here.

## Phase 5 — Dev-loop and regression guards (~2 hours)

- **SVG screenshots:** `app.export_screenshot()` / `textual run --svg`
  — for PR descriptions, docs, and eyeballing layout without re-running
  the flow. Cheap visual history of the design.
- **CSS regression pilot test:** one pilot test asserting computed CSS
  (sidebar width, heading styles present) so a stylesheet regression
  can't land silently. Builds on the existing pilot harness
  (`tests/pilot/harness.py`).
- **Snapshot testing** is already listed as deferred in the pilot-test
  plan (`pytest-textual-snapshot`) — the visual polish phases here are
  exactly the point where it becomes worth doing (4–5 screens, styled).
  Do it after phases 1–3 settle so snapshots capture the polished state,
  not the current one.

## Suggested order and effort

| Phase | Theme | Effort |
|---|---|---|
| 1 | Headings, icons, buttons, sidebar/border | ~half day |
| 2 | Sizing constraints | ~2–3 hours |
| 3 | Padding unification, StepChecklist + ActionBar extraction, StepScreen/Connect conversion | ~1 day |
| 4 | UX niceties | ~half day |
| 5 | SVG export, CSS regression test | ~2 hours |

If only three things are done: **1.1** (heading/text hierarchy), **1.2**
(monochrome glyphs + color), and **1.4** (fixed sidebar width, softer
border).

## Verification

- `textual run --dev mas.cli.tui.dev` with `COMMAND = "update"` for live
  CSS iteration (already set up in `tui/dev.py`).
- Existing unit + pilot suites stay green (`wsl bash -lc` per repo
  convention); phase 3.2's extraction re-runs
  `tests/pilot/update/` specifically.
- Eyeball across: narrow terminal (~80 cols), typical (~120), wide
  (~200), and at least one non-emoji-aware font to confirm the
  monochrome glyph choice.
