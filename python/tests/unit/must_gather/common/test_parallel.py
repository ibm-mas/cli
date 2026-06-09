# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for parallel resource collection utilities.

GIVEN a list of resource types to collect
WHEN collectResourcesParallel is called
THEN resources are collected in parallel using ThreadPoolExecutor.
"""

from unittest.mock import Mock, patch, call
from mas.cli.must_gather.common.parallel import collectResourcesParallel


class TestCollectResourcesParallel:
    """Test parallel resource collection functionality."""

    def test_collectResourcesParallel_collects_multiple_resources_successfully(self):
        """Test successful parallel collection of multiple resources.

        GIVEN a list of multiple resource types
        WHEN collectResourcesParallel is called
        THEN all resources are collected in parallel and function returns True.
        """
        # Setup
        mockDynClient = Mock()
        namespace = "test-namespace"
        resources = [
            ("v1", "ConfigMap"),
            ("v1", "Service"),
            ("apps/v1", "Deployment"),
        ]
        outputDir = "/tmp/output"

        with patch("mas.cli.must_gather.common.parallel.collectResources") as mockCollectResources:
            # Mock collectResources to return True for all calls
            mockCollectResources.return_value = True

            # Execute
            result = collectResourcesParallel(
                dynClient=mockDynClient,
                namespace=namespace,
                resources=resources,
                outputDir=outputDir,
            )

            # Verify
            assert result is True
            assert mockCollectResources.call_count == 3

            # Verify all resources were collected (order may vary due to parallel execution)
            expectedCalls = [
                call(
                    namespace=namespace,
                    apiVersion="v1",
                    kind="ConfigMap",
                    outputDir=outputDir,
                    allNamespaces=False,
                ),
                call(
                    namespace=namespace,
                    apiVersion="v1",
                    kind="Service",
                    outputDir=outputDir,
                    allNamespaces=False,
                ),
                call(
                    namespace=namespace,
                    apiVersion="apps/v1",
                    kind="Deployment",
                    outputDir=outputDir,
                    allNamespaces=False,
                ),
            ]
            for expectedCall in expectedCalls:
                assert expectedCall in mockCollectResources.call_args_list

    def test_collectResourcesParallel_handles_errors_gracefully(self):
        """Test error handling when some collections fail.

        GIVEN a list of resource types where some will fail
        WHEN collectResourcesParallel is called
        THEN function continues collecting other resources and returns False.
        """
        # Setup
        mockDynClient = Mock()
        namespace = "test-namespace"
        resources = [
            ("v1", "ConfigMap"),
            ("v1", "Service"),
            ("apps/v1", "Deployment"),
        ]
        outputDir = "/tmp/output"

        with patch("mas.cli.must_gather.common.parallel.collectResources") as mockCollectResources:
            # Mock collectResources to fail for Service
            def sideEffect(*args, **kwargs):
                if kwargs.get("kind") == "Service":
                    return False
                return True

            mockCollectResources.side_effect = sideEffect

            # Execute
            result = collectResourcesParallel(
                dynClient=mockDynClient,
                namespace=namespace,
                resources=resources,
                outputDir=outputDir,
            )

            # Verify
            assert result is False  # Should return False because one collection failed
            assert mockCollectResources.call_count == 3  # All collections attempted

    def test_collectResourcesParallel_respects_max_workers(self):
        """Test that max_workers parameter is respected.

        GIVEN a custom max_workers value
        WHEN collectResourcesParallel is called
        THEN ThreadPoolExecutor is created with specified max_workers.
        """
        # Setup
        mockDynClient = Mock()
        namespace = "test-namespace"
        resources = [("v1", "ConfigMap")]
        outputDir = "/tmp/output"
        maxWorkers = 5

        with patch("mas.cli.must_gather.common.parallel.collectResources") as mockCollectResources:
            mockCollectResources.return_value = True

            with patch("mas.cli.must_gather.common.parallel.ThreadPoolExecutor") as mockExecutor:
                # Create a mock future that returns immediately
                mockFuture = Mock()
                mockFuture.result.return_value = True

                mockExecutorInstance = Mock()
                mockExecutor.return_value.__enter__.return_value = mockExecutorInstance
                mockExecutorInstance.submit.return_value = mockFuture

                # Mock as_completed to return the future immediately
                with patch("mas.cli.must_gather.common.parallel.as_completed") as mockAsCompleted:
                    mockAsCompleted.return_value = [mockFuture]

                    # Execute
                    collectResourcesParallel(
                        dynClient=mockDynClient,
                        namespace=namespace,
                        resources=resources,
                        outputDir=outputDir,
                        max_workers=maxWorkers,
                    )

                    # Verify
                    mockExecutor.assert_called_once_with(max_workers=maxWorkers)

    def test_collectResourcesParallel_with_empty_resources_list(self):
        """Test handling of empty resources list.

        GIVEN an empty resources list
        WHEN collectResourcesParallel is called
        THEN function returns True without attempting any collections.
        """
        # Setup
        mockDynClient = Mock()
        namespace = "test-namespace"
        resources = []
        outputDir = "/tmp/output"

        with patch("mas.cli.must_gather.common.parallel.collectResources") as mockCollectResources:
            # Execute
            result = collectResourcesParallel(
                dynClient=mockDynClient,
                namespace=namespace,
                resources=resources,
                outputDir=outputDir,
            )

            # Verify
            assert result is True
            mockCollectResources.assert_not_called()

    def test_collectResourcesParallel_updates_progress_bar(self):
        """Test that progress bar is updated as resources are collected.

        GIVEN a progress bar callback
        WHEN collectResourcesParallel is called
        THEN progress bar is incremented for each completed resource.
        """
        # Setup
        mockDynClient = Mock()
        namespace = "test-namespace"
        resources = [
            ("v1", "ConfigMap"),
            ("v1", "Service"),
        ]
        outputDir = "/tmp/output"
        mockProgressBar = Mock()

        with patch("mas.cli.must_gather.common.parallel.collectResources") as mockCollectResources:
            mockCollectResources.return_value = True

            # Execute
            result = collectResourcesParallel(
                dynClient=mockDynClient,
                namespace=namespace,
                resources=resources,
                outputDir=outputDir,
                progressCallback=mockProgressBar,
            )

            # Verify
            assert result is True
            # Progress bar should be called once for each resource
            assert mockProgressBar.call_count == 2
