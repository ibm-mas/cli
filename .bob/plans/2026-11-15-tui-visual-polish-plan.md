# TUI Visual Polish Plan

**Status:** phase 1 implemented (November 2026) · phases 2–5 pending · **Branch:** `textual-update` · **Date:** November 2026

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

## Phase 3 — Consistency and component extraction (~half day)

### 3.1 Unify content padding and footer patterns

Content padding is currently `1 2` (StepScreen, ConfirmUpgradesScreen),
`1` (ConnectStepScreen, `#dep-content`, `#launch-content`), and `0`
(`#review-content` inner). The gutter changing width between steps reads
as inconsistent. Pick one (`padding: 1 2`) and give every screen's
scrollable content the same class/id. Align the near-identical footer
patterns (`#dep-footer` / `#launch-footer` / `#review-footer`).

### 3.2 Extract a shared `StepChecklist` widget

`auto_run.py` and `launch.py` each duplicate `_pending_label`,
`_label_to_id`, `_mark_active`, `_mark_done`, `_mark_error`, `reset`;
`app.tcss` carries three copies of the "strip ListView highlighting"
block. Extract one `StepChecklist` widget (list + state machine + one
CSS block): ~150 lines removed, and the two screens are guaranteed to
look identical forever. Same for a shared footer/action-bar component.
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
| 3 | Padding unification, StepChecklist extraction | ~half day |
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
