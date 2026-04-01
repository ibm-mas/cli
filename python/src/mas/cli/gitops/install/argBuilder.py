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
Bash Function Argument Extractor

This module provides functionality to dynamically extract command-line arguments
from bash function help text. It scans gitops_* functions and parses their help
output to build a comprehensive list of available arguments.
"""

import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Argument:
    """Represents a command-line argument extracted from bash function help"""
    short_option: Optional[str]
    long_option: str
    env_var: str
    description: str
    required: bool = False
    function_name: str = ""
    is_flag: bool = False  # True if this is a boolean flag (action='store_true')


class BashFunctionArgumentExtractor:
    """Extract arguments from bash function source code"""

    def __init__(self, functions_dir: Optional[str] = None):
        """
        Initialize the argument extractor.

        Args:
            functions_dir: Path to the directory containing bash functions (e.g., '/mascli/functions')
        """
        self.functions_dir = functions_dir or "/mascli/functions"
        self.functions_cache: Dict[str, List[Argument]] = {}

    def get_gitops_functions(self) -> List[str]:
        """
        Get list of all gitops_* functions by scanning the functions directory.

        Returns:
            List of function names (with underscores, e.g., 'gitops_suite')
        """
        try:
            import os
            functions = []

            if not os.path.exists(self.functions_dir):
                logger.warning(f"Functions directory not found: {self.functions_dir}")
                return []

            # List all files in the functions directory
            for filename in os.listdir(self.functions_dir):
                filepath = os.path.join(self.functions_dir, filename)

                # Skip directories and non-gitops files
                if not os.path.isfile(filepath):
                    continue
                if not filename.startswith('gitops_'):
                    continue

                functions.append(filename)

            logger.info(f"Found {len(functions)} gitops functions")
            return sorted(functions)

        except Exception as e:
            logger.error(f"Error listing gitops functions: {e}", exc_info=True)
            return []

    def extract_arguments(self, function_name: str) -> List[Argument]:
        """
        Parse bash function source code to extract arguments from the case statement.

        Args:
            function_name: Name of bash function (e.g., 'gitops_suite')

        Returns:
            List of Argument objects with name, env_var, description, required
        """
        # Check cache first
        if function_name in self.functions_cache:
            return self.functions_cache[function_name]

        try:
            import os
            filepath = os.path.join(self.functions_dir, function_name)

            if not os.path.exists(filepath):
                logger.warning(f"Function file not found: {filepath}")
                return []

            # Read the bash function source code
            with open(filepath, 'r') as f:
                source_code = f.read()

            arguments = self._parse_bash_function(source_code, function_name)

            # Cache the results
            self.functions_cache[function_name] = arguments

            logger.debug(f"Extracted {len(arguments)} arguments from {function_name}")
            return arguments

        except Exception as e:
            logger.error(f"Error extracting arguments from {function_name}: {e}", exc_info=True)
            return []

    def _parse_bash_function(self, source_code: str, function_name: str) -> List[Argument]:
        """
        Parse bash function source code to extract arguments from the case statement.

        Args:
            source_code: The bash function source code
            function_name: Name of the function being parsed

        Returns:
            List of Argument objects
        """
        arguments = []

        # Find the while loop with case statement
        # Pattern: while [[ $# -gt 0 ]] ... case $key in ... esac ... done

        # Split into lines for processing
        lines = source_code.split('\n')

        in_while_loop = False
        in_case_statement = False
        current_env_var = None

        for i, line in enumerate(lines):
            # Detect start of while loop
            if 'while [[ $# -gt 0 ]]' in line or 'while [[ $# -gt 0' in line:
                in_while_loop = True
                continue

            # Detect end of while loop
            if in_while_loop and re.match(r'^\s*done\s*$', line):
                in_while_loop = False
                continue

            if not in_while_loop:
                continue

            # Detect case statement
            if 'case $key in' in line or 'case "$key" in' in line:
                in_case_statement = True
                continue

            # Detect end of case statement
            if in_case_statement and re.match(r'^\s*esac\s*$', line):
                in_case_statement = False
                continue

            if not in_case_statement:
                continue

            # Match case option lines: -d|--dir) or --some-option)
            # Pattern 1: Short and long option
            match = re.match(r'^\s*(-[a-zA-Z])\s*\|\s*(--[a-z0-9-]+)\s*\)', line)
            if match:
                short_opt = match.group(1)
                long_opt = match.group(2)

                # Look ahead for the export statement
                for j in range(i + 1, min(i + 5, len(lines))):
                    # Check for flag pattern: export VAR=true or export VAR="true"
                    flag_match = re.search(r'export\s+([A-Z_][A-Z0-9_]*)\s*=\s*["\']?true["\']?\s*$', lines[j])
                    if flag_match:
                        current_env_var = flag_match.group(1)
                        arguments.append(Argument(
                            short_option=short_opt,
                            long_option=long_opt,
                            env_var=current_env_var,
                            description="",
                            required=False,
                            function_name=function_name,
                            is_flag=True
                        ))
                        break

                    # Check for regular argument pattern: export VAR=$1
                    export_match = re.search(r'export\s+([A-Z_][A-Z0-9_]*)\s*=', lines[j])
                    if export_match and not flag_match:
                        current_env_var = export_match.group(1)
                        arguments.append(Argument(
                            short_option=short_opt,
                            long_option=long_opt,
                            env_var=current_env_var,
                            description="",
                            required=False,
                            function_name=function_name,
                            is_flag=False
                        ))
                        break
                    # Stop at next case or end of block
                    if ';;' in lines[j]:
                        break

                current_env_var = None
                continue

            # Pattern 2: Long option only
            match = re.match(r'^\s*(--[a-z0-9-]+)\s*\)', line)
            if match:
                long_opt = match.group(1)
                # Look ahead for the export statement
                for j in range(i + 1, min(i + 5, len(lines))):
                    # Check for flag pattern: export VAR=true or export VAR="true"
                    flag_match = re.search(r'export\s+([A-Z_][A-Z0-9_]*)\s*=\s*["\']?true["\']?\s*$', lines[j])
                    if flag_match:
                        current_env_var = flag_match.group(1)
                        arguments.append(Argument(
                            short_option=None,
                            long_option=long_opt,
                            env_var=current_env_var,
                            description="",
                            required=False,
                            function_name=function_name,
                            is_flag=True
                        ))
                        break

                    # Check for regular argument pattern: export VAR=$1
                    export_match = re.search(r'export\s+([A-Z_][A-Z0-9_]*)\s*=', lines[j])
                    if export_match and not flag_match:
                        current_env_var = export_match.group(1)
                        arguments.append(Argument(
                            short_option=None,
                            long_option=long_opt,
                            env_var=current_env_var,
                            description="",
                            required=False,
                            function_name=function_name,
                            is_flag=False
                        ))
                        break
                    # Stop at next case or end of block
                    if ';;' in lines[j]:
                        break

                current_env_var = None
                continue

        return arguments

    def extract_all_arguments(self) -> Dict[str, List[Argument]]:
        """
        Extract arguments from all gitops functions.

        Returns:
            Dictionary mapping function names to their arguments
        """
        all_arguments = {}
        functions = self.get_gitops_functions()

        for function_name in functions:
            arguments = self.extract_arguments(function_name)
            if arguments:
                all_arguments[function_name] = arguments

        return all_arguments

    def get_unique_arguments(self) -> Dict[str, Argument]:
        """
        Get unique arguments across all functions, deduplicated by long_option and short_option.

        When the same argument appears in multiple functions, we keep the first
        occurrence and merge metadata (required status, description).

        Returns:
            Dictionary mapping long_option to Argument object
        """
        unique_args: Dict[str, Argument] = {}
        used_short_options: set = set()
        all_args = self.extract_all_arguments()

        for function_name, arguments in all_args.items():
            for arg in arguments:
                # Use long_option as the key for deduplication (this is what argparse cares about)
                if arg.long_option not in unique_args:
                    # Check if short option is already used by another argument
                    if arg.short_option and arg.short_option in used_short_options:
                        logger.warning(f"Short option {arg.short_option} for {arg.long_option} conflicts with another argument, removing short option")
                        # Create a new Argument without the short option
                        arg = Argument(
                            short_option=None,
                            long_option=arg.long_option,
                            env_var=arg.env_var,
                            description=arg.description,
                            required=arg.required,
                            function_name=arg.function_name,
                            is_flag=arg.is_flag
                        )

                    unique_args[arg.long_option] = arg
                    if arg.short_option:
                        used_short_options.add(arg.short_option)
                else:
                    # If argument already exists, mark as required if any function requires it
                    if arg.required:
                        unique_args[arg.long_option].required = True
                    # Use longer description if available
                    if len(arg.description) > len(unique_args[arg.long_option].description):
                        unique_args[arg.long_option].description = arg.description

        logger.info(f"Extracted {len(unique_args)} unique arguments from bash functions")
        return unique_args

    def get_per_app_arguments(self) -> Dict[str, Argument]:
        """
        Generate per-app arguments for MAS applications.

        These arguments are not extracted from bash functions but are dynamically
        generated to support per-app configuration (e.g., --mas-app-channel-manage).

        Returns:
            Dictionary mapping long_option to Argument object for per-app parameters
        """
        per_app_args: Dict[str, Argument] = {}

        # List of supported MAS applications
        apps = ['manage', 'iot', 'monitor', 'predict', 'assist', 'optimizer',
                'visualinspection', 'facilities', 'health']

        # Define per-app parameter templates
        # Format: (param_suffix, env_var_suffix, description, is_flag)
        param_templates = [
            # App installation parameters
            ('id', 'ID', 'Enable installation of {app} application', True),
            ('channel', 'CHANNEL', 'Channel for {app} application', False),
            ('catalog-source', 'CATALOG_SOURCE', 'Catalog source for {app} application', False),
            ('api-version', 'API_VERSION', 'API version for {app} application CR', False),
            ('kind', 'KIND', 'Kind for {app} application CR', False),
            ('spec-yaml', 'SPEC_YAML', 'Spec YAML file for {app} application', False),

            # App workspace configuration parameters
            ('appws-api-version', 'APPWS_API_VERSION', 'Workspace API version for {app} application', False),
            ('appws-kind', 'APPWS_KIND', 'Workspace Kind for {app} application', False),
            ('appws-spec-yaml', 'APPWS_SPEC_YAML', 'Workspace spec YAML file for {app} application', False),
        ]

        # DB2/JDBC parameters (only for apps that need them: manage, iot, facilities)
        db2_apps = ['manage', 'iot', 'facilities']
        db2_param_templates = [
            ('db2-channel', 'DB2_CHANNEL', 'DB2 channel for {app} application', False),
            ('db2-version', 'DB2_VERSION', 'DB2 version for {app} application', False),
            ('db2-meta-storage-class', 'DB2_META_STORAGE_CLASS', 'DB2 meta storage class for {app}', False),
            ('db2-data-storage-class', 'DB2_DATA_STORAGE_CLASS', 'DB2 data storage class for {app}', False),
            ('db2-logs-storage-class', 'DB2_LOGS_STORAGE_CLASS', 'DB2 logs storage class for {app}', False),
            ('db2-backup-storage-class', 'DB2_BACKUP_STORAGE_CLASS', 'DB2 backup storage class for {app}', False),
            ('db2-instance-registry-yaml', 'DB2_INSTANCE_REGISTRY_YAML', 'DB2 instance registry YAML for {app}', False),
            ('db2-instance-dbm-config-yaml', 'DB2_INSTANCE_DBM_CONFIG_YAML', 'DB2 instance DBM config YAML for {app}', False),
            ('db2-database-db-config-yaml', 'DB2_DATABASE_DB_CONFIG_YAML', 'DB2 database config YAML for {app}', False),
            ('jdbc-instance-name', 'JDBC_INSTANCE_NAME', 'JDBC instance name for {app}', False),
        ]

        # Generate arguments for each app
        for app in apps:
            app_upper = app.upper().replace('-', '_')

            # Generate standard app parameters
            for param_suffix, env_suffix, desc_template, is_flag in param_templates:
                long_option = f'--mas-app-{param_suffix}-{app}'
                env_var = f'MAS_APP_{env_suffix}_{app_upper}'
                description = desc_template.format(app=app)

                per_app_args[long_option] = Argument(
                    short_option=None,
                    long_option=long_option,
                    env_var=env_var,
                    description=description,
                    required=False,
                    function_name='gitops_install',
                    is_flag=is_flag
                )

            # Generate DB2/JDBC parameters for applicable apps
            if app in db2_apps:
                for param_suffix, env_suffix, desc_template, is_flag in db2_param_templates:
                    long_option = f'--{param_suffix}-{app}'
                    env_var = f'{env_suffix}_{app_upper}'
                    description = desc_template.format(app=app)

                    per_app_args[long_option] = Argument(
                        short_option=None,
                        long_option=long_option,
                        env_var=env_var,
                        description=description,
                        required=False,
                        function_name='gitops_install',
                        is_flag=is_flag
                    )

        logger.info(f"Generated {len(per_app_args)} per-app arguments")
        return per_app_args
