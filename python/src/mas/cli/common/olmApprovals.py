# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

"""OLM install plan approval support shared by the install, update and upgrade commands.

Two concerns live here:

- **Resolution** (:func:`resolveOlmApprovalMode` / :func:`resolveOlmApprovalTimeout`):
  the CLI mirrors the collection's precedence (ansible-devops
  ``plugins/module_utils/olm_approvals.py``) -- flag > ``OLM_APPROVAL_MODE`` /
  ``OLM_APPROVAL_TIMEOUT`` shell environment variable > omitted. Environment
  variable values are validated up front so a bad value fails with a message
  naming the variable, before any cluster interaction or pipeline launch.
  When neither flag nor environment variable is set the params are omitted
  from the PipelineRun and the pipeline defaults apply (empty string, which
  the collection treats as unset: Automatic mode, 7200s timeout).

- **Detection** (:class:`OlmApprovalDetectionMixin`): update and upgrade do
  not ask for the approval mode -- it was chosen at install time and is a
  property of the cluster. Before submitting the PipelineRun they aggregate
  the effective mode of every Subscription in the command's scope (see
  ``mas.devops.olm.getClusterApprovalMode``), report it in the review
  summary, and pass the effective mode to the pipeline. Mixed aggregates are
  treated as Manual, consistent with the collection's semantics.
"""

import logging
from os import environ
from typing import Callable, Optional

from mas.devops.olm import getClusterApprovalMode

logger = logging.getLogger(__name__)

VALID_OLM_APPROVAL_MODES = ("Automatic", "Manual")

# The collection's default per-wait approval budget (2 hours), in seconds
DEFAULT_OLM_APPROVAL_TIMEOUT = 7200

GetenvCallable = Callable[[str], Optional[str]]


def resolveOlmApprovalMode(flagValue: Optional[str], getenv: GetenvCallable = environ.get) -> Optional[str]:
    """Resolve the effective OLM install plan approval mode for install.

    Precedence: flag > ``OLM_APPROVAL_MODE`` environment variable > None
    (omitted from the PipelineRun; the pipeline default of Automatic applies).

    Args:
        flagValue: The ``--olm-approval-mode`` flag value (None when unset).
        getenv: Environment lookup, injectable for testing.

    Returns:
        The resolved mode ("Automatic" or "Manual"), or None when neither the
        flag nor the environment variable is set.

    Raises:
        ValueError: When the environment variable holds a value that is not
            "Automatic" or "Manual" (the variable is named in the message,
            mirroring the collection's validation).
    """
    if flagValue is not None:
        return flagValue

    envMode = getenv("OLM_APPROVAL_MODE")
    if envMode:
        if envMode not in VALID_OLM_APPROVAL_MODES:
            raise ValueError(f"OLM_APPROVAL_MODE must be one of: {', '.join(VALID_OLM_APPROVAL_MODES)} (found '{envMode}')")
        return envMode
    return None


def resolveOlmApprovalTimeout(flagValue: Optional[int], getenv: GetenvCallable = environ.get) -> Optional[int]:
    """Resolve the per-wait OLM approval timeout, in seconds.

    Precedence: flag > ``OLM_APPROVAL_TIMEOUT`` environment variable > None
    (omitted from the PipelineRun; the collection's default of 7200 seconds
    applies).

    Args:
        flagValue: The ``--olm-approval-timeout`` flag value (None when unset).
        getenv: Environment lookup, injectable for testing.

    Returns:
        The resolved timeout in seconds, or None when neither the flag nor
        the environment variable is set.

    Raises:
        ValueError: When the environment variable does not hold an integer
            number of seconds (the variable is named in the message).
    """
    if flagValue is not None:
        return flagValue

    envTimeout = getenv("OLM_APPROVAL_TIMEOUT")
    if envTimeout:
        try:
            return int(envTimeout)
        except ValueError:
            raise ValueError(f"OLM_APPROVAL_TIMEOUT must be an integer number of seconds (found '{envTimeout}')")
    return None


class OlmApprovalDetectionMixin:
    """Detect and report the cluster's aggregate OLM install plan approval mode.

    Mixed into the update and upgrade apps: the approval mode is not a flag on
    those commands (it was chosen at install time), it is detected over the
    command's blast radius -- cluster-wide for update, the ``mas-{instance_id}-``
    namespaces for upgrade -- and the effective mode is passed to the
    PipelineRun so the pipeline behaves consistently with the cluster.

    Requires the host class to provide ``self.dynamicClient`` and
    ``self.setParam`` (any ``BaseApp`` subclass).
    """

    def detectOLMApprovalMode(self, namespacePrefix: Optional[str] = None) -> None:
        """Detect the aggregate approval mode and set the ``olm_approval_mode`` param.

        Stores the full detection result in ``self.olmApprovalStatus`` (dict as
        returned by ``mas.devops.olm.getClusterApprovalMode``) for the review
        summary. A detection failure is non-fatal: the mode is left unset and
        the pipeline defaults (Automatic) apply.

        Args:
            namespacePrefix: Restrict detection to namespaces whose name starts
                with this prefix (the upgrade scope). None inspects the whole
                cluster (the update scope).
        """
        try:
            status = getClusterApprovalMode(self.dynamicClient, namespacePrefix=namespacePrefix)
        except Exception as e:  # noqa: BLE001 - detection is advisory, never blocks the command
            logger.warning(f"Failed to detect the OLM install plan approval mode: {e}")
            self.olmApprovalStatus = None
            return

        self.olmApprovalStatus = status
        mode = status["approvalMode"]
        if mode is None:
            # No subscriptions in scope: nothing can gate on approval, leave
            # the mode unset so the pipeline defaults apply
            logger.debug("No subscriptions in scope for OLM approval mode detection")
            return

        # A Mixed aggregate behaves the same as Manual for waiting semantics
        self.setParam("olm_approval_mode", "Manual" if mode == "Mixed" else mode)
        logger.debug(f"Detected OLM install plan approval mode: {self.getParam('olm_approval_mode')} (aggregate: {mode})")

    def olmApprovalSummary(self) -> str:
        """Format the detected aggregate approval mode for the review summary.

        Returns:
            A human-readable summary: the plain aggregate for Automatic /
            Manual scopes (with the wait behaviour called out under Manual),
            "Mixed (N Automatic, M Manual) — treating as Manual" for mixed
            scopes, or a placeholder when detection found nothing in scope.
        """
        status = getattr(self, "olmApprovalStatus", None)
        if status is None or status.get("approvalMode") is None:
            return "No subscriptions in scope (default Automatic)"

        mode = status["approvalMode"]
        if mode == "Mixed":
            counts = ", ".join(f"{count} {name}" for name, count in sorted(status["counts"].items()))
            return f"Mixed ({counts}) — treating as Manual"
        elif mode == "Manual":
            return "Manual — install plans generated by this run will wait for your approval"
        else:
            return "Automatic"
