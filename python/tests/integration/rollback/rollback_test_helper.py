#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import time
import threading
import contextlib
from typing import Dict, Callable, Optional, List
from unittest import mock
from unittest.mock import MagicMock

from kubernetes.dynamic import DynamicClient

from mas.cli.rollback.app import RollbackApp
from utils.prompt_tracker import create_prompt_handler


class RollbackTestConfig:
    """Configuration for a rollback test scenario."""

    def __init__(
        self,
        prompt_handlers: Optional[Dict[str, Callable[[str], str]]] = None,
        installed_catalog_id: str = "v9-260527-amd64",
        mas_instances: Optional[List[Dict]] = None,
        architecture: str = "amd64",
        ocp_version: str = "4.18.0",
        timeout_seconds: int = 30,
        expect_system_exit: bool = False,
        expected_exit_code: Optional[int] = None,
        expect_exception: Optional[type] = None,
        argv: Optional[list] = None,
    ):
        """
        Initialize rollback test configuration.

        Args:
            prompt_handlers: Dictionary mapping regex patterns to handler functions
            installed_catalog_id: Currently installed catalog version
            mas_instances: List of MAS Suite instance dicts on the cluster
            architecture: Node architecture (amd64, s390x, ppc64le)
            ocp_version: OpenShift cluster version
            timeout_seconds: Watchdog timeout for hanging prompts
            expect_system_exit: Whether a SystemExit is expected
            expected_exit_code: Expected SystemExit code (only relevant when expect_system_exit=True)
            expect_exception: Exception type expected to be raised (other than SystemExit)
            argv: CLI argv list for non-interactive mode (empty list = interactive mode)
        """
        self.prompt_handlers = prompt_handlers if prompt_handlers is not None else {}
        self.installed_catalog_id = installed_catalog_id
        self.mas_instances = mas_instances if mas_instances is not None else [{"metadata": {"name": "inst1"}, "status": {"versions": {"reconciled": "9.1.4"}}}]
        self.architecture = architecture
        self.ocp_version = ocp_version
        self.timeout_seconds = timeout_seconds
        self.expect_system_exit = expect_system_exit
        self.expected_exit_code = expected_exit_code
        self.expect_exception = expect_exception
        self.argv = argv if argv is not None else []


