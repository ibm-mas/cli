# TUI Screen Widgets

Each module in this package provides one focused Textual widget that acts as a
content panel inside `TextualShell`'s `ContentSwitcher`.  All styles live in
[`../styles/app.tcss`](../styles/app.tcss) — no widget carries inline CSS.

---

## `action_overlay.py` — `ActionOverlay`

A **modal overlay** pushed onto the screen stack while a step's blocking
`action` callable runs in a worker thread.

- Shows an indeterminate `ProgressBar` and a `RichLog` for status output.
- On success it dismisses itself and posts `ActionComplete` to `TextualShell`.
- On failure it logs the exception, hides the progress bar, and reveals a
  **Dismiss** button so the user can read the error and recover.

Used by `TextualShell.on_step_completed` when `step.action is not None`.

---

## `connect.py` — `ConnectStepScreen`

Content panel for the **OCP cluster connection** step.  Implements a
two-sub-screen flow inside a `ContentSwitcher`:

| Sub-screen | Shown when |
|---|---|
| **Reuse** (`connect-reuse`) | An active kubeconfig connection is detected.  Displays the console URL and offers **Yes / No** buttons. |
| **New** (`connect-new`) | No active connection exists, or the user clicked **No**.  Collects Server URL, Login Token, and Skip TLS. |

An optional `post_connect` callable (passed via `WorkflowStep.screen_kwargs`)
is called in the same worker thread immediately after a successful connection —
before the workflow advances.  The update workflow uses this to run
`reviewCurrentCatalog()` without a separate `ActionOverlay` flash.

Connection errors are displayed **inline** on the new-credentials sub-screen;
the workflow does not advance until a connection succeeds.

---

## `auto_run.py` — `AutoRunScreen`

A generic **auto-run with progress** panel for any step that follows the
pattern: start work immediately, stream results to a log, reveal Next when done.

- Work starts when `start_dynamic_loaders()` is called by
  `TextualShell._activate_step()` — not on mount, so it only runs once the
  user has completed all preceding steps and params are fully populated.
- Each result is appended to a `RichLog` as `✓ label: detail` or
  `✗ label: detail` via a `progressCallback`.
- The **Next →** button is hidden until work completes (CSS class `dep-ready`
  reveals it).
- `reset()` clears the log and re-hides the button for workflow resets.

Currently used by both `update` and `upgrade` workflows for their
dependency-detection steps, but reusable for any step that calls
`runDependencyChecksWithProgress` on the app instance.

---

## `params_overlay.py` — `ParamsOverlay`

A **debug modal overlay** showing the current `app.params` dict as a sorted
`DataTable`.

- Opened via the `p` key binding on `TextualShell` at any point in the
  workflow.
- Dismisses with **Escape** or the **Close** button.
- The params snapshot is taken at open time; changes made while it is open are
  not reflected until it is reopened.

---

## `review.py` — `ReviewScreen`

The **final review screen** shown after all workflow steps complete.  Split
into two fixed sections:

| Section | Widget | Purpose |
|---|---|---|
| Top (scrollable) | `VerticalScroll` + `Markdown` | Rendered summary of all collected settings |
| Bottom (fixed) | `Vertical` | Review prompt label + action buttons |

The Markdown content is produced by either:
- A **custom `review_builder`** callable `(mas_app) -> str` supplied per
  command (e.g. `buildUpdateReview` in `update/workflow.py`), or
- The **generic fallback** which groups `WorkflowSummaryItem` rows by step
  heading.

Buttons post `WorkflowConfirmed`, `WorkflowReset`, or call `app.exit(1)`.

---

## `step.py` — `StepScreen`

The **generic step content panel** used for any `WorkflowStep` that does not
specify a custom `screen_class`.

Renders in order:
1. Step heading `Label`
2. Description paragraph `Label`s
3. One input widget per `WorkflowField` (see table below)
4. Hidden validator error `Label`
5. **Next →** `Button`

| `WorkflowField.type` | Widget |
|---|---|
| `bool` | `Switch` |
| `select` | `Select` (static options) |
| `multi_select` | `VerticalScroll` of `Checkbox` widgets |
| `dynamic_select` | `LoadingIndicator` replaced by `Select` once options load |
| `password` | `Input` (masked) |
| `int` | `Input` (digits only) |
| `string` / `file` / `dir` | `Input` |

On **Next →**:
1. Required-field validation runs synchronously.
2. All field values are written to `app.params`.
3. If `step.validator` is set it runs in a worker thread; errors are shown
   inline and the button is re-enabled.  On success `StepCompleted` is posted.
4. If no validator, `StepCompleted` is posted directly.

`reset()` clears any validator error and re-enables the button for workflow
resets.
