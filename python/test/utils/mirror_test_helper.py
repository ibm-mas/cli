#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import time
import threading
import yaml
from typing import Dict, Optional, List
from unittest import mock
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from mas.cli.mirror.app import MirrorApp


@dataclass
class MirrorTestConfig:
    """Configuration for a mirror test scenario."""

    mode: str  # m2m, m2d, or d2m
    catalog_version: str
    release: str
    target_registry: str = ""
    root_dir: str = "/tmp/mirror"
    packages: Dict[str, bool] = field(default_factory=dict)
    mock_oc_mirror_output: List[str] = field(default_factory=list)
    mock_image_count: int = 10
    expect_success: bool = True
    timeout_seconds: int = 30
    argv: Optional[list] = None
    authfile: Optional[str] = None
    dest_tls_verify: bool = True
    image_timeout: str = "20m"
    # Environment variables for auth file generation
    env_vars: Dict[str, str] = field(default_factory=dict)
    # Mock catalog data
    mock_catalog_data: Optional[Dict] = None
    # Whether config file should exist locally (vs download from GitHub)
    config_exists_locally: bool = True

    def __post_init__(self):
        """Set default argv if not provided."""
        if self.argv is None:
            self.argv = self._build_default_argv()

    def _build_default_argv(self) -> list:
        """Build default command line arguments from config."""
        args = [
            '--catalog', self.catalog_version,
            '--release', self.release,
            '--mode', self.mode,
            '--dir', self.root_dir,
        ]

        if self.target_registry:
            args.extend(['--target-registry', self.target_registry])

        if self.authfile:
            args.extend(['--authfile', self.authfile])

        if not self.dest_tls_verify:
            args.extend(['--dest-tls-verify', 'false'])

        if self.image_timeout != "20m":
            args.extend(['--image-timeout', self.image_timeout])

        # Add package flags
        for package, enabled in self.packages.items():
            if enabled:
                args.append(f'--{package}')

        return args


