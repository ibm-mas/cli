#!/usr/bin/env python3
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Update copyright headers in Python files to reflect creation and modification years.

This script scans Python files and ensures copyright headers follow the format:
- Single year if created and last modified in same year: "# Copyright (c) 2024 IBM Corporation..."
- Year range if different: "# Copyright (c) 2024, 2026 IBM Corporation..."
"""

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

COPYRIGHT_PATTERN = re.compile(r"^# Copyright \(c\) (\d{4}(?:, \d{4})?)(?: IBM Corporation and other Contributors\.)?")
COPYRIGHT_TEMPLATE = "# Copyright (c) {year} IBM Corporation and other Contributors."


def getGitCreationYear(filePath: Path) -> Optional[int]:
    """Get the year a file was first committed to git.

    Args:
        filePath (Path): Path to the file

    Returns:
        Optional[int]: Year of first commit, or None if not in git
    """
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aI", "--reverse", str(filePath)], capture_output=True, text=True, check=True, cwd=filePath.parent
        )
        if result.stdout.strip():
            firstCommitDate = result.stdout.strip().split("\n")[0]
            return int(firstCommitDate[:4])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass
    return None


def getGitModificationYear(filePath: Path) -> Optional[int]:
    """Get the year a file was last modified in git.

    Args:
        filePath (Path): Path to the file

    Returns:
        Optional[int]: Year of last commit, or None if not in git
    """
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aI", "-1", str(filePath)], capture_output=True, text=True, check=True, cwd=filePath.parent
        )
        if result.stdout.strip():
            lastCommitDate = result.stdout.strip()
            return int(lastCommitDate[:4])
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


def getFileYears(filePath: Path) -> Tuple[Optional[int], Optional[int]]:
    """Get creation and modification years for a file.

    Args:
        filePath (Path): Path to the file

    Returns:
        Tuple[Optional[int], Optional[int]]: (creation_year, modification_year)
    """
    creationYear = getGitCreationYear(filePath)
    modificationYear = getGitModificationYear(filePath)
    return creationYear, modificationYear


def formatYearString(creationYear: int, modificationYear: int) -> str:
    """Format year string for copyright header.

    Args:
        creationYear (int): Year file was created
        modificationYear (int): Year file was last modified

    Returns:
        str: Formatted year string (e.g., "2024" or "2024, 2026")
    """
    if creationYear == modificationYear:
        return str(creationYear)
    return f"{creationYear}, {modificationYear}"


def parseCopyrightLine(line: str) -> Optional[str]:
    """Extract year string from copyright line.

    Args:
        line (str): Copyright header line

    Returns:
        Optional[str]: Year string (e.g., "2024" or "2024, 2026"), or None if not found
    """
    match = COPYRIGHT_PATTERN.match(line)
    if match:
        return match.group(1)
    return None


def findCopyrightLine(filePath: Path) -> Tuple[Optional[int], Optional[str]]:
    """Find copyright line in file.

    Args:
        filePath (Path): Path to the file

    Returns:
        Tuple[Optional[int], Optional[str]]: (line_number, year_string) or (None, None)
    """
    try:
        with open(filePath, "r", encoding="utf-8") as f:
            for lineNum, line in enumerate(f, 1):
                yearString = parseCopyrightLine(line.strip())
                if yearString:
                    return lineNum, yearString
                # Stop searching after first 20 lines
                if lineNum > 20:
                    break
    except Exception as e:
        print(f"Error reading {filePath}: {e}")
    return None, None


def updateCopyrightHeader(filePath: Path, lineNum: int, newYearString: str, dryRun: bool = False) -> bool:
    """Update copyright header in file.

    Args:
        filePath (Path): Path to the file
        lineNum (int): Line number of copyright header (1-based)
        newYearString (str): New year string to use
        dryRun (bool): If True, don't actually modify the file

    Returns:
        bool: True if file was updated (or would be in dry-run mode)
    """
    if dryRun:
        return True

    try:
        with open(filePath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        newCopyrightLine = COPYRIGHT_TEMPLATE.format(year=newYearString) + "\n"
        lines[lineNum - 1] = newCopyrightLine

        with open(filePath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error updating {filePath}: {e}")
        return False


def findPythonFiles(rootDir: Path) -> list[Path]:
    """Find all Python files in directory tree.

    Args:
        rootDir (Path): Root directory to search

    Returns:
        list[Path]: List of Python file paths
    """
    pythonFiles = []
    for root, dirs, files in os.walk(rootDir):
        # Skip hidden directories and common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules"]]

        for file in files:
            if file.endswith(".py"):
                pythonFiles.append(Path(root) / file)

    return sorted(pythonFiles)


def processFile(filePath: Path, dryRun: bool = False) -> dict:
    """Process a single Python file.

    Args:
        filePath (Path): Path to the file
        dryRun (bool): If True, don't actually modify files

    Returns:
        dict: Result dictionary with status and details
    """
    result = {"path": filePath, "status": "ok", "message": None, "old_year": None, "new_year": None}

    # Find copyright line
    lineNum, currentYearString = findCopyrightLine(filePath)

    if lineNum is None:
        result["status"] = "missing"
        result["message"] = "No copyright header found"
        return result

    # Get git years
    creationYear, modificationYear = getFileYears(filePath)

    if creationYear is None or modificationYear is None:
        result["status"] = "no_git"
        result["message"] = "Cannot determine git history"
        return result

    # Calculate expected year string
    expectedYearString = formatYearString(creationYear, modificationYear)

    if currentYearString != expectedYearString:
        result["status"] = "updated"
        result["old_year"] = currentYearString
        result["new_year"] = expectedYearString
        result["message"] = f"Updated: {currentYearString} -> {expectedYearString}"

        if not dryRun:
            if not updateCopyrightHeader(filePath, lineNum, expectedYearString, dryRun):
                result["status"] = "error"
                result["message"] = "Failed to update file"

    return result


def main():
    """Main entry point for copyright header update script."""
    parser = argparse.ArgumentParser(description="Update copyright headers in Python files based on git history")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument("path", nargs="?", default=".", help="Root directory to scan for Python files (default: current directory)")

    args = parser.parse_args()
    rootPath = Path(args.path).resolve()

    if not rootPath.exists():
        print(f"Error: Path does not exist: {rootPath}")
        return 1

    print(f"Scanning for Python files in: {rootPath}")
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    pythonFiles = findPythonFiles(rootPath)
    print(f"Found {len(pythonFiles)} Python files\n")

    # Track results
    updated = []
    missing = []
    noGit = []
    errors = []

    for filePath in pythonFiles:
        result = processFile(filePath, args.dry_run)

        if result["status"] == "updated":
            updated.append(result)
            relPath = filePath.relative_to(rootPath)
            print(f"- {relPath} ({result['old_year']} -> {result['new_year']})")
        elif result["status"] == "missing":
            missing.append(result)
        elif result["status"] == "no_git":
            noGit.append(result)
        elif result["status"] == "error":
            errors.append(result)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files scanned: {len(pythonFiles)}")
    print(f"Files updated: {len(updated)}")
    print(f"Files missing copyright: {len(missing)}")
    print(f"Files without git history: {len(noGit)}")
    print(f"Errors: {len(errors)}")

    if missing:
        print("\n" + "-" * 70)
        print("FILES MISSING COPYRIGHT HEADER:")
        print("-" * 70)
        for result in missing:
            relPath = result["path"].relative_to(rootPath)
            print(f"  {relPath}")

    if noGit:
        print("\n" + "-" * 70)
        print("FILES WITHOUT GIT HISTORY:")
        print("-" * 70)
        for result in noGit:
            relPath = result["path"].relative_to(rootPath)
            print(f"  {relPath}")

    if errors:
        print("\n" + "-" * 70)
        print("ERRORS:")
        print("-" * 70)
        for result in errors:
            relPath = result["path"].relative_to(rootPath)
            print(f"  {relPath}: {result['message']}")

    return 0


if __name__ == "__main__":
    exit(main())
