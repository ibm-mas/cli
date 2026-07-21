# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Type system for the MAS CLI Textual TUI workflow layer.

Defines the pure-data types used to describe a workflow: its steps,
the input fields each step collects, the summary items shown on the review
screen, and the top-level WorkflowDefinition list.  These types are
deliberately free of any Textual dependency so they can be imported and
tested without the optional [tui] extra being installed.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Literal, Optional, Union

FieldType = Literal[
    "string",
    "password",
    "int",
    "bool",
    "select",
    "multi_select",
    "dynamic_select",
    "file",
    "dir",
]
"""Valid field types for a WorkflowField."""


@dataclass
class WorkflowField:
    """A single input field within a workflow step.

    Attributes:
        id: Machine-readable identifier; used as the key in app.params.
        label: Human-readable label shown in the TUI widget.
        type: Widget type (see FieldType literal).
        options: Option list for select / multi_select fields.  May be a
            plain ``List[str]`` or a zero-argument callable that returns one.
            When callable, it is invoked at widget-build time so that the list
            can be populated from app state that was not yet available when the
            WorkflowField was constructed.
        options_loader: Callable for dynamic_select; receives current params
            dict, returns a list of option strings.  Run in a worker thread.
        default: Pre-filled value shown in the widget.
        validator: Optional validator hint (reserved for future use).
        sensitive: When True the value is masked in the review summary.
        required: When True the Next button is blocked while the field is empty.
    """

    id: str
    label: str
    type: FieldType
    options: Optional[Union[List[str], Callable[[], List[str]]]] = None
    options_loader: Optional[Callable] = None
    default: Optional[str] = None
    validator: Optional[str] = None
    sensitive: bool = False
    required: bool = True


@dataclass
class WorkflowSummaryItem:
    """A row in the review-screen summary table.

    Attributes:
        label: Column header / row label shown in the DataTable.
        param: Key in app.params whose value is displayed.  Mutually exclusive
            with ``attr``.
        attr: Name of an instance attribute on the app object to display.
            Use this for values that are app state (e.g. ``installedCatalogId``)
            rather than Tekton pipeline params.  Mutually exclusive with ``param``.
        sensitive: When True the value is replaced with "***" in the table.
    """

    label: str
    param: str = ""
    attr: str = ""
    sensitive: bool = False


@dataclass
class WorkflowStep:
    """A single step in a workflow.

    A step is rendered as one screen in the TUI content area.  Its heading,
    description, and fields are displayed in order.  The optional action is
    run in a worker thread after the step's fields have been confirmed.  The
    optional condition is evaluated with the current params dict before the
    step is shown; when it returns False the step is greyed out and skipped.

    Attributes:
        id: Machine-readable identifier used in the sidebar and for routing.
        heading: Text rendered as the step heading.
        heading_level: "h1" or "h2" — controls the heading CSS class.
        description: List of paragraph strings shown below the heading.
        fields: Input fields collected on this step's screen.
        summary: Items included in the review-screen DataTable for this step.
        action: Optional blocking callable run in a worker thread after the
            step's fields are confirmed.  Receives no arguments; any required
            values should be closed over via the app instance.
        validator: Optional blocking callable run in a worker thread when the
            user presses Next.  Called after params are written.  If it raises,
            the error is shown inline and the step does not advance.  Takes no
            arguments; read required values from the closed-over app instance.
        condition: Optional callable that receives the current params dict and
            returns a bool.  When False the step is skipped.  Always use the
            signature ``lambda p: ...`` (single dict argument).
        screen_class: Optional callable ``(mas_app, step, step_index) -> Widget``
            that overrides the default ``StepScreen`` for this step.  Used by
            specialised steps (e.g. the OCP connection step) that need custom
            internal layout.
    """

    id: str
    heading: str
    heading_level: str = "h1"
    description: List[str] = field(default_factory=list)
    fields: List[WorkflowField] = field(default_factory=list)
    summary: List[WorkflowSummaryItem] = field(default_factory=list)
    action: Optional[Callable] = None
    validator: Optional[Callable] = None
    condition: Optional[Callable[[dict], bool]] = None
    screen_class: Optional[Callable] = None
    screen_kwargs: dict = field(default_factory=dict)
    review_builder: Optional[Callable] = None


WorkflowDefinition = List[WorkflowStep]
"""A complete workflow expressed as an ordered list of WorkflowStep objects."""
