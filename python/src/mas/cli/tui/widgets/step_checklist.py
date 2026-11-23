# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Step-list widget tracking items through pending / active / done / error states.

Extracted (phase 3.2 of the visual polish plan) from the AutoRunScreen and
LaunchScreen duplicate implementations: both screens rendered the same
ListView of ``○``-prefixed labels and toggled the same ``step-*`` CSS
classes as their checks progressed.  The widget owns that machinery; the
screens keep only the behaviour that genuinely differs between them via the
``on_done`` hook (completion side effects) and by calling the marking
primitives from their own error handling.
"""

from typing import Callable, List, Optional

from textual.widgets import Label, ListItem, ListView

# Monochrome state glyphs — the step-* CSS classes provide the colour, so
# the glyphs only need to differ by shape.  Coloured emoji are avoided:
# they ignore CSS colours and render inconsistently across terminals.
GLYPH_PENDING = "○"
GLYPH_ACTIVE = "◐"
GLYPH_DONE = "✓"
GLYPH_ERROR = "✗"


def pending_label(label: str) -> str:
    """Return the pending-state display text for a step-list item.

    Args:
        label (str): Plain step label.

    Returns:
        str: Label prefixed with the pending glyph.
    """
    return f"{GLYPH_PENDING} {label}"


def label_to_id(label: str) -> str:
    """Convert a human-readable label to a CSS-safe identifier fragment.

    Replaces spaces and special characters with hyphens and lowercases the
    result so it is safe to use as a DOM id suffix.

    Args:
        label (str): Human-readable step label.

    Returns:
        str: CSS-safe id fragment.
    """
    return "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")


class StepChecklist(ListView):
    """ListView of workflow steps that transitions items through states.

    Items are shown upfront with the pending glyph and the ``step-skipped``
    class; ``mark_active`` / ``mark_done`` swap the glyph text and the
    ``step-active`` / ``step-completed`` / ``step-error`` classes as the
    work progresses.  A label that was not pre-populated (e.g. a pipeline
    stage only evaluated at runtime) is appended on first sight.

    Attributes:
        _labels: Ordered labels known to the checklist, including any
            dynamically appended ones.
        _item_prefix: Prefix for the generated ListItem ids (e.g.
            ``dep-step-``), kept stable for CSS and tests.
        _on_done: Optional completion hook (see __init__).
    """

    def __init__(
        self,
        labels: List[str],
        item_prefix: str,
        *,
        on_done: Optional[Callable[[str, bool, str], Optional[str]]] = None,
        **kwargs,
    ) -> None:
        """Initialise the checklist.

        Args:
            labels (list[str]): Step labels shown upfront, in order.
            item_prefix (str): Prefix for the generated ListItem ids (e.g.
                ``dep-step-``); pilot tests query the resulting ids.
            on_done (Callable, optional): ``(label, ok, detail) -> text | None``
                hook invoked by mark_done.  Returning a string overrides the
                item text (the launch screen shows only the step name for
                "Submit PipelineRun" and renders the URL elsewhere);
                returning None keeps the default ``"<glyph> <label>: <detail>"``
                text.  Defaults to None.
            **kwargs: Forwarded to ListView (id, classes, ...).  The shared
                ``.step-checklist`` class is always applied.
        """
        # The shared .step-checklist class is part of the widget contract
        # (highlight-stripping) — merged with any caller-provided classes.
        merged = " ".join(c for c in ("step-checklist", kwargs.pop("classes", "")) if c)
        super().__init__(classes=merged, **kwargs)
        self._labels: List[str] = list(labels)
        self._item_prefix = item_prefix
        self._on_done = on_done

    @property
    def labels(self) -> List[str]:
        """The labels known to the checklist, including dynamically appended ones."""
        return list(self._labels)

    def compose(self):
        """Yield one pending-state ListItem per known label."""
        for label in self._labels:
            yield ListItem(Label(pending_label(label)), id=self._item_id(label), classes="step-skipped")

    def _item_id(self, label: str) -> str:
        """Return the DOM id for a label's ListItem.

        Args:
            label (str): Human-readable step label.

        Returns:
            str: Prefixed, CSS-safe id (without the leading ``#``).
        """
        return f"{self._item_prefix}{label_to_id(label)}"

    def _find_item(self, label: str) -> Optional[ListItem]:
        """Return the ListItem for a label, or None when it is not in the list.

        Args:
            label (str): Human-readable step label.

        Returns:
            Optional[ListItem]: The matching item, or None.
        """
        try:
            return self.query_one(f"#{self._item_id(label)}", ListItem)
        except Exception:
            return None

    def mark_active(self, label: str) -> None:
        """Mark the item for a label as in-progress (active).

        A label that is not in the pre-populated list (e.g. a launch stage
        evaluated at runtime) is appended before being marked.

        Args:
            label (str): Human-readable step label.
        """
        item = self._find_item(label)
        if item is None:
            item = ListItem(Label(pending_label(label)), id=self._item_id(label), classes="step-skipped")
            self.append(item)
            self._labels.append(label)
        item.remove_class("step-skipped", "step-completed", "step-error")
        item.add_class("step-active")
        item.query_one(Label).update(f"{GLYPH_ACTIVE} {label}")

    def mark_done(self, label: str, ok: bool, detail: str) -> None:
        """Mark the item for a label as completed (ok) or failed (not ok).

        The item text becomes ``"<glyph> <label>: <detail>"`` unless the
        ``on_done`` hook returns an override string.  A label with no item
        is ignored (callers always mark_active first in practice).

        Args:
            label (str): Human-readable step label.
            ok (bool): True for success, False for failure.
            detail (str): Short result text from the check.
        """
        item = self._find_item(label)
        if item is None:
            return
        icon = GLYPH_DONE if ok else GLYPH_ERROR
        item.remove_class("step-active", "step-skipped")
        item.add_class("step-completed" if ok else "step-error")
        text = None
        if self._on_done is not None:
            text = self._on_done(label, ok, detail)
        item.query_one(Label).update(text if text is not None else f"{icon} {label}: {detail}")

    def mark_error_first_pending(self, message: str) -> None:
        """Mark the first still-pending or in-progress item as failed.

        Used when a failure cannot be attributed to a single check (an
        unexpected exception aborts the run): the first item that has not
        completed yet carries the error, so the user sees where the run
        stopped.

        Args:
            message (str): Error message shown on the marked item.
        """
        for label in self._labels:
            item = self._find_item(label)
            if item is None:
                continue
            if "step-active" in item.classes or "step-skipped" in item.classes:
                item.remove_class("step-active", "step-skipped")
                item.add_class("step-error")
                item.query_one(Label).update(f"{GLYPH_ERROR} {label}: {message}")
                break
