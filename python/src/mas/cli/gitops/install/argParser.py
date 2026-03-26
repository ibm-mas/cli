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
Dynamic Argument Parser for GitOps Install

This module provides functionality to build an argparse.ArgumentParser dynamically
from bash function help text. It merges arguments from multiple functions and
handles deduplication.
"""

import logging
import argparse
import os
from typing import Dict, List, Any, Optional
from .argBuilder import BashFunctionArgumentExtractor, Argument

logger = logging.getLogger(__name__)


class GitOpsArgumentParser:
    """Build argument parser dynamically from bash functions"""

    def __init__(self, functions_dir: Optional[str] = None):
        """
        Initialize the argument parser.

        Args:
            functions_dir: Directory containing bash functions. If None, will auto-detect.
        """
        self.extractor = BashFunctionArgumentExtractor(functions_dir)
        self.parser: Optional[argparse.ArgumentParser] = None

    def build_parser(self) -> argparse.ArgumentParser:
        """
        Build argument parser from all gitops functions.

        Returns:
            Configured ArgumentParser instance
        """
        if self.parser is not None:
            return self.parser

        # Create the parser
        self.parser = argparse.ArgumentParser(
            prog='mas gitops-install',
            description='Install IBM Maximo Application Suite using GitOps',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic installation
  mas gitops-install \\
    --account-id myaccount \\
    --cluster-id mycluster \\
    --mas-instance-id inst1 \\
    --mongodb-provider aws \\
    --sls-channel 3.x \\
    --mas-channel 9.0.x

  # Installation with custom GitOps repository
  mas gitops-install \\
    --account-id myaccount \\
    --cluster-id mycluster \\
    --mas-instance-id inst1 \\
    --github-org myorg \\
    --github-repo myrepo \\
    --gitops-repo-token-secret $GITHUB_PAT

For more information, see: https://ibm-mas.github.io/cli/
"""
        )

        # Get unique arguments from all functions (deduplicated by long_option)
        unique_args = self.extractor.get_unique_arguments()

        # Add per-app arguments (also deduplicated by long_option)
        per_app_args = self.extractor.get_per_app_arguments()

        # Merge per-app arguments, avoiding duplicates by long_option
        for long_option, arg in per_app_args.items():
            if long_option not in unique_args:
                unique_args[long_option] = arg

        logger.info(f"Total unique arguments available for gitops-install: {len(unique_args)}")

        # Debug: Log all unique arguments
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("All unique arguments:")
            for long_option, arg in sorted(unique_args.items()):
                short_opt = f"{arg.short_option}/" if arg.short_option else ""
                logger.debug(f"  {short_opt}{arg.long_option} -> {arg.env_var}")

        # Group arguments by category
        grouped_args = self._group_arguments(unique_args)

        # Add arguments to parser by group
        for group_name, args in grouped_args.items():
            if args:
                group = self.parser.add_argument_group(group_name)
                for arg in args:
                    self._add_argument_to_group(group, arg)

        return self.parser

    def _group_arguments(self, unique_args: Dict[str, Argument]) -> Dict[str, List[Argument]]:
        """
        Group arguments by category for better organization.

        Args:
            unique_args: Dictionary of unique arguments (keyed by long_option)

        Returns:
            Dictionary mapping group names to lists of arguments
        """
        groups: Dict[str, List[Argument]] = {
            'Required Arguments': [],
            'GitOps Configuration': [],
            'MAS Configuration': [],
            'Dependencies': [],
            'Cloud Provider': [],
            'Storage': [],
            'Security': [],
            'Advanced Options': []
        }

        for long_option, arg in unique_args.items():
            # Categorize based on env_var prefix or content
            env_var = arg.env_var
            if arg.required:
                groups['Required Arguments'].append(arg)
            elif env_var.startswith('GITHUB_') or env_var.startswith('GIT_') or env_var == 'GITOPS_WORKING_DIR':
                groups['GitOps Configuration'].append(arg)
            elif env_var.startswith('MAS_') or env_var.startswith('SLS_'):
                groups['MAS Configuration'].append(arg)
            elif (env_var.startswith('MONGO') or env_var.startswith('KAFKA') or
                  env_var.startswith('COS_') or env_var.startswith('DB2_') or
                  env_var.startswith('EFS_')):
                groups['Dependencies'].append(arg)
            elif (env_var.startswith('AWS_') or env_var.startswith('IBMCLOUD_') or
                  env_var.startswith('VPC_') or env_var == 'CLOUD_PROVIDER'):
                groups['Cloud Provider'].append(arg)
            elif env_var.startswith('STORAGE_'):
                groups['Storage'].append(arg)
            elif (env_var.startswith('ICR_') or env_var.startswith('SM_') or
                  env_var.startswith('AVP_') or env_var.startswith('LDAP_') or
                  env_var.startswith('SMTP_')):
                groups['Security'].append(arg)
            else:
                groups['Advanced Options'].append(arg)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def _add_argument_to_group(self, group: argparse._ArgumentGroup, arg: Argument):
        """
        Add an argument to an argument group.

        Args:
            group: The argument group to add to
            arg: The argument to add
        """
        # Build the argument flags
        flags = []
        if arg.short_option:
            flags.append(arg.short_option)
        flags.append(arg.long_option)

        # Determine the destination name (convert --long-option to long_option)
        dest = arg.long_option.lstrip('-').replace('-', '_')

        # Add the argument
        group.add_argument(
            *flags,
            dest=dest,
            help=f"{arg.description} (env: {arg.env_var})",
            required=arg.required,
            metavar=arg.env_var
        )

    def parse_args(self, argv: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Parse command-line arguments and merge with environment variables.

        Args:
            argv: Command-line arguments (default: sys.argv)

        Returns:
            Dictionary of parsed arguments
        """
        if self.parser is None:
            self.build_parser()

        # Parse arguments (parser is guaranteed to be set by build_parser)
        assert self.parser is not None, "Parser should be initialized by build_parser()"
        args = self.parser.parse_args(argv)

        # Convert to dictionary
        params = vars(args)

        # Merge with environment variables (CLI args take precedence)
        # Get unique arguments to know which env vars to check
        unique_args = self.extractor.get_unique_arguments()

        for long_option, arg in unique_args.items():
            dest = arg.long_option.lstrip('-').replace('-', '_')
            # If CLI argument not provided, check environment variable
            if params.get(dest) is None and arg.env_var in os.environ:
                params[dest] = os.environ[arg.env_var]
                logger.debug(f"Using environment variable {arg.env_var} for {dest}")

        # Convert parameter names to match executor expectations
        # The executor expects keys like 'mas_instance_id', not 'mas-instance-id'
        # This is already handled by the dest parameter above

        return params

    def validate_required_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate that all required parameters are provided.

        Args:
            params: Dictionary of parameters

        Returns:
            List of missing required parameter names (empty if all present)
        """
        missing = []
        unique_args = self.extractor.get_unique_arguments()

        for long_option, arg in unique_args.items():
            if arg.required:
                dest = arg.long_option.lstrip('-').replace('-', '_')
                if not params.get(dest):
                    missing.append(arg.long_option)

        return missing
