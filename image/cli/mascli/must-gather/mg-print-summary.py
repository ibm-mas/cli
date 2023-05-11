#!/usr/bin/env python

import yaml
import sys
from prettytable import PrettyTable
from prettytable import from_csv


# process the node information and show any nodes that have problems
def process_node( output_dir, node, node_table ):
  nodename = node.rsplit()[0]
  node_yaml_file = output_dir + "/resources/_cluster/nodes/" + nodename + ".yaml"

  with open(node_yaml_file, 'r') as file:
    node_yaml=yaml.safe_load( file )

  # Extract the conditions we are interested in
  condition_types=['MemoryPressure', 'DiskPressure', 'PIDPressure', 'Ready']  
  condition_statuses= {x['type']:{
    "status": x[ 'status']} for x in node_yaml['status']['conditions'] if x['type'] in condition_types}
  condition_statuses

  node_table.add_row([nodename, 
                      node_yaml['status']['capacity']['cpu'], 
                      node_yaml['status']['capacity']['memory'],
                      condition_statuses['Ready']['status'], 
                      condition_statuses['MemoryPressure']['status'], 
                      condition_statuses['DiskPressure']['status'],
                      condition_statuses['PIDPressure']['status'] ])



# Create a report summarizing the statsus of the nodes in the cluster
def process_nodes(output_dir):
  nodes_file=output_dir + "/resources/_cluster/nodes.txt"
  node_table=PrettyTable()
  node_table.field_names = [ "Node", "CPU", "Memory", "Ready" , "Memory Pressure", "Disk Pressure", "PID Pressure" ]
  header=True
  with open( nodes_file ) as nodes_file:
    for node in nodes_file:
      if header == True:
        header=False
      else:
         process_node( output_dir, node, node_table )  

  print( "*********************************************************************" )   
  print( "Node Information" )
  print( "*********************************************************************" )  
  node_table.align = "l"
  print( node_table )


# Create a report summarizing the cluster verison of the cluster
def process_cluster(output_dir):
  clusterversion_file=output_dir + "/resources/_cluster/clusterversions.txt"
  with open(clusterversion_file , 'r') as file:
    clusterversion = file.read()
  print( "*********************************************************************" )   
  print( "Cluster Version Information" )
  print( "*********************************************************************" )   
  print( clusterversion ) 
    

#Create a report summarizing the catalog source status
def process_catalogsources(output_dir):
  catalogsource_file=output_dir + "/resources/openshift-marketplace/catalogsources.txt"  
  catalogsource_table=PrettyTable()
  catalogsource_table.field_names = [ "Name", "Display Name", "Publisher", "Status" ]
  header=True
  with open( catalogsource_file ) as file:
    for catalogsource in file:
      if header == True:
        header=False
      else:
         process_catalogsource( output_dir, catalogsource, catalogsource_table )  

  print( "*********************************************************************" )   
  print( "Catalog Suurce Information" )
  print( "*********************************************************************" ) 
  catalogsource_table.align = "l" 
  print( catalogsource_table )

# process the catalog source information and show any catalogsources that have problems
def process_catalogsource( output_dir, catalogsource, catalogsource_table ):
  catalogsourcename = catalogsource.rsplit()[0]
  catalogsource_yaml_file = output_dir + "/resources/openshift-marketplace/catalogsources/" + catalogsourcename + ".yaml"

  with open(catalogsource_yaml_file, 'r') as file:
    catalogsource_yaml=yaml.safe_load( file )

  catalogsource_table.add_row([catalogsourcename, 
                               catalogsource_yaml['spec']['displayName'], 
                               catalogsource_yaml['spec']['publisher'],
                               catalogsource_yaml['status']['connectionState']['lastObservedState']])




def process_storageclasses( output_dir ):
  storageclasses_file=output_dir + "/resources/_cluster/storageclasses.txt"  
  storageclass_table=PrettyTable()
  storageclass_table.field_names = [ "Name", "Provisioner", "Reclaim Policy", "Volume Binding Mode", "Allow Volume Expansion", "Default (tbc)" ]
  header=True
  with open( storageclasses_file ) as file:
    for storageclass in file:
      if header == True:
        header=False
      else:
         process_storageclass( output_dir, storageclass, storageclass_table )  

  print( "*********************************************************************" )   
  print( "Storage Class Information" )
  print( "*********************************************************************" ) 
  storageclass_table.align = "l" 
  print( storageclass_table )


# process the storage class information and show any storage classes that have problems
def process_storageclass( output_dir, storageclass, storageclass_table ):
  storageclassname = storageclass.rsplit()[0]
  storageclass_yaml_file = output_dir + "/resources/_cluster/storageclasses/" + storageclassname + ".yaml"

  with open(storageclass_yaml_file, 'r') as file:
    storageclass_yaml=yaml.safe_load( file )

  allow_volume_expansion = "allowVolumeExpansion" in storageclass_yaml

  # We should get this from the annotataions
  default_storage_class = False

  storageclass_table.add_row([ storageclassname, 
                               storageclass_yaml['provisioner'], 
                               storageclass_yaml['reclaimPolicy'],
                               storageclass_yaml['volumeBindingMode'],
                               allow_volume_expansion,
                               default_storage_class ])



# Process the output from the must-gather to generate a summary report
def  process_must_gather(args):
  output_dir=args[1]

  # What do we know about the cluster
  process_cluster( output_dir )\
  
  #What do we know about the nodes
  process_nodes( output_dir)

  #What do we know about the catalogsources
  process_catalogsources( output_dir)

  #What do we know about subscriptions and their install plans
  process_storageclasses( output_dir )


if __name__ == "__main__":
    process_must_gather(sys.argv)

