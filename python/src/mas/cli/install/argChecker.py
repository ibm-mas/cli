# *****************************************************************************
# Copyright (c) 2025 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging

logger = logging.getLogger(__name__)


def verifyArgs(parser, args):
    verifySLSArgs(parser, args)

def verifySLSArgs(parser, args):
    group_1 = [args.sls_namespace, args.license_file]
    group_2 = [args.sls_url, args.sls_registration_key, args.sls_certificates]

    if any(v is not None for v in group_1) and any(v is not None for v in group_2):
        parser.error("Cannot combine [--sls-namespace, --license-file] with [--sls-url, --sls-registration-key, --sls-certificates].")

    if not all(v is not None for v in group_2) and any(v is not None for v in group_2):
        parser.error("When providing any of --sls-url, --sls-registration-key and --sls-certificates, all three are required.")
