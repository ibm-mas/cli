#!/usr/bin/env python
"""
Unit test to validate catalog editorial content can be parsed as HTML.

This test ensures that all catalog files with editorial content (What's New and Known Issues)
can be successfully rendered as HTML without XML parsing errors.
"""

import sys
import os
import glob
import yaml
import pytest
from prompt_toolkit.formatted_text import HTML

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python-devops', 'src'))


def get_all_catalog_files():
    """Get all catalog YAML files from python-devops."""
    catalog_dir = os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..',
        'python-devops', 'src', 'mas', 'devops', 'data', 'catalogs'
    )
    catalog_files = glob.glob(os.path.join(catalog_dir, 'v*.yaml'))
    return catalog_files


def process_catalog_editorial(catalog_data):
    """
    Process catalog editorial content the same way the CLI does.
    Returns the HTML string that would be passed to the HTML parser.
    """
    summary = []

    editorial = catalog_data.get('editorial')
    if not editorial:
        return None

    # Add What's New section
    if 'whats_new' in editorial and editorial['whats_new']:
        summary.append("")
        summary.append("<u>What's New</u>")
        for item in editorial['whats_new']:
            title = item.get('title', '')
            # Replace **text** with <b>text</b> in title
            title = title.replace('**', '<b>', 1).replace('**', '</b>', 1)
            summary.append(title)
            # Add details if present
            if 'details' in item and item['details']:
                for detail in item['details']:
                    summary.append(f" - {detail}")

    # Add Known Issues section
    if 'known_issues' in editorial and editorial['known_issues']:
        summary.append("")
        summary.append("<u>Known Issues</u>")
        for issue in editorial['known_issues']:
            title = issue.get('title', '')
            summary.append(f"- {title}")

    if not summary:
        return None

    # Wrap in color tags like printDescription does
    DESCRIPTIONCOLOR = 'LightSlateGrey'
    summary.insert(0, "")  # Add empty first line
    summary[0] = f"<{DESCRIPTIONCOLOR}>{summary[0]}"
    summary.append("")  # Add empty last line
    summary[len(summary) - 1] = f"{summary[len(summary) - 1]}</{DESCRIPTIONCOLOR}>"

    return "\n".join(summary)


@pytest.mark.parametrize("catalog_file", get_all_catalog_files())
def test_catalog_editorial_html_parsing(catalog_file):
    """
    Test that catalog editorial content can be parsed as HTML without errors.

    This test validates that:
    1. The catalog YAML can be loaded
    2. If editorial content exists, it can be processed
    3. The resulting HTML can be parsed without XML errors
    """
    catalog_name = os.path.basename(catalog_file)

    # Load the catalog
    with open(catalog_file, 'r', encoding='utf-8') as f:
        catalog_data = yaml.safe_load(f)

    assert catalog_data is not None, f"Failed to load catalog {catalog_name}"

    # Process editorial content
    html_string = process_catalog_editorial(catalog_data)

    if html_string is None:
        # No editorial content, test passes
        pytest.skip(f"Catalog {catalog_name} has no editorial content")
        return

    # Try to parse as HTML - this will raise ExpatError if there are unescaped special characters
    try:
        html_obj = HTML(html_string)
        assert html_obj is not None
    except Exception as e:
        # Provide helpful error message showing the problematic content
        pytest.fail(
            f"Catalog {catalog_name} editorial content failed HTML parsing:\n"
            f"Error: {type(e).__name__}: {e}\n\n"
            f"HTML content:\n{html_string}\n\n"
            f"Hint: Check for unescaped special characters like &, <, > in the editorial text.\n"
            f"These should be escaped as &, <, > in the YAML file."
        )


def test_specific_characters_in_editorial():
    """
    Test that common problematic characters are properly escaped in all catalogs.
    """
    import re

    problematic_patterns = [
        (r'(?<!&)&(?!amp;|lt;|gt;|quot;|apos;|#)', 'unescaped ampersand (&)'),
        (r'<(?![/a-zA-Z])', 'unescaped less-than (<)'),
        (r'(?<![a-zA-Z])>(?![a-zA-Z])', 'unescaped greater-than (>)'),
    ]

    catalog_files = get_all_catalog_files()
    issues_found = []

    for catalog_file in catalog_files:
        catalog_name = os.path.basename(catalog_file)

        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog_data = yaml.safe_load(f)

        editorial = catalog_data.get('editorial')
        if not editorial:
            continue

        # Check What's New
        if 'whats_new' in editorial:
            for idx, item in enumerate(editorial['whats_new']):
                title = item.get('title', '')
                for pattern, desc in problematic_patterns:
                    if re.search(pattern, title):
                        issues_found.append(
                            f"{catalog_name}: What's New item {idx + 1} contains {desc}: {title[:100]}..."
                        )

                if 'details' in item:
                    for detail_idx, detail in enumerate(item['details']):
                        for pattern, desc in problematic_patterns:
                            if re.search(pattern, detail):
                                issues_found.append(
                                    f"{catalog_name}: What's New item {idx + 1}, detail {detail_idx + 1} "
                                    f"contains {desc}: {detail[:100]}..."
                                )

        # Check Known Issues
        if 'known_issues' in editorial:
            for idx, issue in enumerate(editorial['known_issues']):
                title = issue.get('title', '')
                for pattern, desc in problematic_patterns:
                    if re.search(pattern, title):
                        issues_found.append(
                            f"{catalog_name}: Known Issue {idx + 1} contains {desc}: {title[:100]}..."
                        )

    if issues_found:
        pytest.fail(
            f"Found {len(issues_found)} catalog(s) with unescaped special characters:\n"
            "\n".join(issues_found)
        )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
