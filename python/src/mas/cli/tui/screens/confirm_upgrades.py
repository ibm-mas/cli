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

The Db2 license path input is rendered inline in the IBM Db2 section: for a
v11 to v12 upgrade, providing the license file path is itself the
confirmation, so no separate Db2 checkbox is shown in that case.  A Db2
checkbox is only rendered for major-version upgrades that do not need a
license file.  The entered path is validated to point at an existing file
before the step can complete, so a typo fails at confirmation time rather
than when the pipeline launch reads the file.

The step is only shown when ``UpdateApp.upgradeConfirmationsPending()`` is
True; otherwise the workflow skips straight to review.
"""

from os import path
from typing import Any, Optional

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import Button, Checkbox, Input, Label
except ModuleNotFoundError as exc:
    raise ImportError("The Textual TUI requires textual to be installed. Install it with: pip install mas-cli[tui]") from exc

from mas.cli.tui.messages import StepCompleted
from mas.cli.tui.models import WorkflowStep


class ConfirmUpgradesScreen(Vertical):
    """Content panel collecting the interactive upgrade confirmations.

    Composed lazily when the step becomes active (after the dependency checks
    have run), so the pending-confirmation state read from the app instance
    is current.  The Confirm button is blocked until every required
    confirmation is satisfied: MongoDB and Db2 checkboxes (where rendered)
    must be checked, and the Db2 v11 to v12 license path (when needed) must
    be provided — for that upgrade, entering the path is the confirmation.
    Confirm writes the corresponding params and posts StepCompleted; Abort
    exits the application.

    The scrollable confirmation sections sit in a ``.content-scroll`` area
    with a fixed ``.action-bar`` pinned below (status row + Confirm/Abort
    buttons), matching every other screen's layout.

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
            A scrollable area with the heading, description and one section
            per pending confirmation (MongoDB notice + checkbox, Db2 section
            with either a checkbox or, for the v11 to v12 license-requiring
            upgrade, an inline license path input), then a fixed action bar
            with the error status row and Confirm / Abort buttons.
        """
        with VerticalScroll(classes="content-scroll"):
            yield Label(self._step.heading, id=f"heading-{self._step.id}", classes="step-heading")
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

            db2UpgradePending = self._mas_app.db2UpgradeConfirmationPending()
            db2LicenseNeeded = self._mas_app.db2LicenseFileNeeded()
            if db2UpgradePending or db2LicenseNeeded:
                current = self._mas_app.db2CurrentMajorVersion
                target = self._mas_app.db2TargetMajorVersion
                namespace = self._mas_app.getParam("db2_namespace")
                with Vertical(id="confirm-db2-section", classes="confirm-section"):
                    yield Label("IBM Db2", classes="confirm-section-heading")
                    if db2LicenseNeeded:
                        # For the v11 to v12 upgrade the license file path input
                        # is the confirmation itself — no separate checkbox.
                        yield Label(
                            f"Db2 {current} instances in {namespace} will be updated to {target}, this update requires a license file",
                            classes="confirm-section-para",
                        )
                        yield Input(placeholder="Path to a valid Db2 v12 license file", id="input-db2-license")
                    else:
                        yield Label(
                            f"Db2 {current} instances in {namespace} will be updated to {target}",
                            classes="confirm-section-para",
                        )
                        yield Checkbox(
                            f"Confirm update from Db2 {current} to {target}",
                            id="confirm-db2",
                            classes="confirm-checkbox",
                        )

        with Vertical(classes="action-bar"):
            yield Label("", id=f"validator-error-{self._step.id}", classes="action-status")
            with Horizontal(classes="action-buttons"):
                yield Button("Confirm & Continue", id="btn-confirm-upgrades", variant="success")
                yield Button("Abort Update", id="btn-abort-upgrades", variant="error")

    def start_dynamic_loaders(self) -> None:
        """No-op — satisfies the interface expected by TextualShell."""

    def _requiredChecked(self) -> bool:
        """Return True when every required confirmation checkbox is checked.

        The Db2 checkbox is only rendered (and therefore only required) for
        major-version upgrades that do not need a license file — for the
        v11 to v12 upgrade, providing the license path is the confirmation.

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
        if self._mas_app.db2UpgradeConfirmationPending() and not self._mas_app.db2LicenseFileNeeded():
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

    def _licensePath(self) -> Optional[str]:
        """Return the license path to store, or None when not needed/empty.

        The entered path is whitespace-trimmed and user-expanded (``~``) so
        that what is stored points at the file the launch path will open.

        Returns:
            Optional[str]: Expanded license path, or None when no license
                file is needed or no path has been entered.
        """
        if not self._mas_app.db2LicenseFileNeeded():
            return None
        try:
            return path.expanduser(self.query_one("#input-db2-license", Input).value.strip())
        except Exception:
            return None

    def _writeConfirmations(self) -> None:
        """Write the confirmed upgrade params and license file path to the app."""
        if self._mas_app.mongoUpgradeConfirmationPending():
            targetMajor = self._mas_app.mongoTargetVersion.split(".")[0]
            self._mas_app.setParam(f"mongodb_v{targetMajor}_upgrade", "true")
        if self._mas_app.db2UpgradeConfirmationPending():
            targetMajor = self._mas_app.db2TargetMajorVersion
            self._mas_app.setParam(f"db2_v{targetMajor}_upgrade", "true")
        licensePath = self._licensePath()
        if licensePath:
            self._mas_app.db2LicenseFileLocal = licensePath

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        """Clear the inline error when a confirmation checkbox changes.

        Args:
            _event (Checkbox.Changed): The checkbox change event (unused).
        """
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update("")
        error_label.remove_class("action-status--error")

    def on_input_changed(self, _event: Input.Changed) -> None:
        """Clear the inline error when the license path input changes.

        Args:
            _event (Input.Changed): The input change event (unused).
        """
        error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
        error_label.update("")
        error_label.remove_class("action-status--error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Confirm and Abort buttons.

        Confirm is blocked with an inline error until every required
        confirmation is satisfied: MongoDB and Db2 checkboxes (where
        rendered) must be checked, and the Db2 v11 to v12 license path
        (when needed) must be entered and point at an existing file — a
        path that only fails when the pipeline launch reads it is caught
        here instead.  Abort exits the application.

        Args:
            event (Button.Pressed): The button press event.
        """
        if event.button.id == "btn-confirm-upgrades":
            if not self._requiredChecked():
                error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
                error_label.update("All upgrade confirmations must be checked before you can continue.")
                error_label.add_class("action-status--error")
                return
            licensePath = self._licensePath()
            if self._mas_app.db2LicenseFileNeeded() and not licensePath:
                error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
                error_label.update("A path to a valid Db2 v12 license file is required.")
                error_label.add_class("action-status--error")
                return
            if licensePath is not None and not path.isfile(licensePath):
                error_label = self.query_one(f"#validator-error-{self._step.id}", Label)
                error_label.update(f"License file not found at {licensePath}")
                error_label.add_class("action-status--error")
                return
            self._writeConfirmations()
            self.post_message(StepCompleted(self._step_index))
        elif event.button.id == "btn-abort-upgrades":
            self.app.exit(1)
