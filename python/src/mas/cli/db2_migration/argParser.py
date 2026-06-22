# -----------------------------------------------------------
# Licensed Materials - Property of IBM
# 5737-M66
# (C) Copyright IBM Corp. 2026 All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication, or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
# -----------------------------------------------------------

import argparse
import sys

from ..cli import getHelpFormatter


class Db2MigrationArgumentParser(argparse.ArgumentParser):
    """Custom argument parser for DB2 migration command"""

    def format_usage(self):
        prog = self.prog
        return (
            f"Usage (non-interactive mode):\n"
            f"  {prog} --namespace NAMESPACE [--cluster-name CLUSTER_NAME]\n"
            f"                  [--backup {{true,false}}] [--no-confirm]\n"
            f"\n"
            f"Usage (interactive mode):\n"
            f"  {prog}\n"
            f"\n"
            f"Usage (help):\n"
            f"  {prog} -h\n"
        )

    def parse_args(self, args=None, namespace=None):
        parsedArgs = super().parse_args(args, namespace)
        
        providedArgs = []
        if args is not None:
            providedArgs = [arg for arg in args if arg.startswith("-")]
        else:
            providedArgs = [arg for arg in sys.argv[1:] if arg.startswith("-")]
        
        hasAnyArgs = len(providedArgs) > 0
        hasNamespace = parsedArgs.namespace is not None
        helpOnly = "--help" in providedArgs or "-h" in providedArgs
        
        if hasAnyArgs and not hasNamespace and not helpOnly:
            self.error("non-interactive mode requires --namespace parameter")
        
        return parsedArgs


db2MigrationArgParser = Db2MigrationArgumentParser(
    prog="mas db2ucluster-migration",
    description="Migrate Db2uCluster to Db2uInstance by launching the DB2 Migration Tekton Pipeline.",
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False,
)

migrationArgGroup = db2MigrationArgParser.add_argument_group(
    "Migration Configuration",
    "Configure the DB2 migration parameters."
)
migrationArgGroup.add_argument(
    "--namespace",
    required=False,
    help="Namespace containing Db2uCluster instances"
)
migrationArgGroup.add_argument(
    "--cluster-name",
    required=False,
    help="Specific Db2uCluster name to migrate"
)
migrationArgGroup.add_argument(
    "--backup",
    required=False,
    choices=["true", "false"],
    help="Enable or disable backup before migration"
)

otherArgGroup = db2MigrationArgParser.add_argument_group("More", "Additional options.")
otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch without prompting for confirmation"
)
otherArgGroup.add_argument(
    "-h",
    "--help",
    action="help",
    default=False,
    help="Show this help message and exit"
)
