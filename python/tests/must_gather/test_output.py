# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test output directory management for must-gather."""

import os
import tempfile
import tarfile
from mas.cli.must_gather.output import OutputManager


class TestOutputManager:
    """Test output directory management."""

    def test_creates_timestamped_directory(self):
        """Test that output manager creates timestamped directory.

        GIVEN output manager with base directory
        WHEN initialize is called
        THEN timestamped directory is created.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            assert os.path.exists(manager.outputDir)
            assert manager.outputDir.startswith(tmpdir)
            assert manager.timestamp in manager.outputDir

    def test_creates_log_file(self):
        """Test that output manager creates log file.

        GIVEN output manager
        WHEN initialize is called
        THEN log file is created in output directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            logFile = os.path.join(manager.outputDir, "must-gather.log")
            assert os.path.exists(logFile)

    def test_creates_tar_archive(self):
        """Test that output manager creates tar.gz archive.

        GIVEN output manager with initialized directory
        WHEN createArchive is called
        THEN tar.gz file is created.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            # Create a test file
            testFile = os.path.join(manager.outputDir, "test.txt")
            with open(testFile, "w") as f:
                f.write("test content")

            archivePath = manager.createArchive()

            assert os.path.exists(archivePath)
            assert archivePath.endswith(".tgz")
            assert tarfile.is_tarfile(archivePath)

    def test_archive_contains_files(self):
        """Test that created archive contains expected files.

        GIVEN output manager with files in directory
        WHEN createArchive is called
        THEN archive contains all files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            # Create test files
            testFile = os.path.join(manager.outputDir, "test.txt")
            with open(testFile, "w") as f:
                f.write("test content")

            archivePath = manager.createArchive()

            with tarfile.open(archivePath, "r:gz") as tar:
                members = tar.getnames()
                assert any("test.txt" in m for m in members)

    def test_cleanup_removes_directory_when_keep_files_false(self):
        """Test that cleanup removes directory when keep_files is False.

        GIVEN output manager with keep_files=False
        WHEN cleanup is called
        THEN output directory is removed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir, keepFiles=False)
            manager.initialize()
            outputDir = manager.outputDir

            manager.cleanup()

            assert not os.path.exists(outputDir)

    def test_cleanup_keeps_directory_when_keep_files_true(self):
        """Test that cleanup keeps directory when keep_files is True.

        GIVEN output manager with keep_files=True
        WHEN cleanup is called
        THEN output directory is preserved.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir, keepFiles=True)
            manager.initialize()
            outputDir = manager.outputDir

            manager.cleanup()

            assert os.path.exists(outputDir)

    def test_get_namespace_dir_creates_subdirectory(self):
        """Test that getNamespaceDir creates namespace subdirectory.

        GIVEN output manager
        WHEN getNamespaceDir is called with namespace
        THEN namespace subdirectory is created under resources.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            namespaceDir = manager.getNamespaceDir("test-namespace")

            assert os.path.exists(namespaceDir)
            assert "test-namespace" in namespaceDir
            assert "resources" in namespaceDir

    def test_get_cluster_dir_creates_cluster_subdirectory(self):
        """Test that getClusterDir creates _cluster subdirectory.

        GIVEN output manager
        WHEN getClusterDir is called
        THEN _cluster subdirectory is created under resources.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            clusterDir = manager.getClusterDir()

            assert os.path.exists(clusterDir)
            assert "_cluster" in clusterDir
            assert "resources" in clusterDir

    def test_output_filename_format(self):
        """Test that output filename follows expected format.

        GIVEN output manager
        WHEN getArchivePath is called
        THEN filename matches must-gather-TIMESTAMP.tgz format.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            archivePath = manager.getArchivePath()
            filename = os.path.basename(archivePath)

            assert filename.startswith("must-gather-")
            assert filename.endswith(".tgz")
            assert manager.timestamp in filename
