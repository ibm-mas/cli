#!/usr/bin/env python3
"""
Update catalog documentation files to use the :::mas-catalog-ocp-compatibility-matrix directive.

This script replaces hardcoded OCP compatibility matrix tables with the dynamic directive,
but only for catalogs from v9-250109 onwards (older catalogs don't have OCP compatibility
metadata in python-devops).

Usage:
    python scripts/update_catalog_ocp_matrix.py
"""

import re
from pathlib import Path


def parse_catalog_version(filename):
    """
    Parse catalog version from filename.

    Args:
        filename: Catalog filename (e.g., "v9-250109-amd64.md")

    Returns:
        tuple: (major_version, date_code) or None if parsing fails
        Example: "v9-250109-amd64.md" -> (9, 250109)
    """
    match = re.match(r"v(\d+)-(\d+)-", filename)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def should_update_catalog(filename):
    """
    Determine if a catalog should be updated based on version.

    Only catalogs from v9-250109 onwards have OCP compatibility metadata.

    Args:
        filename: Catalog filename

    Returns:
        bool: True if catalog should be updated
    """
    version = parse_catalog_version(filename)
    if not version:
        return False

    major, date = version

    # Only v9 catalogs from 250109 onwards
    if major == 9 and date >= 250109:
        return True

    # Future major versions (v10+) should also be updated
    if major > 9:
        return True

    return False


def update_catalog_file(file_path):
    """
    Update a single catalog file to use the OCP matrix directive.

    Args:
        file_path: Path to the catalog markdown file

    Returns:
        tuple: (lines_removed, success)
    """
    with open(file_path, "r", newline="") as f:
        content = f.read()

    original_lines = len(content.splitlines())

    # Pattern to match the OCP compatibility matrix table
    # Matches from the opening <table> tag through the closing </table> tag
    ocp_matrix_pattern = r'<table class="compatabilityMatrix">.*?</table>'

    # Check if the file has an OCP matrix table
    if not re.search(ocp_matrix_pattern, content, re.DOTALL):
        print(f"  WARNING: No OCP matrix table found in {file_path.name}")
        return (0, False)

    # Check if directive already exists
    if ":::mas-catalog-ocp-compatibility-matrix" in content:
        print(f"  INFO: Directive already exists in {file_path.name}")
        return (0, False)

    # Replace the OCP matrix table with the directive
    updated_content = re.sub(
        ocp_matrix_pattern,
        ":::mas-catalog-ocp-compatibility-matrix",
        content,
        flags=re.DOTALL,
    )

    # Write the updated content back
    with open(file_path, "w", newline="") as f:
        f.write(updated_content)

    updated_lines = len(updated_content.splitlines())
    lines_removed = original_lines - updated_lines

    print(f"  SUCCESS: Updated {file_path.name} (removed {lines_removed} lines)")
    return (lines_removed, True)


def main():
    """Main function to update all eligible catalog files."""
    # Get the docs/catalogs directory
    script_dir = Path(__file__).parent
    catalogs_dir = script_dir.parent / "docs" / "catalogs"

    if not catalogs_dir.exists():
        print(f"ERROR: Catalogs directory not found: {catalogs_dir}")
        return

    print("Scanning for catalog files to update...")
    print(f"   Looking in: {catalogs_dir}")
    print()

    # Find all catalog markdown files
    catalog_files = sorted(catalogs_dir.glob("v*.md"))

    if not catalog_files:
        print("ERROR: No catalog files found")
        return

    print(f"Found {len(catalog_files)} catalog files")
    print()

    # Filter to only catalogs that should be updated
    eligible_files = [f for f in catalog_files if should_update_catalog(f.name)]

    print(f"{len(eligible_files)} catalogs eligible for update (v9-250109 and newer)")
    print()

    if not eligible_files:
        print("INFO: No eligible catalogs to update")
        return

    # Update each eligible file
    total_lines_removed = 0
    files_updated = 0

    for file_path in eligible_files:
        lines_removed, success = update_catalog_file(file_path)
        total_lines_removed += lines_removed
        if success:
            files_updated += 1

    print()
    print("=" * 70)
    print("Summary:")
    print(f"   Files updated: {files_updated}/{len(eligible_files)}")
    print(f"   Total lines removed: {total_lines_removed}")
    print("=" * 70)

    if files_updated > 0:
        print()
        print("SUCCESS: Update complete!")
        print()
        print("Next steps:")
        print("1. Review the changes with: git diff docs/catalogs/")
        print("2. Test the documentation build: mkdocs serve")
        print("3. Commit the changes if everything looks good")
    else:
        print()
        print("INFO: No files were updated")


if __name__ == "__main__":
    main()

# Made with Bob
