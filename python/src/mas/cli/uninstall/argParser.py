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

uninstallArgParser = argparse.ArgumentParser(
    prog='mas uninstall',
    description="\n".join([
        f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
        "Uninstall MAS by configuring and launching the MAS Uninstall Tekton Pipeline.\n",
        "Interactive Mode:",
        "Omitting the --instance-id option will trigger an interactive prompt"
    ]),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False
)

masArgGroup = uninstallArgParser.add_argument_group('MAS Instance Selection')
masArgGroup.add_argument(
    '--mas-instance-id',
    required=False,
    help="The MAS instance ID to be uninstalled"
)

masArgGroup.add_argument(
    '--dro-namespace',
    required=False,
    default='redhat-marketplace',
    help="The DRO namespace to be uninstalled"
)

depsArgGroup = uninstallArgParser.add_argument_group('MAS Dependencies Selection')
depsArgGroup.add_argument(
    '--uninstall-all-deps',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall all MAS-related dependencies from the target cluster",
)

depsArgGroup.add_argument(
    '--uninstall-cert-manager',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall Certificate Manager from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-common-services',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall IBM Common Services from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-grafana',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall Grafana from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-ibm-catalog',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall the IBM Maximo Operator Catalog Source (ibm-operator-catalog) from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-mongodb',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall MongoDb from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-sls',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall IBM Suite License Service from the target cluster",
)
depsArgGroup.add_argument(
    '--uninstall-uds',
    required=False,
    action='store_true',
    default=False,
    help="Uninstall IBM User Data Services from the target cluster",
)

otherArgGroup = uninstallArgParser.add_argument_group('More')
otherArgGroup.add_argument(
    '--no-confirm',
    required=False,
    action='store_true',
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)
otherArgGroup.add_argument(
    '-h', "--help",
    action='help',
    default=False,
    help="Show this help message and exit",
)
