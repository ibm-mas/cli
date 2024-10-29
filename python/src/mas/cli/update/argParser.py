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

from .. import __version__ as packageVersion
from ..cli import getHelpFormatter

updateArgParser = argparse.ArgumentParser(
    prog='mas update',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Update the IBM Maximo Operator Catalog, and related MAS dependencies by configuring and launching the MAS Update Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --catalog option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = updateArgParser.add_argument_group('Catalog Selection')
masArgGroup.add_argument(
    '-c', '--catalog',
    dest='mas_catalog_version',
    required=False,
    help="Maximo Operator Catalog Version (e.g. v9-240625-amd64)"
)

depsArgGroup = updateArgParser.add_argument_group('Update Dependencies')
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

droArgGroup = updateArgParser.add_argument_group('UDS to DRO Migration')

droArgGroup.add_argument(
    '--dro-migration',
    required=False,
    help="Required to confirm the migration from IBM User Data Services (UDS) to IBM Data Reporter Operator (DRO)",
)

droArgGroup.add_argument(
    '--dro-storage-class',
    required=False,
    help="Set Custom RWO Storage Class name for DRO as part of the update",
)

droArgGroup.add_argument(
    '--dro-namespace',
    required=False,
    help="Set Custom Namespace for DRO(Default: redhat-marketplace)",
)

# Development Mode
# -----------------------------------------------------------------------------
devArgGroup = updateArgParser.add_argument_group("Development Mode")
devArgGroup.add_argument(
    "--artifactory-username",
    required=False,
    help="Username for access to development builds on Artifactory"
)
devArgGroup.add_argument(
    "--artifactory-token",
    required=False,
    help="API Token for access to development builds on Artifactory"
)

# More Options
# -----------------------------------------------------------------------------
otherArgGroup = updateArgParser.add_argument_group('More')
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
