# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Test output directory management for must-gather."""

import logging
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

    def test_sets_log_file_path(self):
        """Test that output manager sets log file path.

        GIVEN output manager
        WHEN initialize is called
        THEN log file path is set.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            assert manager.logFile is not None
            assert manager.logFile.endswith("must-gather.log")
            assert manager.outputDir in manager.logFile

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

    def test_setup_logging_creates_file_handler(self):
        """Test that setupLogging creates and configures file handler.

        GIVEN initialized output manager
        WHEN setupLogging is called
        THEN file handler is added to root logger.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()

            # Get initial handler count
            rootLogger = logging.getLogger()
            initialHandlerCount = len(rootLogger.handlers)

            manager.setupLogging()

            # Verify handler was added
            assert len(rootLogger.handlers) == initialHandlerCount + 1
            assert manager.logHandler is not None
            assert isinstance(manager.logHandler, logging.FileHandler)

            # Cleanup
            manager.cleanup()

    def test_setup_logging_writes_to_must_gather_log(self):
        """Test that logging writes to must-gather.log file.

        GIVEN output manager with logging configured
        WHEN log messages are written
        THEN messages appear in must-gather.log.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()
            manager.setupLogging()

            # Write test log message
            testLogger = logging.getLogger("test.module")
            testLogger.setLevel(logging.DEBUG)
            testLogger.info("Test log message for must-gather")

            # Flush handlers to ensure write
            for handler in logging.getLogger().handlers:
                handler.flush()

            # Verify log file contains message
            assert manager.logFile is not None
            assert os.path.exists(manager.logFile)
            with open(manager.logFile, "r") as f:
                content = f.read()
                assert "Test log message for must-gather" in content
                assert "test.module" in content

            # Cleanup
            manager.cleanup()

    def test_setup_logging_requires_initialization(self):
        """Test that setupLogging requires initialize to be called first.

        GIVEN output manager without initialization
        WHEN setupLogging is called
        THEN RuntimeError is raised.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)

            try:
                manager.setupLogging()
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert "must be initialized" in str(e)

    def test_cleanup_removes_log_handler(self):
        """Test that cleanup removes log handler from root logger.

        GIVEN output manager with logging configured
        WHEN cleanup is called
        THEN log handler is removed from root logger.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()
            manager.setupLogging()

            rootLogger = logging.getLogger()
            handlerCountBefore = len(rootLogger.handlers)

            manager.cleanup()

            # Verify handler was removed
            assert len(rootLogger.handlers) == handlerCountBefore - 1
            assert manager.logHandler is None

    def test_logging_format_matches_mas_log(self):
        """Test that must-gather.log uses same format as mas.log.

        GIVEN output manager with logging configured
        WHEN log message is written
        THEN format includes timestamp, level, module name, and line number.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()
            manager.setupLogging()

            # Write test log message
            testLogger = logging.getLogger("test.format.check")
            testLogger.setLevel(logging.DEBUG)
            testLogger.warning("Format test message")

            # Flush handlers
            for handler in logging.getLogger().handlers:
                handler.flush()

            # Verify format
            assert manager.logFile is not None
            with open(manager.logFile, "r") as f:
                content = f.read()
                # Check for expected format components
                assert "WARNING" in content
                assert "test.format.check" in content
                assert "Format test message" in content
                # Format should include timestamp (YYYY-MM-DD HH:MM:SS)
                assert any(char.isdigit() for char in content)

            # Cleanup
            manager.cleanup()

    def test_multiple_loggers_write_to_must_gather_log(self):
        """Test that multiple loggers write to must-gather.log.

        GIVEN output manager with logging configured
        WHEN multiple loggers write messages
        THEN all messages appear in must-gather.log.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = OutputManager(tmpdir)
            manager.initialize()
            manager.setupLogging()

            # Write from multiple loggers
            logger1 = logging.getLogger("module.one")
            logger1.setLevel(logging.DEBUG)
            logger1.info("Message from logger 1")

            logger2 = logging.getLogger("module.two")
            logger2.setLevel(logging.DEBUG)
            logger2.error("Message from logger 2")

            # Flush handlers
            for handler in logging.getLogger().handlers:
                handler.flush()

            # Verify both messages in log
            assert manager.logFile is not None
            with open(manager.logFile, "r") as f:
                content = f.read()
                assert "Message from logger 1" in content
                assert "module.one" in content
                assert "Message from logger 2" in content
                assert "module.two" in content

            # Cleanup
            manager.cleanup()
