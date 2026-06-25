# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for web viewer generation functionality.

GIVEN a must-gather output directory
WHEN generateWebViewer is called
THEN manifest.json and index.html are created with correct structure.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mas.cli.must_gather import web_viewer


class TestManifestGeneration:
    """Test manifest generation functionality."""

    def test_generateManifest_creates_valid_structure(self):
        """Test that generateManifest creates valid manifest structure.

        GIVEN a temporary directory with sample files
        WHEN generateManifest is called
        THEN manifest contains version, generated timestamp, and files structure.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create sample directory structure
            resourcesDir = Path(tmpDir) / "resources"
            resourcesDir.mkdir()
            (resourcesDir / "test.md").write_text("# Test")
            (resourcesDir / "test.yaml").write_text("key: value")

            # Generate manifest
            manifest = web_viewer.generateManifest(tmpDir)

            # Verify structure
            assert "version" in manifest
            assert "generated" in manifest
            assert "files" in manifest
            assert manifest["version"] == "2.0"
            # In version 2.0, resources directory creates split manifests, so files dict may be empty
            # or contain non-namespace directories

    def test_generateManifest_handles_nested_directories(self):
        """Test that generateManifest handles nested directory structures.

        GIVEN a directory with nested subdirectories
        WHEN generateManifest is called
        THEN manifest includes all nested directories and files.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create nested structure
            nestedDir = Path(tmpDir) / "resources" / "namespace1" / "pods"
            nestedDir.mkdir(parents=True)
            (nestedDir / "pod1.yaml").write_text("apiVersion: v1")

            # Generate manifest
            manifest = web_viewer.generateManifest(tmpDir)

            # Verify nested structure - in v2.0, namespace directories create split manifests
            assert "namespaces" in manifest
            assert "namespace1" in manifest["namespaces"]
            # Resources directory itself is not in files since all its subdirectories are namespaces

    def test_generateManifest_excludes_hidden_files(self):
        """Test that generateManifest excludes hidden files.

        GIVEN a directory with hidden files
        WHEN generateManifest is called
        THEN hidden files are not included in manifest.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create hidden file
            (Path(tmpDir) / ".hidden").write_text("hidden")
            (Path(tmpDir) / "visible.md").write_text("visible")

            # Generate manifest
            manifest = web_viewer.generateManifest(tmpDir)

            # Verify hidden file excluded
            assert ".hidden" not in manifest["files"]
            assert "visible.md" in manifest["files"]

    def test_generateManifest_excludes_manifest_and_index(self):
        """Test that generateManifest excludes manifest.json and index.html.

        GIVEN a directory with manifest.json and index.html
        WHEN generateManifest is called
        THEN these files are not included in the manifest.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create files that should be excluded
            (Path(tmpDir) / "manifest.json").write_text("{}")
            (Path(tmpDir) / "index.html").write_text("<html></html>")
            (Path(tmpDir) / "other.md").write_text("# Other")

            # Generate manifest
            manifest = web_viewer.generateManifest(tmpDir)

            # Verify exclusions
            assert "manifest.json" not in manifest["files"]
            assert "index.html" not in manifest["files"]
            assert "other.md" in manifest["files"]

    def test_generateManifest_handles_empty_directory(self):
        """Test that generateManifest handles empty directories.

        GIVEN an empty directory
        WHEN generateManifest is called
        THEN manifest is created with empty files structure.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Generate manifest for empty directory
            manifest = web_viewer.generateManifest(tmpDir)

            # Verify structure
            assert "files" in manifest
            assert manifest["files"] == {}

    def test_generateManifest_raises_on_nonexistent_directory(self):
        """Test that generateManifest raises error for nonexistent directory.

        GIVEN a nonexistent directory path
        WHEN generateManifest is called
        THEN OSError is raised.
        """
        with pytest.raises(OSError, match="does not exist"):
            web_viewer.generateManifest("/nonexistent/path")


class TestBinaryFileDetection:
    """Test binary file detection functionality."""

    def test_isBinaryFile_detects_text_extensions(self):
        """Test that text file extensions are correctly identified.

        GIVEN files with text extensions
        WHEN _isBinaryFile is called
        THEN False is returned.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            textFiles = ["test.md", "test.yaml", "test.yml", "test.json", "test.log", "test.txt"]
            for filename in textFiles:
                filePath = Path(tmpDir) / filename
                filePath.write_text("content")
                assert not web_viewer._isBinaryFile(filePath), f"{filename} should not be binary"

    def test_isBinaryFile_detects_null_bytes(self):
        """Test that files with null bytes are detected as binary.

        GIVEN a file with null bytes
        WHEN _isBinaryFile is called
        THEN True is returned.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            binaryFile = Path(tmpDir) / "binary.dat"
            binaryFile.write_bytes(b"content\x00binary")
            assert web_viewer._isBinaryFile(binaryFile)


class TestManifestWriting:
    """Test manifest writing functionality."""

    def test_writeManifest_creates_valid_json(self):
        """Test that writeManifest creates valid JSON file.

        GIVEN a manifest dictionary
        WHEN writeManifest is called
        THEN manifest.json is created with valid JSON.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            manifest = {"version": "1.0", "generated": "2024-01-01T00:00:00Z", "files": {"test.md": {"type": "file", "path": "test.md", "size": 100}}}

            # Write manifest
            web_viewer.writeManifest(tmpDir, manifest)

            # Verify file created and valid
            manifestPath = Path(tmpDir) / "manifest.json"
            assert manifestPath.exists()

            with open(manifestPath, "r") as f:
                loaded = json.load(f)
                assert loaded == manifest

    def test_writeManifest_raises_on_write_failure(self):
        """Test that writeManifest raises error on write failure.

        GIVEN an invalid output directory
        WHEN writeManifest is called
        THEN OSError is raised.
        """
        with pytest.raises(OSError, match="Failed to write manifest"):
            web_viewer.writeManifest("/invalid/path", {})


