# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

_FACILITIES_AGENTS_DEPLOYMENT_MODES = ["shared", "dedicated", "disabled", ""]

_FACILITIES_AGENTS_DEPLOYMENT_MODES_NO_DISABLED = ["shared", "dedicated", ""]

facilitiesAgentsDeploymentModes = {
    "dataconnectagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "extendedformulaagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "formularecalcagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "incomingmailagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "objectmigrationagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "objectpublishagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "maintenanceagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "reportqueueagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES_NO_DISABLED,
    "wfagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES_NO_DISABLED,
    "wffutureagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "wfnotificationagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "reservesmtpagent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
    "scheduleragent": _FACILITIES_AGENTS_DEPLOYMENT_MODES,
}

facilitiesAgents = list(facilitiesAgentsDeploymentModes.keys())