class MirrorTestHelper:
    """Helper class to run mirror tests with minimal code duplication."""

    def __init__(self, tmpdir, config: MirrorTestConfig):
        """
        Initialize the test helper.

        Args:
            tmpdir: pytest tmpdir fixture
            config: Test configuration
        """
        self.tmpdir = tmpdir
        self.config = config
        self.test_failed = {'failed': False, 'message': ''}
        self.last_activity_time = {'time': time.time()}
        self.watchdog_thread = None
        self.oc_mirror_call_count = 0

    def start_watchdog(self):
        """Start watchdog thread to detect hanging tests."""
        def watchdog():
            while not self.test_failed['failed']:
                time.sleep(1)
                elapsed = time.time() - self.last_activity_time['time']
                if elapsed > self.config.timeout_seconds:
                    self.test_failed['failed'] = True
                    self.test_failed['message'] = f"Test hung: No activity for {self.config.timeout_seconds}s"
                    break

        self.watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        self.watchdog_thread.start()

    def stop_watchdog(self):
        """Stop the watchdog thread."""
        self.test_failed['failed'] = True

    def update_activity(self):
        """Update last activity time to prevent watchdog timeout."""
        self.last_activity_time['time'] = time.time()

    def create_mock_subprocess(self):
        """
        Create a mock subprocess.Popen that simulates oc-mirror execution.

        Returns:
            Mock Popen object configured to return test output
        """
        mock_process = MagicMock()

        # Create mock stdout and stderr
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        # Configure readline to return mock output lines
        if self.config.mock_oc_mirror_output:
            # Add lines one by one, then empty string to signal EOF
            stdout_lines = [line + '\n' for line in self.config.mock_oc_mirror_output] + ['']
            mock_stdout.readline.side_effect = stdout_lines
            mock_stdout.fileno.return_value = 1
        else:
            # Default success output
            default_output = [
                f"{self.config.mock_image_count} / {self.config.mock_image_count} additional images mirrored successfully\n",
                ''
            ]
            mock_stdout.readline.side_effect = default_output
            mock_stdout.fileno.return_value = 1

        # Empty stderr
        mock_stderr.readline.side_effect = ['']
        mock_stderr.fileno.return_value = 2

        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_process.wait.return_value = 0 if self.config.expect_success else 1

        return mock_process

    def setup_mocks(self):
        """Setup all mock objects and return context managers."""
        # Mock prompt_toolkit's print_formatted_text to avoid Windows console issues
        mock_print = mock.patch('prompt_toolkit.shortcuts.utils.print_formatted_text')
        mock_print.start()

        # Create mock catalog data
        if self.config.mock_catalog_data is None:
            # Default catalog data structure
            self.config.mock_catalog_data = {
                'sls_version': '3.10.0',
                'tsm_version': '1.5.0',
                'mas_core_version': {'9.1.x': '9.1.0'},
                'mas_assist_version': {'9.1.x': '9.1.0'},
                'mas_iot_version': {'9.1.x': '9.1.0'},
                'mas_manage_version': {'9.1.x': '9.1.0'},
                'mas_monitor_version': {'9.1.x': '9.1.0'},
                'mas_predict_version': {'9.1.x': '9.1.0'},
                'mas_optimizer_version': {'9.1.x': '9.1.0'},
                'mas_visualinspection_version': {'9.1.x': '9.1.0'},
                'mas_facilities_version': {'9.1.x': '9.1.0'},
                'db2u_version': '11.5.9.0+123',
                'amlen_extras_version': '1.0.0',
                'aiservice_version': {'9.1.x': '1.0.0'},
                'dd_version': '1.0.0',
                'mongo_extras_version_default': '6.0.0',
            }

        # Mock YAML config file content
        mock_yaml_content = {
            'mirror': {
                'additionalImages': [
                    {'name': f'image{i}'} for i in range(self.config.mock_image_count)
                ]
            }
        }

        return mock_yaml_content

    def run_mirror_test(self):
        """
        Run the mirror test with all mocks configured.

        Raises:
            TimeoutError: If test times out
            AssertionError: If validation fails
        """
        self.start_watchdog()

        mock_yaml_content = self.setup_mocks()

        # Create a custom open mock that only affects YAML config files
        original_open = open

        def selective_open(file, mode='r', *args, **kwargs):
            # Only mock YAML config files, let everything else (including log files) use real open
            if isinstance(file, str) and ('.yaml' in file or 'auth.json' in file):
                if mode == 'r' or 'r' in mode:
                    # Return mock file with YAML content for reading
                    from io import StringIO
                    return StringIO(yaml.dump(mock_yaml_content))
                else:
                    # For writing (auth.json), return a mock that accepts writes
                    mock_file = MagicMock()
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=False)
                    return mock_file
            # Use original open for everything else (log files, etc.)
            return original_open(file, mode, *args, **kwargs)

        with (
            # Mock kubectl check in BaseApp.__init__ (which is imported from shutil)
            mock.patch('mas.cli.cli.which') as mock_kubectl_which,
            # Mock oc-mirror availability
            mock.patch('mas.cli.mirror.app.shutil.which') as mock_which,
            mock.patch('mas.cli.mirror.app.subprocess.Popen') as mock_popen,
            mock.patch('mas.cli.mirror.app.getCatalog') as mock_get_catalog,
            mock.patch('builtins.open', side_effect=selective_open) as mock_file,  # noqa: F841
            mock.patch('mas.cli.mirror.app.path.exists') as mock_path_exists,
            mock.patch('mas.cli.mirror.app.makedirs') as mock_makedirs,  # noqa: F841
            mock.patch('mas.cli.mirror.app.urllib.request.urlopen') as mock_urlopen,
            mock.patch('mas.cli.mirror.app.environ', self.config.env_vars) as mock_environ,  # noqa: F841
        ):
            # Configure kubectl mock (for BaseApp.__init__)
            mock_kubectl_which.return_value = '/usr/local/bin/kubectl'
            # Configure oc-mirror mock
            mock_which.return_value = '/usr/local/bin/oc-mirror'
            mock_get_catalog.return_value = self.config.mock_catalog_data

            # Configure path.exists based on config
            if self.config.authfile:
                # If authfile is provided, it should exist
                mock_path_exists.side_effect = lambda p: self.config.authfile in p or self.config.config_exists_locally
            else:
                # Config files exist locally, auth file will be generated
                mock_path_exists.return_value = self.config.config_exists_locally

            # Configure subprocess mock
            def popen_side_effect(*args, **kwargs):
                self.update_activity()
                self.oc_mirror_call_count += 1
                return self.create_mock_subprocess()

            mock_popen.side_effect = popen_side_effect

            # Configure urllib for GitHub downloads (if needed)
            if not self.config.config_exists_locally:
                mock_response = MagicMock()
                mock_response.read.return_value = yaml.dump(mock_yaml_content).encode()
                mock_urlopen.return_value.__enter__.return_value = mock_response

            try:
                # Run the mirror command
                app = MirrorApp()
                app.mirror(argv=self.config.argv)

                # Update activity after completion
                self.update_activity()

            finally:
                self.stop_watchdog()

            # Check if test timed out
            if self.test_failed['message']:
                raise TimeoutError(self.test_failed['message'])

            # Verify oc-mirror was called
            assert self.oc_mirror_call_count > 0, "oc-mirror command was not executed"

            # Verify oc-mirror was called with correct arguments
            if mock_popen.called:
                call_args = mock_popen.call_args[0][0]  # Get the command list
                assert 'oc-mirror' in call_args[0] or call_args[0].endswith('oc-mirror'), \
                    f"Expected oc-mirror in command, got: {call_args[0]}"
                assert '--v2' in call_args, "Expected --v2 flag"
                assert '--config' in call_args, "Expected --config flag"
                assert self.config.mode in ['m2m', 'm2d', 'd2m'], f"Invalid mode: {self.config.mode}"

                # Verify mode-specific arguments
                if self.config.mode == 'm2m':
                    assert f"docker://{self.config.target_registry}" in call_args, \
                        "Expected target registry in m2m mode"
                elif self.config.mode == 'm2d':
                    assert any('file://' in arg for arg in call_args), \
                        "Expected file:// destination in m2d mode"
                elif self.config.mode == 'd2m':
                    assert '--from' in call_args, "Expected --from flag in d2m mode"
                    assert f"docker://{self.config.target_registry}" in call_args, \
                        "Expected target registry in d2m mode"


def run_mirror_test(tmpdir, config: MirrorTestConfig):
    """
    Convenience function to run a mirror test.

    Args:
        tmpdir: pytest tmpdir fixture
        config: Test configuration

    Raises:
        TimeoutError: If test times out
        AssertionError: If validation fails
    """
    helper = MirrorTestHelper(tmpdir, config)
    helper.run_mirror_test()


# Made with Bob
