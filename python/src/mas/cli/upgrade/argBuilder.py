# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""
Declarative specification of the non-interactive `mas upgrade` command that
the interactive wizard prints before the review settings screen.

Each entry names the argparse dest it maps to; the flag spelling is resolved
from the real upgradeArgParser at render time (see common.commandBuilder).
Only what argparse cannot express is spelled out here: where a value comes
from, which parameters are secrets (env-masked with an export placeholder),
and the conditions under which a flag is emitted.

Note that the wizard collects artifactory credentials in dev mode, but the
upgrade argument parser has no flags for them, so they cannot appear in the
generated command.
"""

from ..common.commandBuilder import CommandArg, renderCommand
from .argParser import upgradeArgParser

# ---------------------------------------------------------------------------
# Condition helpers
# ---------------------------------------------------------------------------


def _attr(name: str, default=None):
    return lambda app: getattr(app, name, default)


def _attrTruthy(name: str):
    return lambda app: bool(getattr(app, name, False))


def _knownChannel(app) -> bool:
    # The channel is "Unknown" when it could not be detected from the cluster;
    # --next-channel must not carry that placeholder value
    return getattr(app, "nextChannel", "") not in ("", "Unknown")


# ---------------------------------------------------------------------------
# Command specification
# ---------------------------------------------------------------------------

UPGRADE_COMMAND_ARGS = [
    # Instance Selection
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_instance_id", value=_attr("masInstanceId")),
    CommandArg(dest="next_channel", value=_attr("nextChannel"), when=_knownChannel),
    # Storage
    # -----------------------------------------------------------------------------
    CommandArg(dest="storage_pipeline", value=_attr("pipelineStorageClass")),
    CommandArg(dest="storage_accessmode", value=_attr("pipelineStorageAccessMode")),
    CommandArg(dest="storage_class_rwo"),
    CommandArg(dest="storage_class_rwx"),
    # Slack Integration
    # -----------------------------------------------------------------------------
    CommandArg(dest="slack_channel"),
    CommandArg(dest="slack_token", env_var="SLACK_TOKEN"),
    # More Options
    # -----------------------------------------------------------------------------
    CommandArg(dest="image_pull_policy"),
    CommandArg(dest="olm_approval_timeout"),
    CommandArg(dest="dev_mode", const=True, when=_attrTruthy("devMode")),
    CommandArg(dest="skip_pre_check", const=True, when=_attrTruthy("skipPreCheck")),
    # Footer
    # -----------------------------------------------------------------------------
    CommandArg(dest="accept_license", const=True, required=True),
    CommandArg(dest="no_confirm", const=True, required=True),
]


class upgradeArgBuilderMixin:
    def buildCommand(self) -> str:
        """
        Render the equivalent non-interactive `mas upgrade` command for the
        current wizard state, with secrets replaced by environment variables.
        """
        return renderCommand("mas upgrade", UPGRADE_COMMAND_ARGS, self, upgradeArgParser)
