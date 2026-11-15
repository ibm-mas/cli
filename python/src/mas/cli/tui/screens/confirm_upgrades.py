# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Conditional step screen collecting interactive upgrade confirmations.

Rendered between the dependency-checks and review steps when the detected
dependencies require an explicit confirmation before the update can proceed:

- MongoDB Community major-version update (with backup recommendation notice)
- IBM Db2 major-version update
- Db2 v11 to v12 activation license file path

The step is only shown when ``UpdateApp.upgradeConfirmationsPending()`` is
True; otherwise the workflow skips straight to review.
"""

from typing import Any

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Checkbox, Input, Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep


class ConfirmUpgradesScreen(VerticalScroll):
    """Content panel collecting the interactive upgrade confirmations.

    Composed lazily when the step becomes active (after the dependency checks
    have run), so the pending-confirmation state read from the app instance
    is current.  The Confirm button is blocked until every required
    confirmation is checked and (for Db2 v11 to v12) a license file path is
    provided.  Confirm writes the corresponding params and posts
    StepCompleted; Abort exits the application.

    Attributes:
        _mas_app: MAS CLI app instance (UpdateApp).
        _step: The confirm-upgrades WorkflowStep.
        _step_index: Zero-based position in the definition.
    """

    def __init__(self, mas_app: Any, step: WorkflowStep, step_index: int) -> None:
        """Initialise the confirm upgrades screen.

        Args:
            mas_app: MAS CLI app instance with upgradeConfirmationsPending()
                and the pending-state helpers.
            step (WorkflowStep): The confirm-upgrades WorkflowStep.
            step_index (int): Zero-based index in the workflow definition.
        """
        super().__init__(id=f"step-panel-{step.id}")
        self._mas_app = mas_app
        self._step = step
        self._step_index = step_index

    def compose(self) -> ComposeResult:
        """Build the confirmation sections for each pending upgrade.

        Yields:
            Heading, description, one section per pending confirmation
            (MongoDB notice + checkbox, Db2 checkbox, Db2 license path input),
            an error label, and Confirm / Abort buttons.
        """
        yield Label(self._step.heading, id=f"heading-{self._step.id}")
        for para in self._step.description:
            yield Label(para, classes="description-para")

        if self._mas_app.mongoUpgradeConfirmationPending():
            target = self._mas_app.mongoTargetVersion
            current = self._mas_app.mongoCurrentVersion or "(current)"
            with Vertical(id="confirm-mongodb-section", classes="confirm-section"):
                yield Label("MongoDB Community Edition", classes="confirm-section-heading")
                yield Label(
                    f"MongoDB Community Edition is currently running version {current} and will be updated to {target}",
                    classes="confirm-section-para",
                )
                yield Label(
                    "It is recommended that you backup your MongoDB instance before proceeding:\n"
                    "https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=suite-backing-up-mongodb-maximo-application",
                    classes="confirm-section-para",
                )
                yield Checkbox(
                    f"Confirm update to MongoDB {target}",
                    id="confirm-mongodb",
                    classes="confirm-checkbox",
                )

        if self._mas_app.db2UpgradeConfirmationPending():
            current = self._mas_app.db2CurrentMajorVersion
            target = self._mas_app.db2TargetMajorVersion
            with Vertical(id="confirm-db2-section", classes="confirm-section"):
                yield Label("IBM Db2", classes="confirm-section-heading")
                yield Label(
                    f"Db2 {current} instances in {self._mas_app.getParam('db2_namespace')} will be updated to {target}",
                    classes="confirm-section-para",
                )
                yield Checkbox(
                    f"Confirm update from Db2 {current} to {target}",
                    id="confirm-db2",
                    classes="confirm-checkbox",
                )

        if self._mas_app.db2LicenseFileNeeded():
            with Vertical(id="db2-license-section", classes="confirm-section"):
                yield Label("Db2 v12 Activation License File", classes="confirm-section-heading")
                yield Label(
                    "Db2 v11 to v12 upgrades require a valid Db2 v12 activation license file.\n"
                    "If you cannot provide a valid file, the update must be aborted.",
                    classes="confirm-section-para",
                )
                yield Label("Path to a valid Db2 v12 license file", classes="field-label")
                yield Input(placeholder="/path/to/db2/license/file", id="input-db2-license")

        yield Label("", id=f"validator-error-{self._step.id}", classes="validator-error")
        with Horizontal(id="confirm-buttons"):
            yield Button("✓ Confirm & Continue", id="btn-confirm-upgrades", variant="success")
            yield Button("✕ Abort Update", id="btn-abort-upgrades", variant="error")

    def start_dynamic_loaders(self) -> None:
        """No-op — satisfies the interface expected by TextualShell."""

    def _requiredChecked(self) -> bool:
        """Return True when every required confirmation checkbox is checked.

        Returns:
            bool: True when the MongoDB and Db2 confirmations (as applicable)
                are checked.
        """
        if self._mas_app.mongoUpgradeConfirmationPending():
            try:
                if not self.query_one("#confirm-mongodb", Checkbox).value:
                    return False
            except Exception:
                return False
        if self._mas_app.db2UpgradeConfirmationPending():
            try:
                if not self.query_one("#confirm-db2", Checkbox).value:
                    return False
            except Exception:
                return False
        return True

    def _licenseProvided(self) -> bool:
        """Return True when a license path is entered or not needed.

        Returns:
            bool: True when the Db2 v11 to v12 license input is non-empty
                (whitespace-trimmed), or no license file is needed.
        """
        if not self._mas_app.db2LicenseFileNeeded():
            return True
        try:
            return bool(self.query_one("#input-db2-license", Input).value.strip())
        except Exception:
            return False

    def _writeConfirmations(self) -> None:
        """Write the confirmed upgrade params and license file path to the app."""
        if self._mas_app.mongoUpgradeConfirmationPending():
            targetMajor = self._mas_app.mongoTargetVersion.split(".")[0]
            self._mas_app.setParam(f"mongodb_v{targetMajor}_upgrade", "true")
        if self._mas_app.db2UpgradeConfirmationPending():
            targetMajor = self._mas_app.db2TargetMajorVersion
            self._mas_app.setParam(f"db2_v{targetMajor}_upgrade", "true")
        if self._mas_app.db2LicenseFileNeeded():
            licensePath = self.query_one("#input-db2-license", Input).value.strip()
            self._mas_app.db2LicenseFileLocal = licensePath

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        """Clear the inline error when a confirmation checkbox changes.

        Args:
            _event (Checkbox.Changed): The checkbox change event (unused).
        """
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update("")
        error_label.remove_class("validator-error--visible")

    def on_input_changed(self, _event: Input.Changed) -> None:
        """Clear the inline error when the license path input changes.

        Args:
            _event (Input.Changed): The input change event (unused).
        """
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update("")
        error_label.remove_class("validator-error--visible")

    def reset(self) -> None:
        """Clear checkbox and input state for a workflow reset."""
        for checkbox_id in ("#confirm-mongodb", "#confirm-db2"):
            try:
                self.query_one(checkbox_id, Checkbox).value = False
            except Exception:
                pass
        try:
            self.query_one("#input-db2-license", Input).value = ""
        except Exception:
            pass
        try:
            error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
            error_label.update("")
            error_label.remove_class("validator-error--visible")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Confirm and Abort buttons.

        Confirm is blocked with an inline error until every required
        confirmation is checked and the license path (when needed) is
        provided.  Abort exits the application.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-confirm-upgrades":
            if not self._requiredChecked():
                error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
                error_label.update("All upgrade confirmations must be checked before you can continue.")
                error_label.add_class("validator-error--visible")
                return
            if not self._licenseProvided():
                error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
                error_label.update("A path to a valid Db2 v12 license file is required.")
                error_label.add_class("validator-error--visible")
                return
            self._writeConfirmations()
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-abort-upgrades":
            self.app.exit(1)
