# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the custom MAS Textual theme (phase 3.4 of the visual polish plan).

Covers: TextualShell registering and selecting the ``mas`` theme, the brand
palette resolving into the app's CSS variables, and the theme definition
specifying semantic colours explicitly (Textual would otherwise derive them
from the primary colour, making state colours indistinguishable).
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


def _color_close(a, b, tolerance: int = 2) -> bool:
    """Return True when two textual Colors are within tolerance per RGB channel.

    Textual generates CSS variables via an HSL round-trip, which can shift
    a channel by one; brand-colour assertions must tolerate that.

    Args:
        a (Color): First colour.
        b (Color): Second colour.
        tolerance (int): Maximum per-channel difference.

    Returns:
        bool: True when every channel differs by at most tolerance.
    """
    return all(abs(x - y) <= tolerance for x, y in zip(a.rgb, b.rgb))


# ---------------------------------------------------------------------------
# Theme registration / selection
# ---------------------------------------------------------------------------


def test_shell_selects_mas_theme():
    """Test that TextualShell registers and selects the custom theme.

    GIVEN a TextualShell with the custom theme module installed
    WHEN the shell runs
    THEN the active theme is ``mas`` and the app's CSS variables resolve
        to the palette defined in tui/theme.py.
    """
    from textual.color import Color

    from mas.cli.tui.shell import TextualShell
    from mas.cli.tui.theme import MAS_THEME

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            variables = shell.get_css_variables()
            return shell.theme, variables

    theme, variables = asyncio.run(run())
    assert theme == "mas"
    # The CSS variables the stylesheet references resolve to the MAS
    # palette (parsed and compared with a per-channel tolerance, since
    # Textual's HSL variable generation can shift a channel by one).
    assert _color_close(Color.parse(variables["primary"]), Color.parse(MAS_THEME.primary))
    assert _color_close(Color.parse(variables["accent"]), Color.parse(MAS_THEME.accent))
    assert _color_close(Color.parse(variables["background"]), Color.parse(MAS_THEME.background))
    assert _color_close(Color.parse(variables["surface"]), Color.parse(MAS_THEME.surface))


def test_chrome_tint_follows_custom_theme():
    """Test that the phase 3.3 chrome tint uses the custom theme's surface.

    GIVEN a TextualShell running under the custom MAS theme
    WHEN the header and footer chrome render
    THEN their backgrounds resolve to the MAS theme's $surface (Gray 90),
        proving the chrome tint rule follows the active theme rather
        than a hard-coded colour.
    """
    from textual.color import Color
    from textual.widgets import Footer, Header

    from mas.cli.tui.shell import TextualShell
    from mas.cli.tui.theme import MAS_THEME

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            header_bg = shell.query_one(Header).styles.background
            footer_bg = shell.query_one(Footer).styles.background
            return header_bg, footer_bg

    header_bg, footer_bg = asyncio.run(run())
    assert header_bg == Color.parse(MAS_THEME.surface)
    assert footer_bg == Color.parse(MAS_THEME.surface)


# ---------------------------------------------------------------------------
# Theme definition invariants
# ---------------------------------------------------------------------------


def test_mas_theme_defines_semantic_colors():
    """Test that the theme sets success/warning/error explicitly.

    GIVEN the MAS theme definition in tui/theme.py
    WHEN its semantic colours are compared against the primary
    THEN each is distinct — Textual derives unspecified theme colours
        from the primary, which would render every state colour blue and
        make the sidebar/checklist state glyphs indistinguishable.
    """
    from mas.cli.tui.theme import MAS_THEME

    primary = MAS_THEME.primary.lower()
    for colour in (MAS_THEME.success, MAS_THEME.warning, MAS_THEME.error):
        assert colour is not None
        assert colour.lower() != primary


def test_mas_theme_is_dark():
    """Test that the theme declares itself dark.

    GIVEN the MAS theme definition in tui/theme.py
    WHEN the theme is inspected
    THEN dark is True, matching the Carbon dark-theme palette the colours
        are drawn from (a light palette would need different tokens).
    """
    from mas.cli.tui.theme import MAS_THEME

    assert MAS_THEME.dark is True


def test_mas_theme_scrollbars_are_neutral():
    """Test that the theme's scrollbar colours are neutral greys.

    GIVEN a TextualShell running under the custom MAS theme
    WHEN the scrollbar CSS variables resolve
    THEN the thumb colours match the theme's neutral palette (Textual's
        defaults derive them from the primary colour, painting every
        scroll thumb the saturated navy that dominated the grey theme)
        and are distinct from the brand primary.
    """
    from textual.color import Color

    from mas.cli.tui.shell import TextualShell
    from mas.cli.tui.theme import MAS_THEME

    definition = [WorkflowStep(id="test-step", heading="Test Step")]

    async def run():
        shell = TextualShell(_make_app(), definition)
        async with shell.run_test() as pilot:
            await pilot.pause()
            return shell.get_css_variables()

    variables = asyncio.run(run())
    primary = Color.parse(MAS_THEME.primary)
    for name in ("scrollbar", "scrollbar-hover", "scrollbar-active"):
        assert name in MAS_THEME.variables
        # The variable reaches the app's CSS (the theme merge worked) and
        # matches the palette defined in tui/theme.py.
        assert _color_close(Color.parse(variables[name]), Color.parse(MAS_THEME.variables[name]))
        # Neutral, not primary-derived navy.
        assert Color.parse(variables[name]) != primary
