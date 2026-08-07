# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Subscriptions summarizer for must-gather."""

import os
import yaml
from prettytable import PrettyTable, TableStyle
from typing import Optional, Dict, Any


def processSubscription(outputDir: str, subscriptionYaml: Dict[str, Any], ipYaml: Optional[Dict[str, Any]], subscriptionsTable: PrettyTable) -> None:
    """Process a single subscription and add its information to the table.

    Args:
        outputDir (str): Path to must-gather output directory
        subscriptionYaml (dict): Subscription YAML data
        ipYaml (dict, optional): InstallPlan YAML data
        subscriptionsTable (PrettyTable): Table to add subscription information to
    """
    if ipYaml is not None:
        ipStatus = ipYaml["status"]["phase"]
    else:
        ipStatus = "<unknown>"

    if "installPlanApproval" in subscriptionYaml["spec"]:
        approval = subscriptionYaml["spec"]["installPlanApproval"]
    else:
        approval = "<undefined>"

    if "installplan" in subscriptionYaml["status"]:
        installPlanName = subscriptionYaml["status"]["installplan"]["name"]
    else:
        installPlanName = "<undefined>"

    if "installedCSV" in subscriptionYaml["status"]:
        installedCSV = subscriptionYaml["status"]["installedCSV"]
    else:
        installedCSV = "<undefined>"

    # Create markdown links
    namespace = subscriptionYaml["metadata"]["namespace"]
    name = subscriptionYaml["metadata"]["name"]
    subscriptionLink = f"[{name}](../resources/{namespace}/subscriptions/{name}.yaml)"

    # Create InstallPlan link if it exists
    if installPlanName != "<undefined>":
        installPlanLink = f"[{installPlanName}](../resources/{namespace}/installplans/{installPlanName}.yaml)"
    else:
        installPlanLink = installPlanName

    subscriptionsTable.add_row(
        [
            namespace,
            subscriptionLink,
            subscriptionYaml["spec"]["channel"],
            subscriptionYaml["spec"]["source"],
            installedCSV,
            approval,
            installPlanLink,
            ipStatus,
        ]
    )


def summarize(outputDir: str) -> None:
    """Generate cluster-wide subscriptions summary.

    Reads subscription and installplan resources from per-namespace directories
    and writes a unified markdown table to resources/_cluster/subscriptions.md.

    Args:
        outputDir (str): Path to must-gather output directory
    """
    resourcesDir = os.path.join(outputDir, "resources")

    # Collect all subscriptions and installplans from all namespaces
    subscriptions = []
    installPlans = []

    # Walk through all namespace directories
    if os.path.exists(resourcesDir):
        for namespace in os.listdir(resourcesDir):
            namespacePath = os.path.join(resourcesDir, namespace)
            if not os.path.isdir(namespacePath):
                continue

            # Read subscriptions from this namespace
            subsDir = os.path.join(namespacePath, "subscriptions")
            if os.path.exists(subsDir):
                for filename in os.listdir(subsDir):
                    if filename.endswith(".yaml"):
                        filepath = os.path.join(subsDir, filename)
                        with open(filepath, "r") as file:
                            sub = yaml.safe_load(file)
                            if sub:
                                subscriptions.append(sub)

            # Read installplans from this namespace
            ipsDir = os.path.join(namespacePath, "installplans")
            if os.path.exists(ipsDir):
                for filename in os.listdir(ipsDir):
                    if filename.endswith(".yaml"):
                        filepath = os.path.join(ipsDir, filename)
                        with open(filepath, "r") as file:
                            ip = yaml.safe_load(file)
                            if ip:
                                installPlans.append(ip)

    # Build installplan lookup by name
    installPlansByName = {}
    for ip in installPlans:
        installPlansByName[ip["metadata"]["name"]] = ip

    subscriptionsTable = PrettyTable()
    subscriptionsTable.field_names = ["Namespace", "Name", "Channel", "Source", "Installed CSV", "Approval", "Install Plan", "Install Phase"]

    for sub in subscriptions:
        if "installplan" in sub["status"] and sub["status"]["installplan"]["name"] in installPlansByName:
            ip = installPlansByName[sub["status"]["installplan"]["name"]]
        else:
            ip = None
        processSubscription(outputDir, sub, ip, subscriptionsTable)

    subscriptionsTable.align = "l"
    subscriptionsTable.set_style(TableStyle.MARKDOWN)

    # Write to resources/_cluster/subscriptions.md
    clusterDir = os.path.join(outputDir, "resources", "_cluster")
    os.makedirs(clusterDir, exist_ok=True)
    outputFile = os.path.join(clusterDir, "subscriptions.md")

    with open(outputFile, "w") as f:
        f.write("# Subscription (operators.coreos.com/v1alpha1)\n\n")
        f.write(str(subscriptionsTable))
        f.write("\n")
