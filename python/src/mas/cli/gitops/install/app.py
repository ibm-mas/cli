# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
GitOps Install Application

This module provides the main application class for the mas gitops-install command.
It is a non-interactive command that orchestrates GitOps-based MAS installations.
"""

import logging
import sys
from typing import List, Optional
from prompt_toolkit import print_formatted_text, HTML
from halo import Halo

from ...cli import BaseApp
from .argParser import GitOpsArgumentParser
from .executor import GitOpsInstallExecutor
from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions
from mas.devops.ocp import connect

logger = logging.getLogger(__name__)


class GitOpsInstallApp(BaseApp):
    """
    Main application class for GitOps-based MAS installation.

    This is a non-interactive command that orchestrates GitOps functions
    based on provided command-line arguments.
    """

    def __init__(self):
        """Initialize the GitOps install application."""
        # Initialize BaseApp to set up logging
        super().__init__()

        # Pass the functions directory path to the argument parser
        # The path is relative to the CLI root directory
        self.arg_parser = GitOpsArgumentParser(functions_dir="/mascli/functions")
        self.executor: Optional[GitOpsInstallExecutor] = None
        self.dynamicClient = None

    def install(self, argv: List[str]) -> int:
        """
        Main entry point for gitops-install command.

        Args:
            argv: Command-line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        logger.debug(">>> GitOpsInstallApp.install")
        logger.info("Starting GitOps installation")

        try:
            # Print header
            self._print_header()

            # Parse arguments with spinner (this can take time as it scans bash functions)
            logger.debug("Parsing command-line arguments")
            spinner = Halo(text='Computing available arguments from GitOps functions...', spinner='dots')
            spinner.start()
            try:
                self.params = self.arg_parser.parse_args(argv)
                spinner.succeed('Arguments computed successfully')
                logger.info(f"Parsed {len(self.params)} parameters from command line and environment")
            except SystemExit:
                # argparse calls sys.exit() for --help or errors
                spinner.stop()
                raise
            except Exception:
                spinner.fail('Failed to compute arguments')
                raise

            # Validate configuration
            logger.info("Validating configuration")
            if not self._validate_configuration():
                logger.error("Configuration validation failed")
                return 1

            logger.info("Configuration validation successful")

            # Connect to OpenShift cluster if install-pipelines-operator flag is set
            if self.params.get('install_pipelines_operator'):
                logger.info("Connecting to OpenShift cluster for pipelines installation")
                self.dynamicClient = connect()

            # Execute installation
            logger.info("Starting installation execution")
            if self._execute_installation():
                # Install OpenShift Pipelines if requested
                if self.params.get('install_pipelines_operator'):
                    logger.info("Installing OpenShift Pipelines Operator")
                    pipelinesNamespace = f"mas-{self.params.get('mas_instance_id')}-pipelines"
                    with Halo(text='Validating OpenShift Pipelines installation', spinner='dots') as h:
                        if installOpenShiftPipelines(self.dynamicClient, self.params.get("storage_class_rwx")):
                            h.stop_and_persist(symbol='✔', text="OpenShift Pipelines Operator is installed and ready to use")
                        else:
                            h.stop_and_persist(symbol='✖', text="OpenShift Pipelines Operator installation failed")
                            logger.error("OpenShift Pipelines installation failed")
                            self._print_failure()
                            logger.debug("<<< GitOpsInstallApp.install (pipelines installation failure)")
                            return 1

                    with Halo(text=f'Installing latest Tekton definitions (v{self.version})', spinner=self.spinner) as h:
                        updateTektonDefinitions(pipelinesNamespace, self.tektonDefsPath)
                        h.stop_and_persist(symbol=self.successIcon, text=f"Latest Tekton definitions are installed (v{self.version})")

                self._print_success()
                logger.info("GitOps installation completed successfully")
                logger.debug("<<< GitOpsInstallApp.install (success)")
                return 0
            else:
                self._print_failure()
                logger.error("GitOps installation failed")
                logger.debug("<<< GitOpsInstallApp.install (failure)")
                return 1

        except KeyboardInterrupt:
            logger.warning("Installation cancelled by user")
            print_formatted_text(HTML("\n<Red>Installation cancelled by user</Red>"))
            logger.debug("<<< GitOpsInstallApp.install (cancelled)")
            return 130
        except Exception as e:
            logger.error(f"Unexpected error during GitOps installation: {e}", exc_info=True)
            print_formatted_text(HTML(f"\n<Red>Error: {e}</Red>"))
            logger.debug("<<< GitOpsInstallApp.install (exception)")
            return 1

    def _print_header(self):
        """Print the application header."""
        print_formatted_text(HTML("""
<b><u>IBM Maximo Application Suite - GitOps Install</u></b>

This command performs a non-interactive GitOps-based installation of MAS.
All configuration must be provided via command-line arguments or environment variables.
"""))

    def _validate_configuration(self) -> bool:
        """
        Validate that required parameters are provided.

        Returns:
            True if configuration is valid, False otherwise
        """
        logger.debug(">>> GitOpsInstallApp._validate_configuration")

        # Check for required parameters
        missing = self.arg_parser.validate_required_params(self.params)

        if missing:
            logger.error("Missing required parameters for GitOps installation")
            for param in missing:
                logger.error(f"  Missing parameter: {param}")
            print_formatted_text(HTML("<Red><b>Error: Missing required parameters:</b></Red>"))
            for param in missing:
                print_formatted_text(HTML(f"  <Red>- {param}</Red>"))
            print_formatted_text(HTML("\n<Yellow>Use --help to see all available options</Yellow>"))
            logger.debug("<<< GitOpsInstallApp._validate_configuration (validation failed)")
            return False

        # Validate specific parameter combinations
        if not self._validate_parameter_combinations():
            logger.debug("<<< GitOpsInstallApp._validate_configuration (parameter combination validation failed)")
            return False

        # Log configuration summary
        self._log_configuration_summary()

        logger.debug("<<< GitOpsInstallApp._validate_configuration (success)")
        return True

    def _validate_parameter_combinations(self) -> bool:
        """
        Validate parameter combinations and dependencies.

        Returns:
            True if valid, False otherwise
        """
        logger.debug(">>> GitOpsInstallApp._validate_parameter_combinations")

        # If DNS provider is specified, validate related parameters
        dns_provider = self.params.get('dns_provider')
        if dns_provider:
            logger.debug(f"Validating DNS provider: {dns_provider}")
            if dns_provider not in ['cloudflare', 'cis', 'route53']:
                logger.error(f"Invalid DNS provider '{dns_provider}'. Must be one of: cloudflare, cis, route53")
                print_formatted_text(HTML(
                    f"<Red>Error: Invalid DNS provider '{dns_provider}'. "
                    f"Must be one of: cloudflare, cis, route53</Red>"
                ))
                logger.debug("<<< GitOpsInstallApp._validate_parameter_combinations (DNS provider validation failed)")
                return False

        # If MongoDB action is specified, validate provider
        if self.params.get('mongodb_action'):
            logger.debug(f"MongoDB action specified: {self.params.get('mongodb_action')}")
            if not self.params.get('mongo_provider'):
                logger.error("mongo_provider is required when mongodb_action is specified")
                print_formatted_text(HTML(
                    "<Red>Error: --mongo-provider is required when --mongodb-action is specified</Red>"
                ))
                logger.debug("<<< GitOpsInstallApp._validate_parameter_combinations (MongoDB validation failed)")
                return False
            logger.debug(f"MongoDB provider: {self.params.get('mongo_provider')}")

        # If Kafka action is specified, validate provider
        if self.params.get('kafka_action'):
            logger.debug(f"Kafka action specified: {self.params.get('kafka_action')}")
            if not self.params.get('kafka_provider'):
                logger.error("kafka_provider is required when kafka_action is specified")
                print_formatted_text(HTML(
                    "<Red>Error: --kafka-provider is required when --kafka-action is specified</Red>"
                ))
                logger.debug("<<< GitOpsInstallApp._validate_parameter_combinations (Kafka validation failed)")
                return False
            logger.debug(f"Kafka provider: {self.params.get('kafka_provider')}")

        logger.debug("<<< GitOpsInstallApp._validate_parameter_combinations (success)")
        return True

    def _log_configuration_summary(self):
        """Log a summary of the configuration."""
        logger.info("=" * 80)
        logger.info("GitOps Installation Configuration Summary")
        logger.info("=" * 80)

        # Log key parameters
        key_params = [
            'account_id', 'cluster_id', 'mas_instance_id', 'mas_workspace_id',
            'mas_channel', 'sls_channel', 'mongodb_action', 'kafka_action',
            'cos_action', 'github_org', 'github_repo'
        ]

        for param in key_params:
            value = self.params.get(param)
            if value:
                # Mask sensitive values
                if 'password' in param.lower() or 'token' in param.lower() or 'key' in param.lower():
                    value = '***REDACTED***'
                logger.info(f"  {param}: {value}")

        logger.info("=" * 80)

    def _execute_installation(self) -> bool:
        """
        Execute GitOps installation using executor.

        Returns:
            True if successful, False otherwise
        """
        logger.debug(">>> GitOpsInstallApp._execute_installation")

        try:
            # Create executor with parameters
            logger.info("Creating GitOps installation executor")
            self.executor = GitOpsInstallExecutor(
                params=self.params,
                spinner='dots',
                success_icon='✔',
                failure_icon='✖'
            )

            # Execute installation
            logger.info("Executing GitOps installation pipeline")
            result = self.executor.execute()

            if result:
                logger.info("Installation execution completed successfully")
            else:
                logger.error("Installation execution failed")

            logger.debug("<<< GitOpsInstallApp._execute_installation")
            return result

        except Exception as e:
            logger.error(f"Error during installation execution: {e}", exc_info=True)
            print_formatted_text(HTML(f"<Red>Installation failed: {e}</Red>"))
            logger.debug("<<< GitOpsInstallApp._execute_installation (exception)")
            return False

    def _print_success(self):
        """Print success message."""
        print_formatted_text(HTML("""
<Green><b>✔ GitOps Installation Completed Successfully!</b></Green>

Your MAS instance has been configured via GitOps.
Check your GitOps repository for the generated configuration files.
"""))

    def _print_failure(self):
        """Print failure message."""
        print_formatted_text(HTML("""
<Red><b>✖ GitOps Installation Failed</b></Red>

Please check the logs for more details.
You can retry the installation after fixing any issues.
"""))


def main(argv: Optional[List[str]] = None):
    """
    Main entry point for the gitops-install command.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])
    """
    if argv is None:
        argv = sys.argv[1:]

    app = GitOpsInstallApp()
    sys.exit(app.install(argv))


if __name__ == '__main__':
    main()
