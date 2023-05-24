#!/usr/bin/env python3

import yaml
from prettytable import PrettyTable

from mg.utils import printHeader

def process_subscription( output_dir, subscription, subscriptions_table ):
  subscriptionnamespace = subscription.rsplit()[0]
  subscriptionname = subscription.rsplit()[1]

  getSubscriptionOutput =  subprocess.run( "oc get subscription " + subscriptionname + " -n " + subscriptionnamespace + " -o yaml" , shell=True, capture_output=True, text=True)
  subscription_yaml =  yaml.load( getSubscriptionOutput.stdout, Loader=Loader )

  # Extract the conditions we are interested in
  sub_condition_types=['CatalogSourcesUnhealthy']
  sub_condition_statuses= {x['type']:{
    "status": x[ 'status']} for x in subscription_yaml['status']['conditions'] if x['type'] in sub_condition_types}
  sub_condition_statuses

  installplanname=subscription_yaml['status']['installplan']['name']

  #Lets check if we have an installplan as referenced in the subscription
  installplan_status="na"

  getInstallPlanOutput =  subprocess.run( "oc get installplan " + installplanname + " -n " + subscriptionnamespace + " -o yaml" , shell=True, capture_output=True, text=True)
  installplan_yaml =  yaml.load( getInstallPlanOutput.stdout, Loader=Loader)

  if str(installplan_yaml) != "None":
    ip_condition_types=['Installed']
    ip_condition_statuses= {x['type']:{
      "status": x[ 'status']} for x in installplan_yaml['status']['conditions'] if x['type'] in ip_condition_types}
    ip_condition_statuses
    ip_status= ip_condition_statuses['Installed']['status']
  else:
    ip_status="UNKNOWN"

  subscriptions_table.add_row([subscriptionname,
                               subscriptionnamespace,
                               subscription_yaml['spec']['channel'],
                               subscription_yaml['spec']['source'],
                               subscription_yaml['status']['installedCSV'],
                               subscription_yaml['spec']['installPlanApproval'],
                               sub_condition_statuses['CatalogSourcesUnhealthy']['status'],
                               subscription_yaml['status']['installplan']['name'],
                               ip_status])


def summarize( output_dir):
  subscriptions_file=output_dir + "/resources/_cluster/subscriptions.txt"
  subscriptions_table=PrettyTable()
  subscriptions_table.field_names = [ "Name", "Namespace", "Channel", "Source", "Installed CSV" ,"Approval", "CS Health", 'Install Plan', 'Installed' ]
  header=True
  with open( subscriptions_file ) as file:
    for subscription in file:
      if header == True:
        header=False
      else:
         process_subscription( output_dir, subscription, subscriptions_table )

  printHeader( "Subscriptions" )
  subscriptions_table.align = "l"
  print( subscriptions_table )
