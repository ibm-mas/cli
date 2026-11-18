# TUI Visual Polish Plan

**Status:** phases 1–3.4 implemented (November 2026) · phases 4–5 pending · **Branch:** `textual-update` · **Date:** November 2026

> **Implementation notes (phase 3.4, landed November 2026):**
>
> - Custom theme: new `tui/theme.py` defines `MAS_THEME` — an IBM
>   Carbon-derived dark palette (primary Blue 60 `#0F62FE`, accent /
>   secondary Blue 40 `#78A9FF`, background / surface / panel Gray
>   100 / 90 / 80, success Green 40, warning Yellow 30, error Red 40) —
>   registered and selected by two lines in `TextualShell.__init__`
>   (`register_theme(MAS_THEME)` + `self.theme = "mas"`).
> - **Rollback isolation (the point of landing 3.3 and 3.4 separately):**
>   the entire 3.4 change is `tui/theme.py`, `tests/unit/tui/
>   test_tui_theme.py`, and the import + two registration lines in
>   `shell.py` — one commit, revertable with `git revert` to restore the
>   default Textual theme with no other behaviour change.  This works
>   because the stylesheet only ever references theme *variables*
>   (`$surface`, `$primary-darken-3`, …), never literal colours: the 3.3
>   chrome tint follows whichever theme is active (there is a test
>   proving it renders the MAS theme's surface).
> - Every semantic colour is specified explicitly — Textual derives
>   unspecified theme colours from `primary`, which turns success /
>   warning / error blue and makes the sidebar / checklist state glyphs
>   indistinguishable (guarded by
>   `test_mas_theme_defines_semantic_colors`).
> - Tests: `tests/unit/tui/test_tui_theme.py` (4 tests — theme selected
>   and variables resolve to the brand palette, chrome tint follows the
>   custom theme, semantic colours explicit, dark=True).  Colour
>   comparisons parse and use a per-channel tolerance of 2 because
>   Textual's HSL variable generation can shift a channel by one.
>   Full TUI unit + pilot suites green (107 passed), black and flake8
>   clean.  A dark/light toggle keybinding remains future work, as the
>   plan section anticipated.

> **Implementation notes (phase 3.3, landed November 2026):**
>
> - Chrome tint: the Header/Footer override blocks in `app.tcss` changed
>   `background: $background` → `background: $surface` — one subtle step
>   lighter, so the chrome reads as a frame around the content instead of
>   disappearing into it.  (Eyeball with
>   `textual run --dev mas.cli.tui.dev`; reverting is the one-line CSS
>   swap back to `$background`.)
> - The rule uses the `$surface` *variable*, not a literal colour, so the
>   tint follows whatever theme is active — it stays correct when the
>   phase 3.4 custom theme lands (or if that theme is later rolled back).
> - Regression test: `tests/unit/tui/test_tui_shell_chrome.py` asserts the
>   computed Header/Footer backgrounds equal the active theme's `$surface`
>   (and that `$surface` differs from `$background`, so the rule can never
>   silently become a no-op).  Theme-agnostic by construction.  Full TUI
>   unit + pilot suites green (103 passed), black and flake8 clean.
> - Deliberately **kept separate from 3.4**: this change is CSS-only plus
>   its test, in its own commit, so the custom-theme work can be reverted
>   independently of the chrome tint.

> **Implementation notes (phase 3.2, landed November 2026):**
>
> - Pure Python extraction, **no visual change**:
>   `tests/pilot/tui/test_screen_layout.py` passed unchanged; full TUI
>   unit + pilot suites green (240 passed — 206 unit + 34 pilot, net +6:
>   8 new widget tests, 2 auto-run `_mark_done` tests moved), black and
>   flake8 clean.  (The one failure in the wider repo suite,
>   `must_gather/test_timer.py`, is a known load-sensitive timing flake
>   that passes in isolation and touches nothing TUI-related.)
> - New `tui/widgets/` package exporting `StepChecklist` and `ActionBar`.
> - **StepChecklist(ListView)**: owns the item list, the
>   pending/active/done/error class transitions, the glyph text updates,
>   and the module helpers `pending_label` / `label_to_id` (previously
>   byte-duplicated as `_pending_label` / `_label_to_id` in auto_run.py
>   and launch.py).  Constructor takes the labels plus an id prefix
>   (`dep-step-` / `launch-step-`), keeping the item and list ids the
>   pilot tests query.  `mark_active` appends unknown labels (launch's
>   dynamic RBAC stages); `mark_done` accepts an
>   `on_done(label, ok, detail) -> text | None` hook — launch's Submit
>   PipelineRun special case (URL to `#pipeline-url`, name-only item
>   text, Copy URL reveal) became the screen's `_on_checklist_done`
>   hook returning override text; `mark_error_first_pending` carries
>   launch's first-still-pending error marking, while dep's status-row
>   error stays in the screen.  `_mark_error` therefore remains a screen
>   method on both, delegating to the primitive where applicable.
> - **ActionBar(Vertical)**: owns the reserved status row —
>   `set_status` / `set_error` / `clear_status` / `has_error` — the
>   button row (screens pass their Buttons in and keep owning
>   `on_button_pressed`), and the optional leading busy spinner
>   (`busy=True` + `show_busy` / `hide_busy`).  The spinner id changed
>   `connect-busy-spinner` → `action-busy-spinner` and visibility is now
>   Python display-toggling, so the `connect-busy--visible` CSS class
>   rules are gone (the two connect pilot busy assertions now check
>   `.display` instead of the class).  The widget applies the shared
>   `action-bar` class itself; status label ids are kept via a
>   `status_id` arg (`dep-prompt`, `launch-prompt`, `review-prompt`,
>   `validator-error-{step.id}`, `connect-status-label`).  The dropped
>   `#connect-status` and `#*-buttons` row ids were queried by nothing.
> - CSS: one `.step-checklist` class (background/hover/focus stripping +
>   item Label wrap) is shared by the StepChecklist widget **and the
>   sidebar's `#step-list`** (which just carries the class in
>   `shell.compose`); a `.step-checklist--boxed` variant carries the
>   bordered-box geometry the two in-content lists need and the sidebar
>   must not get.  The three per-id blocks (`#step-list`,
>   `#dep-step-list`, `#launch-step-list`) are gone.
> - Tests: new `tests/unit/tui/test_step_checklist.py` covers the
>   marking primitives and the on_done hook contract; auto_run's
>   `_mark_done` unit tests moved there and its `_pending_label` import
>   now points at the widget's `pending_label`; the two launch
>   `_mark_done` unit tests were rewritten to drive a real StepChecklist
>   wired to the screen's hook.  Screens keep `_step_labels` as
>   construction-time data (the widget copies it; the widget's `labels`
>   property is the live list that grows with dynamic stages).

