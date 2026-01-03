#!/usr/bin/env python3
"""
Script to replace Manual Installation and Source sections in catalog documentation
with the new directives.
"""

import re
from pathlib import Path


def update_catalog_file(file_path):
    """Replace Manual Installation and Source sections with directives."""
    # Read with newline='' to preserve original line endings
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    changes_made = []

    # Pattern 1: Manual Installation section
    # Matches from "Manual Installation" header through the oc apply command
    install_pattern = r"Manual Installation\s*\n-+\s*\n`oc apply -f https://raw\.githubusercontent\.com/ibm-mas/cli/master/catalogs/[^`]+`"

    if re.search(install_pattern, content):
        content = re.sub(install_pattern, ":::mas-catalog-install", content)
        changes_made.append("Manual Installation")

    # Pattern 2: Source section
    # Matches from "Source" header through the closing ``` of the YAML block
    source_pattern = r"Source\s*\n-+\s*\n```yaml\s*\napiVersion: operators\.coreos\.com/v1alpha1.*?```"

    if re.search(source_pattern, content, re.DOTALL):
        content = re.sub(
            source_pattern, ":::mas-catalog-source", content, flags=re.DOTALL
        )
        changes_made.append("Source")

    if not changes_made:
        return False, "No sections found to replace"

    # Write back with newline='' to preserve original line endings
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

    return True, f"Replaced: {', '.join(changes_made)}"


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
