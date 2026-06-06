# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Output directory management for must-gather."""

import logging
import os
import shutil
import tarfile
from datetime import datetime
from typing import Optional


class OutputManager:
    """Manage output directory structure and archive creation for must-gather.

    Handles creation of timestamped output directories, subdirectory organization,
    tar.gz archive generation, and cleanup operations.
    """

    def __init__(self, baseDir: str, keepFiles: bool = False):
        """Initialize output manager.

        Args:
            baseDir (str): Base directory where must-gather output will be created
            keepFiles (bool, optional): Whether to keep individual files after archiving. Defaults to False.
        """
        self.baseDir = baseDir
        self.keepFiles = keepFiles
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.outputDir = os.path.join(baseDir, self.timestamp)
        self.logFile = None
        self.logHandler: Optional[logging.FileHandler] = None

    def initialize(self) -> None:
        """Initialize output directory structure.

        Creates the timestamped output directory and sets up the log file path.

        Raises:
            OSError: If directory creation fails
        """
        os.makedirs(self.outputDir, exist_ok=True)
        self.logFile = os.path.join(self.outputDir, "must-gather.log")

    def getNamespaceDir(self, namespace: str) -> str:
        """Get directory path for namespace-specific resources.

        Creates the directory if it doesn't exist.

        Args:
            namespace (str): Kubernetes namespace name

        Returns:
            str: Path to namespace directory
        """
        namespaceDir = os.path.join(self.outputDir, "resources", namespace)
        os.makedirs(namespaceDir, exist_ok=True)
        return namespaceDir

    def getClusterDir(self) -> str:
        """Get directory path for cluster-level resources.

        Creates the directory if it doesn't exist.

        Returns:
            str: Path to cluster directory
        """
        clusterDir = os.path.join(self.outputDir, "resources", "_cluster")
        os.makedirs(clusterDir, exist_ok=True)
        return clusterDir

    def getArchivePath(self) -> str:
        """Get path for the tar.gz archive file.

        Returns:
            str: Path where archive will be created
        """
        filename = f"must-gather-{self.timestamp}.tgz"
        return os.path.join(self.baseDir, filename)

    def createArchive(self) -> str:
        """Create tar.gz archive of the output directory.

        Returns:
            str: Path to created archive file

        Raises:
            OSError: If archive creation fails
        """
        archivePath = self.getArchivePath()

        with tarfile.open(archivePath, "w:gz") as tar:
            tar.add(self.outputDir, arcname=self.timestamp)

        return archivePath

    def setupLogging(self) -> None:
        """Configure logging to write to must-gather.log in addition to mas.log.

        Adds a FileHandler to the root logger that writes all log messages
        to the must-gather.log file within the output directory.
        """
        if not self.logFile:
            raise RuntimeError("OutputManager must be initialized before setting up logging")

        # Create formatter matching the mas.log format
        formatter = logging.Formatter("%(asctime)s  %(levelname)-8s [%(name)s:%(lineno)d] %(message)s")

        # Create file handler for must-gather.log
        self.logHandler = logging.FileHandler(self.logFile)
        self.logHandler.setLevel(logging.DEBUG)
        self.logHandler.setFormatter(formatter)

        # Add handler to root logger
        rootLogger = logging.getLogger()
        rootLogger.addHandler(self.logHandler)

    def cleanup(self) -> None:
        """Clean up output directory and logging handler.

        Removes the log handler from the root logger and optionally removes
        the output directory and all its contents if keepFiles is False.
        """
        # Remove the log handler from root logger
        if self.logHandler:
            rootLogger = logging.getLogger()
            rootLogger.removeHandler(self.logHandler)
            self.logHandler.close()
            self.logHandler = None

        # Remove output directory if not keeping files
        if not self.keepFiles and os.path.exists(self.outputDir):
            shutil.rmtree(self.outputDir)
