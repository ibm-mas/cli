# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for SLS namespace filtering and pod log read retries."""

from unittest.mock import Mock, patch
import pytest
from kubernetes.client.exceptions import ApiException

from mas.cli.must_gather.common import pods
from mas.cli.must_gather.dependencies import sls


class TestSLSNamespaceFilter:
    """Test the slsNamespaceFilter option of addSLSToCollectionPlan."""

    @patch("mas.cli.must_gather.dependencies.sls._generateSLSCollectionTasks", return_value=[("t", None)])
    @patch("mas.cli.must_gather.dependencies.sls._discoverSLSNamespaces")
    def test_filter_limits_namespaces(self, mockDiscover, mockTasks):
        """Test that only requested SLS namespaces are added to the plan.

        GIVEN multiple SLS namespaces are discovered
        WHEN slsNamespaceFilter names one of them
        THEN only that namespace is added to the plan.
        """
        mockDiscover.return_value = {"mas-a-sls", "mas-b-sls", "mas-c-sls"}
        plan = Mock()
        sls.addSLSToCollectionPlan(plan, Mock(), "/tmp/out", False, [], slsNamespaceFilter=["mas-b-sls"])
        assert [c.args[0] for c in plan.addGroup.call_args_list] == ["mas-b-sls"]

    @patch("mas.cli.must_gather.dependencies.sls._generateSLSCollectionTasks", return_value=[("t", None)])
    @patch("mas.cli.must_gather.dependencies.sls._discoverSLSNamespaces")
    def test_no_filter_collects_all(self, mockDiscover, mockTasks):
        """Test that without a filter all discovered SLS namespaces are collected.

        GIVEN multiple SLS namespaces are discovered
        WHEN slsNamespaceFilter is not provided
        THEN all namespaces are added to the plan.
        """
        mockDiscover.return_value = {"mas-a-sls", "mas-b-sls"}
        plan = Mock()
        sls.addSLSToCollectionPlan(plan, Mock(), "/tmp/out", False, [])
        assert plan.addGroup.call_count == 2

    @patch("mas.cli.must_gather.dependencies.sls._discoverSLSNamespaces")
    def test_filter_with_unknown_namespace_adds_nothing(self, mockDiscover):
        """Test that a filter matching no discovered namespace adds no groups.

        GIVEN SLS namespaces are discovered
        WHEN slsNamespaceFilter only names an unknown namespace
        THEN no groups are added to the plan.
        """
        mockDiscover.return_value = {"mas-a-sls"}
        plan = Mock()
        sls.addSLSToCollectionPlan(plan, Mock(), "/tmp/out", False, [], slsNamespaceFilter=["nope"])
        plan.addGroup.assert_not_called()


class TestPodLogRetry:
    """Test retry behaviour of _readPodLogWithRetry."""

    @patch("mas.cli.must_gather.common.pods.time.sleep")
    def test_retries_connection_errors_then_succeeds(self, mockSleep):
        """Test transient connection errors are retried.

        GIVEN the first two log reads raise a connection error
        WHEN _readPodLogWithRetry is called
        THEN the third attempt's logs are returned.
        """
        coreV1 = Mock()
        coreV1.read_namespaced_pod_log.side_effect = [ConnectionError("refused"), ConnectionError("refused"), "logs"]
        assert pods._readPodLogWithRetry(coreV1, "ns", "pod", "c") == "logs"
        assert coreV1.read_namespaced_pod_log.call_count == 3
        assert mockSleep.call_count == 2

    @patch("mas.cli.must_gather.common.pods.time.sleep")
    def test_raises_after_max_attempts(self, mockSleep):
        """Test the last error is raised once attempts are exhausted.

        GIVEN every log read raises a connection error
        WHEN _readPodLogWithRetry is called
        THEN the error is raised after the maximum number of attempts.
        """
        coreV1 = Mock()
        coreV1.read_namespaced_pod_log.side_effect = ConnectionError("refused")
        with pytest.raises(ConnectionError):
            pods._readPodLogWithRetry(coreV1, "ns", "pod", "c")
        assert coreV1.read_namespaced_pod_log.call_count == pods.LOG_READ_MAX_ATTEMPTS

    @patch("mas.cli.must_gather.common.pods.time.sleep")
    def test_api_exception_not_retried(self, mockSleep):
        """Test Kubernetes API errors are not retried.

        GIVEN the log read raises an ApiException
        WHEN _readPodLogWithRetry is called
        THEN it is raised immediately without retrying.
        """
        coreV1 = Mock()
        coreV1.read_namespaced_pod_log.side_effect = ApiException(status=400)
        with pytest.raises(ApiException):
            pods._readPodLogWithRetry(coreV1, "ns", "pod", "c")
        assert coreV1.read_namespaced_pod_log.call_count == 1
        mockSleep.assert_not_called()
