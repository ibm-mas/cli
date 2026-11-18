# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the TextualShell header / footer chrome tint (phase 3.3 of the visual polish plan).

Covers: the app-level chrome (Header, Footer) rendering with the theme's
$surface tint rather than $background, so the chrome frames the content
instead of disappearing into it.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

from mas.cli.tui.models import WorkflowStep

pytestmark = pytest.mark.tui


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(params: dict = None):
    """Create a minimal mock MAS CLI app with a params dict.

    Args:
        params (dict, optional): Initial params. Defaults to empty dict.

    Returns:
        MagicMock: Mock app instance with .params attribute.
    """
    m = MagicMock()
    m.params = params if params is not None else {}
    return m


# ---------------------------------------------------------------------------
# Header / Footer surface tint
# ---------------------------------------------------------------------------


def test_chrome_uses_surface_tint():
    """Test that the header and footer render with the $surface tint.

    GIVEN the shell running at the pilot default size
    WHEN the header and footer chrome render
    THEN both backgrounds resolve to the theme's $surface variable —
        one subtle step above $background — rather than $background itself,
        so the chrome reads as a frame around the content area.

    The assertion compares against whatever theme is active (the CSS uses
    the $surface variable), so it holds both for the default Textual theme
    and for the custom MAS theme.
    """
    from textual.color import Color
    from textual.widgets import Footer, Header

    from mas.cli.tui.shell import TextualShell

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            variables = shell.get_css_variables()
            surface = Color.parse(variables["surface"])
            background = Color.parse(variables["background"])
            header_bg = shell.query_one(Header).styles.background
            footer_bg = shell.query_one(Footer).styles.background
            return header_bg, footer_bg, surface, background

    header_bg, footer_bg, surface, background = asyncio.run(run())
    assert header_bg == surface
    assert footer_bg == surface
    # The tint must be a real step away from the background, otherwise the
    # rule is a visual no-op.
    assert surface != background
