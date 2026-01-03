#!/usr/bin/env python3
"""
Script to replace hardcoded Details tables in catalog documentation
with the :::mas-catalog-details directive.
"""

import re
from pathlib import Path


def update_catalog_file(file_path):
    """Replace hardcoded Details table with directive."""
    # Read with newline='' to preserve original line endings
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    # Pattern to match the Details section with the table
    # Matches from "Details" header through the closing </table> tag
    pattern = r"Details\s*\n-+\s*\n\s*<table>.*?</table>"

    # Check if file has the old format
    if not re.search(pattern, content, re.DOTALL):
        return False, "No Details table found"

    # Replace with the directive
    new_content = re.sub(pattern, ":::mas-catalog-details", content, flags=re.DOTALL)

    # Write back with newline='' to preserve original line endings
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)

    return True, "Updated successfully"


def main():
    """Process all catalog markdown files."""
    catalog_dir = Path("docs/catalogs")

    # Find all .md files except index.md
    catalog_files = [f for f in catalog_dir.glob("*.md") if f.name != "index.md"]

    updated_count = 0
    skipped_count = 0

    print(f"Found {len(catalog_files)} catalog files to process\n")

    for file_path in sorted(catalog_files):
        success, message = update_catalog_file(file_path)

        if success:
            print(f"[OK] {file_path.name}: {message}")
            updated_count += 1
        else:
            print(f"[SKIP] {file_path.name}: {message}")
            skipped_count += 1

    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total:   {len(catalog_files)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

# Made with Bob
