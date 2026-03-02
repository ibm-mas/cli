# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import argparse
import sys

from ..cli import getHelpFormatter


class UpdateArgumentParser(argparse.ArgumentParser):
    """Custom argument parser that validates --catalog requirement"""

    def format_usage(self):
        """Custom usage message showing different modes"""
        prog = self.prog
        return (
            f"Usage (non-interactive mode):\n"
            f"  {prog} -c MAS_CATALOG_VERSION [--db2-namespace DB2_NAMESPACE]\n"
            f"                  [--mongodb-namespace MONGODB_NAMESPACE] [--mongodb-v5-upgrade]\n"
            f"                  [--mongodb-v6-upgrade] [--mongodb-v7-upgrade] [--mongodb-v8-upgrade]\n"
            f"                  [--kafka-namespace KAFKA_NAMESPACE] [--kafka-provider {{redhat,strimzi}}]\n"
            f"                  [--artifactory-username ARTIFACTORY_USERNAME]\n"
            f"                  [--artifactory-token ARTIFACTORY_TOKEN] [--dev-mode]\n"
            f"                  [--cp4d-version CPD_PRODUCT_VERSION] [--no-confirm] [--skip-pre-check]\n"
            f"\n"
            f"Usage (interactive mode):\n"
            f"  {prog}\n"
            f"\n"
            f"Usage (help):\n"
            f"  {prog} -h\n"
        )

    def format_help(self):
        """Override format_help to use our custom usage format"""
        formatter = self._get_formatter()

        # Add description
        formatter.add_text(self.description)

        # Add custom usage
        formatter.add_text(self.format_usage())

        # Add argument groups
        for actionGroup in self._action_groups:
            formatter.start_section(actionGroup.title)
            formatter.add_text(actionGroup.description)
            formatter.add_arguments(actionGroup._group_actions)
            formatter.end_section()

        # Add epilog
        formatter.add_text(self.epilog)

        return formatter.format_help()

    def parse_args(self, args=None, namespace=None):  # type: ignore[override]
        parsedArgs = super().parse_args(args, namespace)

        # Get all arguments that were actually provided by the user
        providedArgs = []
        if args is not None:
            providedArgs = [arg for arg in args if arg.startswith('-')]
        else:
            providedArgs = [arg for arg in sys.argv[1:] if arg.startswith('-')]

        # Check if any arguments were provided
        hasAnyArgs = len(providedArgs) > 0

        # Check if --catalog was provided
        hasCatalog = parsedArgs.mas_catalog_version is not None

        # Check if only help was requested
        helpOnly = '--help' in providedArgs or '-h' in providedArgs

        # Validation: If any arguments are provided (except help), --catalog must be present
        if hasAnyArgs and not hasCatalog and not helpOnly:
            self.error("non-interactive mode requires --catalog parameter, the interactive mode does not support any flags")

        return parsedArgs


updateArgParser = UpdateArgumentParser(
    prog='mas update',
    description="Update the IBM Maximo Operator Catalog, and related MAS dependencies by configuring and launching the MAS Update Tekton Pipeline.",
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = updateArgParser.add_argument_group(
    'Catalog Selection',
    'Select the IBM Maximo Operator Catalog version to update to.'
)
masArgGroup.add_argument(
    '-c', '--catalog',
    dest='mas_catalog_version',
    required=False,
    help="Maximo Operator Catalog Version (e.g. v9-240625-amd64)"
)

depsArgGroup = updateArgParser.add_argument_group(
    'Update Dependencies',
    'Configure which MAS dependencies (Db2, MongoDB, Kafka) should be updated and specify their namespaces.'
)
depsArgGroup.add_argument(
    '--db2-namespace',
    required=False,
    help="Namespace where Db2u operator and instances will be updated",
)

depsArgGroup.add_argument(
    '--mongodb-namespace',
    required=False,
    help="Namespace where MongoCE operator and instances will be updated",
)

depsArgGroup.add_argument(
    '--mongodb-v5-upgrade',
    required=False,
    action="store_const",
    const="true",
    help="Required to confirm a major version update for MongoDb to version 5",
)

depsArgGroup.add_argument(
    '--mongodb-v6-upgrade',
    required=False,
    action="store_const",
    const="true",
    help="Required to confirm a major version update for MongoDb to version 6",
)

depsArgGroup.add_argument(
    '--mongodb-v7-upgrade',
    required=False,
    action="store_const",
    const="true",
    help="Required to confirm a major version update for MongoDb to version 7",
)

depsArgGroup.add_argument(
    '--mongodb-v8-upgrade',
    required=False,
    action="store_const",
    const="true",
    help="Required to confirm a major version update for MongoDb to version 8",
)

depsArgGroup.add_argument(
    '--kafka-namespace',
    required=False,
    help="Namespace where Kafka operator and instances will be updated",
)

depsArgGroup.add_argument(
    '--kafka-provider',
    required=False,
    choices=["redhat", "strimzi"],
    help="The type of Kakfa operator installed in the target namespace for updte",
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = updateArgParser.add_argument_group(
    'More',
    'Additional options including development mode, Artifactory credentials, CP4D version, confirmation prompts, and pre-check control.'
)
otherArgGroup.add_argument(
    "--artifactory-username",
    required=False,
    help="Username for access to development builds on Artifactory"
)
otherArgGroup.add_argument(
    "--artifactory-token",
    required=False,
    help="API Token for access to development builds on Artifactory"
)
otherArgGroup.add_argument(
    "--dev-mode",
    required=False,
    action="store_true",
    default=False,
    help="Configure installation for development mode",
)
otherArgGroup.add_argument(
    "--cp4d-version",
    dest="cpd_product_version",
    required=False,
    help="Product version of CP4D to use"
)
otherArgGroup.add_argument(
    '--no-confirm',
    required=False,
    action='store_true',
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)
otherArgGroup.add_argument(
    '--skip-pre-check',
    required=False,
    action='store_true',
    default=False,
    help="Skips the 'pre-update-check' and 'post-update-verify' tasks in the update pipeline",
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit",
)