class RollbackTestHelper:
    """Helper class to run rollback tests with minimal code duplication."""

    def __init__(self, tmpdir, config: RollbackTestConfig):
        """
        Initialize the test helper.

        Args:
            tmpdir: pytest tmpdir fixture
            config: Test configuration
        """
        self.tmpdir = tmpdir
        self.config = config
        self.test_failed = {"failed": False, "message": ""}
        self.last_prompt_time = {"time": time.time()}
        self.watchdog_thread = None
        self.prompt_tracker = None
        self.app = None

    def start_watchdog(self):
        """Start watchdog thread to detect hanging prompts."""

        def watchdog():
            while not self.test_failed["failed"]:
                time.sleep(1)
                elapsed = time.time() - self.last_prompt_time["time"]
                if elapsed > self.config.timeout_seconds:
                    self.test_failed["failed"] = True
                    self.test_failed["message"] = f"Test hung: No prompt received for {self.config.timeout_seconds}s"
                    break

        self.watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        self.watchdog_thread.start()

    def stop_watchdog(self):
        """Stop the watchdog thread."""
        self.test_failed["failed"] = True

    def setup_prompt_handler(self, mixins_prompt, prompt_session_instance):
        """Setup prompt handler with tracking and watchdog integration."""
        self.prompt_tracker, prompt_handler = create_prompt_handler(self.config.prompt_handlers)

        def wrapped_prompt_handler(*args, **kwargs):
            """Handle prompts and update watchdog timer."""
            if self.test_failed["failed"]:
                raise TimeoutError(self.test_failed["message"])
            self.last_prompt_time["time"] = time.time()
            return prompt_handler(*args, **kwargs)

        mixins_prompt.side_effect = wrapped_prompt_handler
        prompt_session_instance.prompt.side_effect = wrapped_prompt_handler

    def run_rollback_test(self):
        """
        Run the rollback test with all mocks configured.

        Raises:
            TimeoutError: If test times out
            AssertionError: If prompt verification or assertions fail
        """
        self.start_watchdog()

        system_exit_raised = False
        exit_code = None

        with mock.patch("mas.cli.cli.config"):
            # Build mock DynamicClient
            dynamic_client = MagicMock(DynamicClient)

            with contextlib.ExitStack() as stack:
                patches = [
                    ("dynamic_client_class", mock.patch("mas.cli.cli.DynamicClient")),
                    ("connect", mock.patch("mas.cli.cli.BaseApp.connect")),
                    ("get_nodes", mock.patch("mas.cli.cli.getNodes")),
                    ("cli_prompt", mock.patch("mas.cli.cli.prompt")),
                    ("get_current_catalog", mock.patch("mas.cli.rollback.app.getCurrentCatalog")),
                    ("get_console_url", mock.patch("mas.cli.rollback.app.getConsoleURL")),
                    ("list_mas_instances", mock.patch("mas.cli.rollback.app.listMasInstances")),
                    ("install_pipelines", mock.patch("mas.cli.rollback.app.installOpenShiftPipelines")),
                    ("create_namespace", mock.patch("mas.cli.rollback.app.createNamespace")),
                    ("prepare_pipelines_namespace", mock.patch("mas.cli.rollback.app.preparePipelinesNamespace")),
                    ("update_tekton_definitions", mock.patch("mas.cli.rollback.app.updateTektonDefinitions")),
                    ("launch_rollback_pipeline", mock.patch("mas.cli.rollback.app.launchRollbackPipeline")),
                    ("mixins_prompt", mock.patch("mas.cli.displayMixins.prompt")),
                    ("prompt_session_class", mock.patch("mas.cli.displayMixins.PromptSession")),
                    ("is_airgap_install", mock.patch("mas.cli.cli.isAirgapInstall")),
                    ("is_sno", mock.patch("mas.cli.cli.isSNO")),
                ]

                mocks = {}
                for name, patch in patches:
                    mocks[name] = stack.enter_context(patch)

                # Configure mock return values
                mocks["dynamic_client_class"].return_value = dynamic_client
                mocks["get_nodes"].return_value = [{"status": {"nodeInfo": {"architecture": self.config.architecture}}}]
                mocks["cli_prompt"].return_value = ""
                mocks["get_console_url"].return_value = "https://console.test.maximo.ibm.com"
                mocks["get_current_catalog"].return_value = {
                    "catalogId": self.config.installed_catalog_id,
                    "displayName": f"IBM Maximo Operator Catalog ({self.config.installed_catalog_id})",
                    "image": f"icr.io/cpopen/ibm-maximo-operator-catalog:{self.config.installed_catalog_id}",
                }
                mocks["list_mas_instances"].return_value = self.config.mas_instances
                mocks["install_pipelines"].return_value = True
                mocks["launch_rollback_pipeline"].return_value = "https://pipeline.test.maximo.ibm.com"
                mocks["is_airgap_install"].return_value = False
                mocks["is_sno"].return_value = False

                prompt_session_instance = MagicMock()
                mocks["prompt_session_class"].return_value = prompt_session_instance

                self.setup_prompt_handler(mocks["mixins_prompt"], prompt_session_instance)

                exception_raised = None

                try:
                    self.app = RollbackApp()
                    # Pre-set _dynClient so interactive connect() short-circuits
                    self.app._dynClient = dynamic_client
                    self.app.rollback(argv=self.config.argv)
                except SystemExit as e:
                    system_exit_raised = True
                    exit_code = e.code
                    if not self.config.expect_system_exit:
                        raise
                except Exception as e:
                    exception_raised = e
                    if self.config.expect_exception is None or not isinstance(e, self.config.expect_exception):
                        raise
                finally:
                    self.stop_watchdog()

                # Check watchdog timeout
                if self.test_failed["message"]:
                    raise TimeoutError(self.test_failed["message"])

                # Verify exception was raised if expected
                if self.config.expect_exception is not None and exception_raised is None:
                    raise AssertionError(f"Expected {self.config.expect_exception.__name__} to be raised but it was not")

                # Verify SystemExit was raised if expected
                if self.config.expect_system_exit and not system_exit_raised:
                    raise AssertionError("Expected SystemExit to be raised but it was not")

                # Verify exit code
                if self.config.expect_system_exit and self.config.expected_exit_code is not None:
                    if exit_code != self.config.expected_exit_code:
                        raise AssertionError(f"Expected exit code {self.config.expected_exit_code} but got {exit_code}")
                elif self.config.expect_system_exit and exit_code == 0:
                    raise AssertionError(f"Expected non-zero exit code but got {exit_code}")

                # Verify all prompts were matched
                if len(self.config.prompt_handlers) > 0:
                    self.prompt_tracker.verify_all_prompts_matched(allow_unmatched=self.config.expect_system_exit)


def run_rollback_test(tmpdir, config: RollbackTestConfig):
    """
    Convenience function to run a rollback test.

    Args:
        tmpdir: pytest tmpdir fixture
        config: Test configuration

    Raises:
        TimeoutError: If test times out
        AssertionError: If prompt verification or assertions fail
    """
    helper = RollbackTestHelper(tmpdir, config)
    helper.run_rollback_test()
