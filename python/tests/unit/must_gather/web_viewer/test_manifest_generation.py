"""Unit tests for web viewer manifest generation.

GIVEN a must-gather output directory with namespace subdirectories
WHEN generateManifest() is called
THEN split manifests are created with correct structure.
"""

import json
import tempfile
from pathlib import Path

from mas.cli.must_gather.web_viewer import (
    generateManifest,
    writeManifest,
    _generateNamespaceManifest,
)


def test_generateManifest_creates_v2_structure():
    """Test that generateManifest creates v2.0 manifest structure.

    GIVEN a must-gather directory with resources subdirectories
    WHEN generateManifest() is called
    THEN a v2.0 manifest with namespaces list is returned.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources"
        resourcesPath.mkdir()

        # Create namespace directories
        (resourcesPath / "_cluster").mkdir()
        (resourcesPath / "test-namespace").mkdir()

        # Create some files
        (outputPath / "summary.md").write_text("# Summary")
        (resourcesPath / "_cluster" / "nodes.yaml").write_text("kind: Node")

        # Generate manifest
        manifest = generateManifest(str(outputPath))

        # Verify structure
        assert manifest["version"] == "2.0"
        assert "generated" in manifest
        assert "namespaces" in manifest
        assert "_cluster" in manifest["namespaces"]
        assert "test-namespace" in manifest["namespaces"]
        assert "files" in manifest
        assert "summary.md" in manifest["files"]
        # Resources directory should not be in root files
        assert "resources" not in manifest["files"]


def test_generateManifest_excludes_resources_from_root():
    """Test that resources directory is excluded from root manifest files.

    GIVEN a must-gather directory with resources subdirectory
    WHEN generateManifest() is called
    THEN resources directory is not included in root files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources"
        resourcesPath.mkdir()
        (resourcesPath / "namespace1").mkdir()

        manifest = generateManifest(str(outputPath))

        assert "resources" not in manifest["files"]
        assert "namespace1" in manifest["namespaces"]


def test_generateManifest_handles_empty_resources():
    """Test manifest generation with empty resources directory.

    GIVEN a must-gather directory with empty resources directory
    WHEN generateManifest() is called
    THEN manifest is created with empty namespaces list.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources"
        resourcesPath.mkdir()

        manifest = generateManifest(str(outputPath))

        assert manifest["namespaces"] == []


def test_generateManifest_includes_cluster_metadata():
    """Test that cluster metadata is included when available.

    GIVEN a must-gather directory with cluster version info
    WHEN generateManifest() is called
    THEN cluster metadata is included in manifest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources" / "_cluster"
        resourcesPath.mkdir(parents=True)

        # Create cluster version file
        (resourcesPath / "clusterversions.md").write_text("# Cluster Version")

        manifest = generateManifest(str(outputPath))

        assert "cluster" in manifest
        assert manifest["cluster"]["info_available"] is True


def test_generateNamespaceManifest_creates_namespace_file():
    """Test that namespace manifest is created correctly.

    GIVEN a namespace directory with files
    WHEN _generateNamespaceManifest() is called
    THEN a namespace manifest file is created.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources"
        namespacePath = resourcesPath / "test-ns"
        namespacePath.mkdir(parents=True)

        # Create test files
        (namespacePath / "pods.md").write_text("# Pods")
        podsDir = namespacePath / "pods"
        podsDir.mkdir()
        (podsDir / "pod1.yaml").write_text("kind: Pod")

        # Generate namespace manifest
        _generateNamespaceManifest(outputPath, "test-ns")

        # Verify manifest file exists
        manifestPath = resourcesPath / "test-ns.json"
        assert manifestPath.exists()

        # Verify content
        with open(manifestPath) as f:
            nsManifest = json.load(f)

        assert nsManifest["namespace"] == "test-ns"
        assert "files" in nsManifest
        assert "pods.md" in nsManifest["files"]
        assert "pods" in nsManifest["files"]


def test_writeManifest_creates_json_file():
    """Test that writeManifest creates a valid JSON file.

    GIVEN a manifest dictionary
    WHEN writeManifest() is called
    THEN a valid JSON file is created.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = {"version": "2.0", "generated": "2026-06-07T19:00:00Z", "namespaces": ["ns1", "ns2"], "files": {}}

        writeManifest(tmpdir, manifest)

        manifestPath = Path(tmpdir) / "manifest.json"
        assert manifestPath.exists()

        with open(manifestPath) as f:
            loaded = json.load(f)

        assert loaded == manifest


def test_generateManifest_handles_nested_directories():
    """Test manifest generation with nested directory structures.

    GIVEN a namespace with nested directories
    WHEN generateManifest() is called
    THEN nested structure is preserved in namespace manifest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        namespacePath = outputPath / "resources" / "test-ns"
        nestedPath = namespacePath / "pods" / "details"
        nestedPath.mkdir(parents=True)

        (nestedPath / "pod1.yaml").write_text("kind: Pod")

        generateManifest(str(outputPath))

        # Verify namespace manifest was created
        nsManifestPath = outputPath / "resources" / "test-ns.json"
        assert nsManifestPath.exists()

        with open(nsManifestPath) as f:
            nsManifest = json.load(f)

        assert "pods" in nsManifest["files"]
        assert nsManifest["files"]["pods"]["type"] == "directory"


def test_generateManifest_skips_binary_files():
    """Test that binary files are excluded from manifests.

    GIVEN a directory with binary files
    WHEN generateManifest() is called
    THEN binary files are not included in manifest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)

        # Create text and binary files
        (outputPath / "text.txt").write_text("text content")
        (outputPath / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

        result = generateManifest(str(outputPath))

        assert "text.txt" in result["files"]
        assert "binary.bin" not in result["files"]


def test_generateManifest_sorts_namespaces():
    """Test that namespaces are sorted alphabetically.

    GIVEN multiple namespace directories
    WHEN generateManifest() is called
    THEN namespaces list is sorted.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputPath = Path(tmpdir)
        resourcesPath = outputPath / "resources"
        resourcesPath.mkdir()

        # Create namespaces in non-alphabetical order
        (resourcesPath / "zebra-ns").mkdir()
        (resourcesPath / "alpha-ns").mkdir()
        (resourcesPath / "beta-ns").mkdir()

        manifest = generateManifest(str(outputPath))

        assert manifest["namespaces"] == ["alpha-ns", "beta-ns", "zebra-ns"]