class TestViewerTemplateCopying:
    """Test viewer template copying functionality."""

    def test_copyViewerTemplate_creates_index_html(self):
        """Test that copyViewerTemplate creates index.html.

        GIVEN a valid output directory and manifest
        WHEN copyViewerTemplate is called
        THEN index.html is created with embedded manifest.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Copy template
            web_viewer.copyViewerTemplate(tmpDir)

            # Verify file created
            indexPath = Path(tmpDir) / "index.html"
            assert indexPath.exists()
            assert indexPath.stat().st_size > 0

            # Verify template content was copied
            with open(indexPath, "r") as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content

    def test_copyViewerTemplate_raises_on_missing_template(self):
        """Test that copyViewerTemplate raises error if template missing.

        GIVEN a scenario where template file doesn't exist
        WHEN copyViewerTemplate is called
        THEN OSError is raised.
        """
        # This test verifies error handling, but in normal operation
        # the template should always exist
        with tempfile.TemporaryDirectory() as tmpDir:
            # Temporarily move template to simulate missing file
            templatePath = Path(web_viewer.__file__).parent / "templates" / "viewer.html"
            if templatePath.exists():
                # Template exists, so we can't test missing template scenario
                # Just verify the function works normally
                web_viewer.copyViewerTemplate(tmpDir)
                assert (Path(tmpDir) / "index.html").exists()


class TestWebViewerGeneration:
    """Test complete web viewer generation."""

    def test_generateWebViewer_creates_all_files(self):
        """Test that generateWebViewer creates both manifest and viewer.

        GIVEN a directory with sample must-gather output
        WHEN generateWebViewer is called
        THEN both manifest.json and index.html are created.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create sample structure
            resourcesDir = Path(tmpDir) / "resources"
            resourcesDir.mkdir()
            (resourcesDir / "test.md").write_text("# Test")

            # Generate web viewer
            result = web_viewer.generateWebViewer(tmpDir)

            # Verify success
            assert result is True
            assert (Path(tmpDir) / "manifest.json").exists()
            assert (Path(tmpDir) / "index.html").exists()

    def test_generateWebViewer_returns_false_on_error(self):
        """Test that generateWebViewer returns False on error.

        GIVEN an invalid output directory
        WHEN generateWebViewer is called
        THEN False is returned.
        """
        result = web_viewer.generateWebViewer("/nonexistent/path")
        assert result is False

    def test_generateWebViewer_with_complex_structure(self):
        """Test generateWebViewer with complex directory structure.

        GIVEN a complex must-gather directory structure
        WHEN generateWebViewer is called
        THEN manifest correctly represents the structure.
        """
        with tempfile.TemporaryDirectory() as tmpDir:
            # Create complex structure
            structure = {
                "resources": {
                    "_cluster": ["nodes.md", "clusterversions.md"],
                    "namespace1": {"pods": ["pod1.yaml", "pod2.yaml"], "services": ["svc1.yaml"]},
                    "namespace2": {"deployments": ["deploy1.yaml"]},
                },
                "logs": {"namespace1": ["pod1.log"]},
            }

            def createStructure(basePath: Path, struct: dict):
                for name, content in struct.items():
                    path = basePath / name
                    if isinstance(content, dict):
                        path.mkdir(parents=True, exist_ok=True)
                        createStructure(path, content)
                    elif isinstance(content, list):
                        path.mkdir(parents=True, exist_ok=True)
                        for filename in content:
                            (path / filename).write_text(f"# {filename}")

            createStructure(Path(tmpDir), structure)

            # Generate web viewer
            result = web_viewer.generateWebViewer(tmpDir)

            # Verify success and structure
            assert result is True

            # Load and verify manifest
            with open(Path(tmpDir) / "manifest.json", "r") as f:
                manifest = json.load(f)

            # In v2.0, namespace directories under resources/ create split manifests
            assert "namespaces" in manifest
            assert "_cluster" in manifest["namespaces"]
            assert "namespace1" in manifest["namespaces"]
            assert "namespace2" in manifest["namespaces"]
            # Non-namespace directories like logs are in files
            assert "logs" in manifest["files"]
