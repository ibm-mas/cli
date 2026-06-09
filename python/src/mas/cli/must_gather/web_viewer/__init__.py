# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Web viewer generation for must-gather output.

This module provides functionality to generate a self-contained web viewer
for must-gather output, including manifest generation and template copying.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


def generateManifest(outputDir: str) -> Dict[str, Any]:
    """Generate split manifest files with per-namespace manifests.

    Creates a root manifest.json with metadata and namespace list, plus
    individual manifest files for each namespace in resources/{namespace}.json.
    This enables lazy loading in the web viewer for better performance.

    Args:
        outputDir (str): Path to the must-gather output directory

    Returns:
        Dict[str, Any]: Root manifest dictionary containing metadata and namespace list

    Raises:
        OSError: If directory cannot be read or manifests cannot be written
    """
    logger.info(f"📦 Generating manifests for {outputDir}")

    outputPath = Path(outputDir)
    if not outputPath.exists():
        raise OSError(f"Output directory does not exist: {outputDir}")

    # Initialize root manifest
    manifest = {"version": "2.0", "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "namespaces": [], "files": {}}

    # Add cluster metadata if available
    clusterInfoPath = outputPath / "resources" / "_cluster" / "clusterversions.md"
    if clusterInfoPath.exists():
        try:
            with open(clusterInfoPath, "r", encoding="utf-8") as f:
                f.read()  # Read to verify file is accessible
                manifest["cluster"] = {"info_available": True}
        except Exception as e:
            logger.warning(f"⚠️ Could not read cluster info: {e}")

    # Identify namespaces in resources directory
    resourcesPath = outputPath / "resources"
    namespaces = []
    if resourcesPath.exists() and resourcesPath.is_dir():
        for item in sorted(resourcesPath.iterdir()):
            if item.is_dir():
                namespaces.append(item.name)

    manifest["namespaces"] = namespaces

    # Build file tree for root level (excluding resources directory)
    manifest["files"] = _buildFileTree(outputPath, outputPath, excludeDirs={"resources"})

    # Generate per-namespace manifests
    for namespace in namespaces:
        _generateNamespaceManifest(outputPath, namespace)

    return manifest


def _buildFileTree(basePath: Path, currentPath: Path, excludeDirs: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Recursively build file tree structure.

    Args:
        basePath (Path): Base output directory path
        currentPath (Path): Current directory being processed
        excludeDirs (Optional[Set[str]], optional): Set of directory names to exclude from tree. Defaults to None.

    Returns:
        Dict[str, Any]: Nested dictionary representing file tree
    """
    if excludeDirs is None:
        excludeDirs = set()

    tree = {}

    try:
        items = sorted(currentPath.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        logger.warning(f"⚠️ Permission denied reading directory: {currentPath}")
        return tree

    for item in items:
        # Skip hidden files and the manifest/viewer files themselves
        if item.name.startswith(".") or item.name in ["manifest.json", "index.html"]:
            continue

        # Skip excluded directories (only at root level)
        if item.is_dir() and currentPath == basePath and item.name in excludeDirs:
            continue

        relativePath = item.relative_to(basePath)

        if item.is_dir():
            children = _buildFileTree(basePath, item, excludeDirs)
            if children:  # Only include non-empty directories
                tree[item.name] = {"type": "directory", "children": children}
        else:
            # Skip binary files
            if _isBinaryFile(item):
                continue

            tree[item.name] = {"type": "file", "path": str(relativePath).replace("\\", "/"), "size": item.stat().st_size}

    return tree


def _generateNamespaceManifest(outputPath: Path, namespace: str) -> None:
    """Generate manifest file for a specific namespace.

    Creates a manifest file at resources/{namespace}.json containing
    the file tree for that namespace only.

    Args:
        outputPath (Path): Base output directory path
        namespace (str): Namespace name

    Raises:
        OSError: If manifest cannot be written
    """
    namespacePath = outputPath / "resources" / namespace
    if not namespacePath.exists():
        logger.warning(f"⚠️ Namespace directory does not exist: {namespacePath}")
        return

    # Build file tree for this namespace
    namespaceManifest = {"namespace": namespace, "files": _buildFileTree(namespacePath, namespacePath)}

    # Write namespace manifest
    manifestPath = outputPath / "resources" / f"{namespace}.json"
    try:
        with open(manifestPath, "w", encoding="utf-8") as f:
            json.dump(namespaceManifest, f, indent=2)
        logger.info(f"✅ Generated manifest: {manifestPath}")
    except Exception as e:
        logger.error(f"❌ Failed to write manifest for {namespace}: {e}")
        raise OSError(f"Failed to write namespace manifest: {e}")


def _isBinaryFile(filePath: Path) -> bool:
    """Check if a file is binary.

    Args:
        filePath (Path): Path to file to check

    Returns:
        bool: True if file appears to be binary, False otherwise
    """
    # Check by extension first
    textExtensions = {".md", ".yaml", ".yml", ".json", ".log", ".txt", ".xml", ".html"}
    if filePath.suffix.lower() in textExtensions:
        return False

    # For files without known extensions, check content
    try:
        with open(filePath, "rb") as f:
            chunk = f.read(1024)
            # Check for null bytes which indicate binary
            return b"\x00" in chunk
    except Exception:
        return True


def writeManifest(outputDir: str, manifest: Dict[str, Any]) -> None:
    """Write manifest to manifest.json file.

    Args:
        outputDir (str): Path to output directory
        manifest (Dict[str, Any]): Manifest dictionary to write

    Raises:
        OSError: If manifest cannot be written
    """
    manifestPath = Path(outputDir) / "manifest.json"
    logger.info(f"Writing manifest to {manifestPath}")

    try:
        with open(manifestPath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        raise OSError(f"Failed to write manifest: {e}")


def copyViewerTemplate(outputDir: str) -> None:
    """Copy viewer.html template to output directory.

    The viewer will fetch manifest.json via HTTP when served.

    Args:
        outputDir (str): Path to output directory

    Raises:
        OSError: If template cannot be found or copied
    """
    # Find template file relative to this module
    templatePath = Path(__file__).parent / "templates" / "viewer.html"

    if not templatePath.exists():
        raise OSError(f"Viewer template not found: {templatePath}")

    targetPath = Path(outputDir) / "index.html"
    logger.info(f"Copying viewer template to {targetPath}")

    try:
        # Simply copy the template without modification
        shutil.copy2(templatePath, targetPath)
    except Exception as e:
        logger.error(f"Failed to copy viewer template: {e}")
        raise OSError(f"Failed to copy viewer template: {e}")


def generateWebViewer(outputDir: str, skipManifest: bool = False) -> bool:
    """Generate complete web viewer for must-gather output.

    This is the main entry point that orchestrates manifest generation
    and template copying. Designed to be called after must-gather collection
    is complete.

    Args:
        outputDir (str): Path to must-gather output directory
        skipManifest (bool, optional): Skip manifest generation if manifest.json exists. Defaults to False.

    Returns:
        bool: True if viewer was generated successfully, False otherwise
    """
    try:
        logger.info("Generating web viewer")

        manifestPath = Path(outputDir) / "manifest.json"

        # Generate manifest only if needed
        if skipManifest and manifestPath.exists():
            logger.info(f"Skipping manifest generation - {manifestPath} already exists")
        else:
            # Generate manifest
            manifest = generateManifest(outputDir)
            # Write manifest.json
            writeManifest(outputDir, manifest)

        # Always copy viewer template (fast operation)
        copyViewerTemplate(outputDir)

        logger.info("Web viewer generated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to generate web viewer: {e}")
        return False
