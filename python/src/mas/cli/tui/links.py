# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Rich text helper for ctrl+clickable terminal hyperlinks.

Textual renders Rich ``link`` styles as OSC 8 terminal hyperlinks, so a
URL stylized this way opens in full via ctrl+click even when the text
folds across lines inside a width-capped panel (a folded plain-text URL
would otherwise only select the line fragment under the cursor).
"""

from rich.text import Text


def linkText(url: str, prefix: str = "") -> Text:
    """Return ``prefix + url`` as Rich text with the URL hyperlinked.

    Args:
        url (str): URL to hyperlink.
        prefix (str, optional): Leading plain text shown before the URL.

    Returns:
        Text: Rich text whose URL portion carries an OSC 8 link style.
    """
    text = Text(f"{prefix}{url}")
    text.stylize(f"link {url}", len(prefix))
    return text
