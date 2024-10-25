#!/usr/bin/env python3

import yaml
from prettytable import PrettyTable

from mg.utils import printHeader

# Create a report summarizing the cluster verison of the cluster


def processClusterVersion(output_dir):
    clusterversion_file = output_dir + "/resources/_cluster/clusterversions.txt"
    with open(clusterversion_file, 'r') as file:
    clusterversion = file.read()
  print(clusterversion)


# process the node information and show any nodes that have problems
def processNode(output_dir, node, node_table):
  nodename = node.rsplit()[0]
  node_yaml_file = output_dir + "/resources/_cluster/nodes/" + nodename + ".yaml"

  with open(node_yaml_file, 'r') as file:
        node_yaml = yaml.safe_load(file)

  # Extract the conditions we are interested in
    condition_types = ['MemoryPressure', 'DiskPressure', 'PIDPressure', 'Ready']
    condition_statuses = {x['type']: {
        "status": x['status']} for x in node_yaml['status']['conditions'] if x['type'] in condition_types}
  condition_statuses

  node_table.add_row([nodename,
                      node_yaml['status']['capacity']['cpu'],
                      node_yaml['status']['capacity']['memory'],
                      condition_statuses['Ready']['status'],
                      condition_statuses['MemoryPressure']['status'],
                      condition_statuses['DiskPressure']['status'],
                        condition_statuses['PIDPressure']['status']])


def processNodes(output_dir):
    nodes_file = output_dir + "/resources/_cluster/nodes.txt"
    node_table = PrettyTable()
    node_table.field_names = ["Node", "CPU", "Memory", "Ready", "Memory Pressure", "Disk Pressure", "PID Pressure"]
    header = True
    with open(nodes_file) as nodes_file:
    for node in nodes_file:
            if header is True:
                header = False
      else:
                processNode(output_dir, node, node_table)

  node_table.align = "l"
    print(node_table)


def summarize(output_dir):
  printHeader("Cluster Information")
  processClusterVersion(output_dir)
  processNodes(output_dir)