> **Implementation notes (phase 3.1, landed November 2026):**
>
> - Content padding: new shared `.content-scroll` class (`padding: 1 2`,
>   `height: 1fr`) carried by every screen's scrollable content — the
>   inner scrolls of StepScreen / ConfirmUpgradesScreen, `#dep-content`,
>   `#launch-content`, `#review-content`, and the connect screen's root
>   (which *is* the scroll). Review's Markdown widget padding is stripped
>   (`#review-content Markdown { padding: 0 }`) because its own `0 2`
>   previously combined with the screen padding — every screen's content
>   now starts at the same column.
> - Action bar: shared `.action-bar` / `.action-status` / `.action-buttons`
>   classes replace the per-screen `#dep-footer` / `#launch-footer` /
>   `#review-footer` rules. The bar height is **fixed at 6** (border-top 1 +
>   status row 1 + gap 1 + buttons 3; vertical padding is 0 — the border
>   already separates the bar from the content and the buttons sit flush
>   against the panel's bottom edge) so the content/action-bar boundary
>   sits on the same row on every screen. (First pass used padding 1 2 for
>   a height of 8; tuned down to 6 the same day — three blank rows read
>   as excessive dead space.)
> - Reserved status row: `.action-status` is always one row (`height: 1`,
>   `text-wrap: nowrap`, `text-overflow: ellipsis` — verified end-to-end
>   that a long message paints with a trailing `…` rather than wrapping).
>   The dep screen's prompt and error labels merged into that one row
>   (`#dep-prompt` shows guidance until a failure, then the `✗` error in
>   red bold via `.action-status--error`); the dropped "The update cannot
>   proceed…" second sentence was redundant next to the error itself.
>   StepScreen / ConfirmUpgradesScreen validator errors render in the same
>   reserved row (same class toggle) instead of a `display:none → block`
>   label that grew the layout.
> - StepScreen / ConfirmUpgradesScreen conversion: roots changed
>   `VerticalScroll` → `Vertical` with the content wrapped in an inner
>   `.content-scroll`; "Next →" / "Confirm & Continue" and the validator
>   error moved out of the scrollable content into the pinned action bar,
>   so those buttons no longer scroll out of view and sit at the same
>   position as every other screen's. AutoRunScreen / LaunchScreen roots
>   also changed to `Vertical` (the root scroll previously wrapped
>   content + footer, making the "pinned" footer technically scrollable).
> - The review prompt was shortened ("Review your choices carefully —
>   mistakes are easier to fix now.") because the old two-sentence prompt
>   wrapped to two lines below ~120 columns, which the single reserved
>   row cannot do.
> - ConnectStepScreen converted the same day (it had been deferred to
>   3.2): root is now a Vertical with a `.content-scroll` area (heading +
>   ContentSwitcher, sub-screens are plain Verticals) and the shared
>   action bar below.  The Yes / No / Connect buttons moved out of the
>   scrollable sub-screens into the bar's button row, with visibility
>   following the active sub-screen (`_set_mode`); the busy indicator and
>   error label became the reserved status row — a Horizontal carrying
>   `.action-status` with a hidden `LoadingIndicator` spinner leading it
>   and `#connect-status-label` as the text (`.action-status > Label`
>   rules in the shared block apply the muted/ellipsis/error treatment to
>   the inner label).  The old `#reuse-buttons`, `#connect-busy`,
>   `#connect-busy-label`, `#connect-error-label` and `.connect-error`
>   rules are gone.  The credentials sub-screen's bar shows Connect plus
>  Cancel: Connect is disabled until both the server URL and login token
>  are entered (live via `on_input_changed`, replacing the old click-time
>  "Server URL is required" error), and Cancel returns to the reuse
>  sub-screen untouched — it is only shown when a connection was detected
>  (otherwise there is nothing to go back to).  With this, every screen in the update vertical slice
>   follows the standardized shape; 3.2's remaining work is the pure
>   Python extraction (ActionBar + StepChecklist widgets), not layout.
> - Regression tests: new `tests/pilot/tui/test_screen_layout.py` (bar
>   exactly 6 rows with a one-row status row and the same boundary row on
>   step/auto-run/launch/review/connect; uniform 1 2 content gutter incl.
>   the connect screen; a failing validator fills the reserved status row
>   without changing the bar height).  The dep failure pilot test was
>   updated for the merged status row; the connect pilot tests were
>   updated for the status-row ids and gained button-mode swap, disabled-
>   until-credentials, and cancel tests.  Full TUI unit + pilot suites
>   green (234 passed), black and flake8 clean.

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

## Phase 3 — Consistency and component extraction (~1 day; landed November 2026)

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

### 3.2 Extract the shared `StepChecklist` and `ActionBar` widgets

> **Rescoped November 2026, after the 3.1 implementation** (and landed
> later that month — see the phase 3.2 implementation notes at the top):
> everything
> this section originally promised *visually* — the
> StepScreen/ConfirmUpgradesScreen and ConnectStepScreen conversions, and
> the single CSS block replacing `#dep-footer` / `#launch-footer` /
> `#review-footer` — landed with 3.1 (see the implementation notes at
> the top). What remains is pure Python extraction with **no intended
> visual change**: the shared CSS plus
> `tests/pilot/tui/test_screen_layout.py` already lock the layout
> contract, so this is a maintainability refactor, not a design one.
> Acceptance for the whole phase: the full TUI unit + pilot suites
> (234 tests) stay green, black and flake8 clean, and
> `test_screen_layout.py` passes **unchanged**.

#### 3.2a `StepChecklist`

`tui/screens/auto_run.py` and `tui/screens/launch.py` still duplicate:

- `_pending_label` and `_label_to_id` — byte-identical module functions;
- `_mark_active` / `_mark_done` — near-identical methods;
- three copies of the ListView highlight-strip CSS block in `app.tcss`
  (`#step-list` in the sidebar, `#dep-step-list`, `#launch-step-list`).

(The original wording here also listed a `reset` method — it no longer
exists in either screen — and estimated ~150 lines removed, which dated
from before the CSS unification.)

Extract one widget (new `tui/widgets/` package,
`tui/widgets/step_checklist.py`) owning the ListView, the
pending/active/done/error class transitions and the glyph updates. This
is **not** a copy-paste-merge — the two screens genuinely differ, so the
widget needs hook points:

- **id prefix** (`dep-step-` vs `launch-step-`) — constructor arg; keep
  the resulting item ids stable, the pilot tests query them
  (`#dep-step-*`, `#launch-step-*`, `#launch-step-list`).
- **dynamic items** — launch's `_mark_active` appends labels it doesn't
  know (RBAC stages evaluated at runtime); build append-on-unknown into
  the widget or expose an `on_unknown_label` hook.
- **per-item completion side effects** — launch's `_mark_done`
  special-cases "Submit PipelineRun" (the URL goes to the dedicated
  `#pipeline-url` label and reveals Copy URL); expose an
  `on_done(label, ok, detail)` hook or a subclass override point.
- **`_mark_error` stays in the screens** — the two implementations do
  different things (dep: status-row error + Quit reveal; launch: mark
  the first still-pending list item); only the underlying item-marking
  primitive moves into the widget.

CSS: one `.step-checklist` class carrying the strip rules replaces the
three per-id blocks — including the sidebar's `#step-list`, which speaks
the same visual language.

Test touch points: `tests/unit/update/test_update_auto_run_screen.py`
imports `_pending_label` from `auto_run` — re-export it from the screen
module or move the import to the widget. Its `_mark_done` unit tests
test widget behaviour, not screen behaviour — move them to a new
`tests/unit/tui/` module for the widget.

#### 3.2b `ActionBar`

Six screens hand-compose the same structure
(`Vertical(.action-bar)` → status row + `Horizontal(.action-buttons)`),
and four of them duplicate the status-row error show/clear pattern
(`update(text)` + add/remove `action-status--error`). Extract one widget
(`tui/widgets/action_bar.py`) owning:

- the reserved status row — `set_status(text)` / `set_error(text)` /
  `clear_status()`;
- the button row — screens pass their `Button`s in and keep owning their
  `on_button_pressed` logic;
- the optional leading busy spinner (connect only) — `busy=True`
  constructor arg with show/hide helpers replacing connect's
  `connect-busy--visible` class toggling.

Keep the status label ids that screens and tests query (`#dep-prompt`,
`#validator-error-{step.id}`, `#connect-status-label`) — accept a
`status_id` constructor arg. The bar stays inside each screen's panel
(not hoisted to the shell), as before: hoisting would rework how screens
communicate actions to the shell for no gain, since the fixed height
makes per-screen copies pixel-identical anyway.

### 3.3 Header / Footer chrome

Currently both flattened to `$background` (chrome disappears entirely).
Try a very subtle tint (`$surface`) and compare. Defensible either way —
eyeball it.

### 3.4 Custom theme (optional)

> **Landed November 2026** — see the phase 3.4 implementation notes at the
> top.  Landed in its own commit, deliberately isolated from 3.3 so the
> custom theme can be reverted with a single `git revert` if the palette
> doesn't land well.

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
| 3 | Screen layout unification + StepChecklist / ActionBar widget extraction | done |
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
