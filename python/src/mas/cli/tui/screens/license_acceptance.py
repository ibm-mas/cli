# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""Conditional step screen collecting license acceptance.

Rendered after the command-specific selection step when the resolved target
release carries a license that has not been accepted yet (e.g. the upgrade
workflow's license-acceptance step, shown when
``UpgradeApp.licenseAcceptancePending()`` is True).  It is the TUI
equivalent of the classic wizard's license yes/no prompt and of the
``--accept-license`` flag on the non-interactive path.

The step is only shown when the command app reports a pending license; the
command's workflow skips straight to review otherwise.
"""

from typing import Any

try:
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll
    from textual.widgets import Button, Checkbox, Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep
from mas.cli.tui.widgets.action_bar import ActionBar


class LicenseAcceptanceScreen(Vertical):
    """Content panel collecting acceptance of the target release's license.

    Composed lazily when the step becomes active (after the preceding step's
    validator has resolved the target channel), so the license text read
    from the app instance is current.  The Confirm button is blocked with an
    inline error until the acceptance checkbox is checked; Confirm records
    the acceptance on the app instance and posts StepCompleted; Abort exits
    the application.

    The license links and notices sit in a ``.content-scroll`` area with a
    fixed ``.action-bar`` pinned below (status row + Confirm/Abort buttons),
    matching every other screen's layout.

    Attributes:
        _mas_app: MAS CLI app instance (provides ``licenses``,
            ``nextChannel`` and ``licenseAccepted``).
        _step: The license-acceptance WorkflowStep.
        _step_index: Zero-based position in the workflow definition.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the license acceptance screen.

        Args:
            mas_app: MAS CLI app instance with a ``licenses`` dict, a
                resolved ``nextChannel`` and a settable ``licenseAccepted``
                flag.
            step (WorkflowStep): The license-acceptance WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index

    def _licenseLines(self) -> list:
        """Return the license text lines for the target release.

        The ``licenses`` entries are written for prompt_toolkit HTML output
        (URLs wrapped in ``<u>`` tags); the tags are stripped for the Textual
        labels, which render the URLs as plain text.

        Returns:
            list: Non-empty license text lines, or an empty list when the
            target channel carries no license entry.
        """
        raw = self._mas_app.licenses.get(self._mas_app.nextChannel, "")
        return [line.strip().replace("</u>", "").replace("<u>", "") for line in raw.splitlines() if line.strip()]

    def compose(self) -> ComposeResult:
        """Build the screen: heading, description, license text, checkbox.

        Yields:
            A scrollable area (``.content-scroll``) with the heading, the
            step description, one paragraph per license notice/link line,
            and the acceptance checkbox, then a fixed ActionBar
            (``.action-bar``) with the status row and the Confirm / Abort
            buttons.
        """
        with VerticalScroll(classes="content-scroll"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}", classes="step-heading")
            for para in self._step.description:
                yield Label(para, classes="description-para")
            with Vertical(id="license-terms-section", classes="confirm-section"):
                yield Label(f"License terms for MAS {self._mas_app.nextChannel}:", classes="confirm-section-heading")
                for line in self._licenseLines():
                    yield Label(line, classes="confirm-section-para")
            yield Checkbox(
                f"I accept the license terms for MAS {self._mas_app.nextChannel}",
                id="accept-license",
                classes="confirm-checkbox",
            )
        yield ActionBar(
            "",
            status_id=f"validator-error-{self._step.id}",
            buttons=[
                Button("Confirm & Continue", id="btn-confirm-license", variant="success"),
                Button("Abort Upgrade", id="btn-abort-license", variant="error"),
            ],
        )

    def _action_bar(self) -> ActionBar:
        """Return this screen's action bar.

        Returns:
            ActionBar: The pinned status + buttons bar.
        """
        return self.query_one(ActionBar)

    def start_dynamic_loaders(self) -> None:
        """No-op — satisfies the interface expected by TextualShell."""

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        """Clear the inline error when the acceptance checkbox changes.

        Args:
            _event (Checkbox.Changed): The checkbox change event (unused).
        """
        self._action_bar().clear_status()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Confirm and Abort buttons.

        Confirm is blocked with an inline error until the acceptance
        checkbox is checked; it then records the acceptance on the app
        instance (so the command's own launch logic and arg builder see it,
        exactly as ``--accept-license`` would) and posts StepCompleted.
        Abort exits the application.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-confirm-license":
            if not self.query_one("#accept-license", Checkbox).value:
                self._action_bar().set_error("You must accept the license terms before you can continue.")
                return
            self._mas_app.licenseAccepted = True
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-abort-license":
            self.app.exit(1)
