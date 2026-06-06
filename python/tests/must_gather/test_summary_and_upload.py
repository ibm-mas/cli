# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for Artifactory upload functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from mas.cli.must_gather.app import MustGatherApp


class TestUploadToArtifactory:
    """Test suite for uploadToArtifactory method."""

    def test_upload_success(self):
        """Test successful Artifactory upload.

        GIVEN a must-gather app with valid archive
        WHEN uploadToArtifactory is called with valid credentials
        THEN archive is uploaded with correct checksums.
        """
        app = MustGatherApp()

        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test archive content")
            tmpfile.flush()
            archivePath = tmpfile.name

        try:
            mockResponse = MagicMock()
            mockResponse.status_code = 201

            with patch("requests.put", return_value=mockResponse) as mockPut:
                result = app.uploadToArtifactory(
                    archivePath=archivePath, artifactoryToken="test-token", artifactoryUploadDir="https://artifactory.example.com/repo"
                )

                assert result is True
                # Verify PUT was called with correct URL
                mockPut.assert_called_once()
                args, kwargs = mockPut.call_args
                assert args[0].startswith("https://artifactory.example.com/repo/")
                # Verify headers include checksums
                assert "X-Checksum-Md5" in kwargs["headers"]
                assert "X-Checksum-Sha1" in kwargs["headers"]
                assert kwargs["headers"]["Authorization"] == "Bearer test-token"
        finally:
            os.unlink(archivePath)

    def test_upload_file_not_found(self):
        """Test upload when archive file doesn't exist.

        GIVEN a must-gather app
        WHEN uploadToArtifactory is called with non-existent file
        THEN returns False and logs error.
        """
        app = MustGatherApp()

        result = app.uploadToArtifactory(
            archivePath="/nonexistent/file.tar.gz", artifactoryToken="test-token", artifactoryUploadDir="https://artifactory.example.com/repo"
        )

        assert result is False

    def test_upload_http_error(self):
        """Test upload with HTTP error response.

        GIVEN a must-gather app with valid archive
        WHEN uploadToArtifactory is called and server returns error
        THEN returns False and logs error.
        """
        app = MustGatherApp()

        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test content")
            tmpfile.flush()
            archivePath = tmpfile.name

        try:
            mockResponse = MagicMock()
            mockResponse.status_code = 403
            mockResponse.text = "Forbidden"

            with patch("requests.put", return_value=mockResponse):
                result = app.uploadToArtifactory(
                    archivePath=archivePath, artifactoryToken="test-token", artifactoryUploadDir="https://artifactory.example.com/repo"
                )

                assert result is False
        finally:
            os.unlink(archivePath)

    def test_upload_network_error(self):
        """Test upload with network error.

        GIVEN a must-gather app with valid archive
        WHEN uploadToArtifactory is called and network error occurs
        THEN returns False and logs error.
        """
        app = MustGatherApp()

        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test content")
            tmpfile.flush()
            archivePath = tmpfile.name

        try:
            with patch("requests.put", side_effect=ConnectionError("Network error")):
                result = app.uploadToArtifactory(
                    archivePath=archivePath, artifactoryToken="test-token", artifactoryUploadDir="https://artifactory.example.com/repo"
                )

                assert result is False
        finally:
            os.unlink(archivePath)

    def test_upload_calculates_correct_checksums(self):
        """Test that upload calculates correct MD5 and SHA1 checksums.

        GIVEN a must-gather app with archive containing known content
        WHEN uploadToArtifactory is called
        THEN correct MD5 and SHA1 checksums are calculated.
        """
        app = MustGatherApp()

        # Create file with known content
        testContent = b"Hello, World!"
        expectedMd5 = "65a8e27d8879283831b664bd8b7f0ad4"  # MD5 of "Hello, World!"
        expectedSha1 = "0a0a9f2a6772942557ab5355d76af442f8f65e01"  # SHA1 of "Hello, World!"

        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(testContent)
            tmpfile.flush()
            archivePath = tmpfile.name

        try:
            mockResponse = MagicMock()
            mockResponse.status_code = 200

            with patch("requests.put", return_value=mockResponse) as mockPut:
                result = app.uploadToArtifactory(
                    archivePath=archivePath, artifactoryToken="test-token", artifactoryUploadDir="https://artifactory.example.com/repo"
                )

                assert result is True
                # Verify checksums in headers
                args, kwargs = mockPut.call_args
                assert kwargs["headers"]["X-Checksum-Md5"] == expectedMd5
                assert kwargs["headers"]["X-Checksum-Sha1"] == expectedSha1
        finally:
            os.unlink(archivePath)


# Made with Bob
