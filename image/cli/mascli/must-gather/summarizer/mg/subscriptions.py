#!/usr/bin/env python3

import yaml
from prettytable import PrettyTable

from mg.utils import printHeader


def process_subscription(output_dir, subscriptionYaml, ipYaml, subscriptions_table):
  # Extract the conditions we are interested in
  sub_condition_types = ["CatalogSourcesUnhealthy"]
  sub_condition_statuses = {x["type"]: {
    "status": x["status"]} for x in subscriptionYaml["status"]["conditions"] if x["type"] in sub_condition_types}

  if ipYaml is not None:
    ip_status = ipYaml["status"]["phase"]
  else:
    ip_status = "<unknown>"

  if "installPlanApproval" in subscriptionYaml["spec"]:
    approval = subscriptionYaml["spec"]["installPlanApproval"]
  else:
    approval = "<undefined>"

  if "installplan" in subscriptionYaml["status"]:
    installPlan = subscriptionYaml["status"]["installplan"]["name"]
  else:
    installPlan = "<undefined>"

  if "installedCSV" in subscriptionYaml["status"]:
    installedCSV = subscriptionYaml["status"]["installedCSV"]
  else:
    installedCSV = "<undefined>"

  subscriptions_table.add_row([
    subscriptionYaml["metadata"]["namespace"],
    subscriptionYaml["metadata"]["name"],
    subscriptionYaml["spec"]["channel"],
    subscriptionYaml["spec"]["source"],
    installedCSV,
    approval,
    sub_condition_statuses["CatalogSourcesUnhealthy"]["status"],
    installPlan,
    ip_status
  ])


def summarize(output_dir):
  subsFile = output_dir + "/resources/_cluster/subscriptions/all-namespaces.yaml"
  ipsFile = output_dir + "/resources/_cluster/installplans/all-namespaces.yaml"

  with open(subsFile, "r") as file:
    subs = yaml.safe_load(file)

  with open(ipsFile, "r") as file:
    ips = yaml.safe_load(file)

  installPlansByName = {}
  for ip in ips["items"]:
    installPlansByName[ip["metadata"]["name"]] = ip

  subscriptions_table = PrettyTable()
  subscriptions_table.field_names = ["Namespace", "Name", "Channel", "Source", "Installed CSV", "Approval", "CS Health", "Install Plan", "Install Phase"]

  for sub in subs["items"]:
    if "installplan" in sub["status"] and sub["status"]["installplan"]["name"] in installPlansByName:
      ip = installPlansByName[sub["status"]["installplan"]["name"]]
    else:
      ip = None
    process_subscription(output_dir, sub, ip, subscriptions_table)

  printHeader("Subscriptions")
  subscriptions_table.align = "l"
  print(subscriptions_table)