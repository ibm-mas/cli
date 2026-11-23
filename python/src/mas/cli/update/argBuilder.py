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
Declarative specification of the non-interactive `mas update` command that
the interactive wizard prints before the review settings screen.

Each entry names the argparse dest it maps to; the flag spelling is resolved
from the real updateArgParser at render time (see common.commandBuilder).
Only what argparse cannot express is spelled out here: where a value comes
from, which parameters are secrets (env-masked with an export placeholder),
and the conditions under which a flag is emitted.

Note that many wizard parameters are auto-detected from the cluster at
runtime (e.g. mongodb_version, grafana_v5_upgrade, odh_to_rhoai_migration,
cp4d_update) and have no command line flag, so they intentionally do not
appear here: the generated command re-runs the same detection.
"""

from ..common.commandBuilder import CommandArg, paramIsTrue, renderCommand
from .argParser import updateArgParser

# ---------------------------------------------------------------------------
# Condition helpers
# ---------------------------------------------------------------------------


def _ne(param: str, unexpected: str):
    return lambda app: app.getParam(param) != unexpected


def _attr(name: str, default=None):
    return lambda app: getattr(app, name, default)


def _attrTruthy(name: str):
    return lambda app: bool(getattr(app, name, False))


# ---------------------------------------------------------------------------
# Command specification
# ---------------------------------------------------------------------------

UPDATE_COMMAND_ARGS = [
    # Catalog Selection
    # -----------------------------------------------------------------------------
    CommandArg(dest="mas_catalog_version"),
    # Dependency Updates
    # -----------------------------------------------------------------------------
    CommandArg(dest="db2_namespace"),
    CommandArg(dest="db2_v12_upgrade", const=True, when=paramIsTrue("db2_v12_upgrade")),
    CommandArg(dest="db2_license_file", value=_attr("db2LicenseFileLocal")),
    CommandArg(dest="mongodb_namespace"),
    CommandArg(dest="mongodb_v5_upgrade", const=True, when=paramIsTrue("mongodb_v5_upgrade")),
    CommandArg(dest="mongodb_v6_upgrade", const=True, when=paramIsTrue("mongodb_v6_upgrade")),
    CommandArg(dest="mongodb_v7_upgrade", const=True, when=paramIsTrue("mongodb_v7_upgrade")),
    CommandArg(dest="mongodb_v8_upgrade", const=True, when=paramIsTrue("mongodb_v8_upgrade")),
    CommandArg(dest="kafka_namespace"),
    CommandArg(dest="kafka_provider"),
    # IBM Cloud Pak for Data
    # -----------------------------------------------------------------------------
    CommandArg(dest="cpd_product_version"),
    # Development Mode
    # -----------------------------------------------------------------------------
    CommandArg(dest="artifactory_username", env_var="ARTIFACTORY_USERNAME", extra_exports=("ARTIFACTORY_TOKEN",)),
    CommandArg(dest="artifactory_token", env_var="ARTIFACTORY_TOKEN", when=_ne("artifactory_username", "")),
    # Slack Integration
    # -----------------------------------------------------------------------------
    CommandArg(dest="slack_channel"),
    CommandArg(dest="slack_token", env_var="SLACK_TOKEN"),
    # More Options
    # -----------------------------------------------------------------------------
    CommandArg(dest="image_pull_policy"),
    CommandArg(dest="olm_approval_timeout"),
    CommandArg(dest="dev_mode", const=True, when=_attrTruthy("devMode")),
    CommandArg(dest="skip_pre_check", const=True, when=paramIsTrue("skip_pre_check")),
    # Footer
    # -----------------------------------------------------------------------------
    CommandArg(dest="no_confirm", const=True, required=True),
]


class updateArgBuilderMixin:
    def buildCommand(self) -> str:
        """
        Render the equivalent non-interactive `mas update` command for the
        current wizard state, with secrets replaced by environment variables.
        """
        return renderCommand("mas update", UPDATE_COMMAND_ARGS, self, updateArgParser)
