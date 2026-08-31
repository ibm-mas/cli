# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
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

IMAGE_PULL_POLICIES = ["IfNotPresent", "Always"]
STORAGE_ACCESS_MODES = ["ReadWriteMany", "ReadWriteOnce"]

upgradeArgParser = argparse.ArgumentParser(
    prog="mas upgrade",
    description="\n".join(
        [
            f"IBM Maximo Application Suite Admin CLI v{packageVersion}",
            "Upgrade MAS by configuring and launching the MAS Upgrade Tekton Pipeline.\n",
            "Interactive Mode:",
            "Omitting the --instance-id option will trigger an interactive prompt",
        ]
    ),
    epilog="Refer to the online documentation for more information: https://ibm-mas.github.io/cli/",
    formatter_class=getHelpFormatter(),
    add_help=False,
)

masArgGroup = upgradeArgParser.add_argument_group("MAS Instance Selection", "Select the MAS instance to upgrade to the next available release.")
masArgGroup.add_argument("--mas-instance-id", required=False, help="The MAS instance ID to be upgraded")
otherArgGroup = upgradeArgParser.add_argument_group(
    "More", "Additional options including pre-check control, confirmation prompts, license acceptance, and development mode."
)
otherArgGroup.add_argument(
    "--skip-pre-check",
    required=False,
    action="store_true",
    default=False,
    help="Disable the 'pre-upgrade-check' and 'post-upgrade-verify' tasks in the upgrade pipeline",
)
otherArgGroup.add_argument(
    "--no-confirm",
    required=False,
    action="store_true",
    default=False,
    help="Launch the upgrade without prompting for confirmation",
)
otherArgGroup.add_argument("--accept-license", action="store_true", default=False, help="Accept all license terms without prompting")
otherArgGroup.add_argument(
    "--dev-mode",
    required=False,
    action="store_true",
    default=False,
    help="Configure upgrade for development mode",
)
masArgGroup.add_argument("--next-channel", required=False, default="", help="The Target Mas channel to Upgrade on")
storageArgGroup = upgradeArgParser.add_argument_group("Storage", "Storage class configuration for the upgrade pipeline PVC.")
storageArgGroup.add_argument(
    "--storage-pipeline",
    required=False,
    dest="storage_pipeline",
    help="Pipeline storage class to use for the upgrade config PVC (e.g. ibmc-file-gold-gid). " "Auto-detected from the existing config-pvc when omitted.",
)
storageArgGroup.add_argument(
    "--storage-accessmode",
    required=False,
    dest="storage_accessmode",
    choices=STORAGE_ACCESS_MODES,
    metavar="{ReadWriteMany,ReadWriteOnce}",
    help="Pipeline storage class access mode (ReadWriteMany or ReadWriteOnce). " "Auto-detected from the existing config-pvc when omitted.",
)
otherArgGroup.add_argument("--slack-token", required=False, help="Slack bot token for sending pipeline status notifications")
otherArgGroup.add_argument("--slack-channel", required=False, help="Slack channel(s) for pipeline notifications (comma-separated for multiple channels)")
otherArgGroup.add_argument(
    "--image-pull-policy",
    dest="image_pull_policy",
    required=False,
    help="Image pull policy for Tekton Pipeline",
    choices=IMAGE_PULL_POLICIES,
    metavar="{IfNotPresent,Always}",
)
otherArgGroup.add_argument(
    "-h",
    "--help",
    action="help",
    default=False,
    help="Show this help message and exit",
)
