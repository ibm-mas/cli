"""Web viewer generation for must-gather output.

This module provides functionality to generate a self-contained web viewer
for must-gather output, including manifest generation and template copying.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generateManifest(outputDir: str) -> Dict[str, Any]:
    """Generate manifest.json with file tree structure and metadata.

    Walks the output directory tree and builds a nested structure representing
    all files and directories. Excludes binary files and includes metadata
    about the collection.

    Args:
        outputDir (str): Path to the must-gather output directory

    Returns:
        Dict[str, Any]: Manifest dictionary containing file tree and metadata

    Raises:
        OSError: If directory cannot be read or manifest cannot be written
    """
    logger.info(f"Generating manifest for {outputDir}")

    outputPath = Path(outputDir)
    if not outputPath.exists():
        raise OSError(f"Output directory does not exist: {outputDir}")

    manifest = {"version": "1.0", "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "files": {}}

    # Add cluster metadata if available
    clusterInfoPath = outputPath / "resources" / "_cluster" / "clusterversions.md"
    if clusterInfoPath.exists():
        try:
            with open(clusterInfoPath, "r", encoding="utf-8") as f:
                f.read()  # Read to verify file is accessible
                # Extract cluster version from markdown if possible
                manifest["cluster"] = {"info_available": True}
        except Exception as e:
            logger.warning(f"Could not read cluster info: {e}")

    # Build file tree
    manifest["files"] = _buildFileTree(outputPath, outputPath)

    return manifest


def _buildFileTree(basePath: Path, currentPath: Path) -> Dict[str, Any]:
    """Recursively build file tree structure.

    Args:
        basePath (Path): Base output directory path
        currentPath (Path): Current directory being processed

    Returns:
        Dict[str, Any]: Nested dictionary representing file tree
    """
    tree = {}

    try:
        items = sorted(currentPath.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        logger.warning(f"Permission denied reading directory: {currentPath}")
        return tree

    for item in items:
        # Skip hidden files and the manifest/viewer files themselves
        if item.name.startswith(".") or item.name in ["manifest.json", "index.html"]:
            continue

        relativePath = item.relative_to(basePath)

        if item.is_dir():
            children = _buildFileTree(basePath, item)
            if children:  # Only include non-empty directories
                tree[item.name] = {"type": "directory", "children": children}
        else:
            # Skip binary files
            if _isBinaryFile(item):
                continue

            tree[item.name] = {"type": "file", "path": str(relativePath).replace("\\", "/"), "size": item.stat().st_size}

    return tree


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


# Made with Bob
