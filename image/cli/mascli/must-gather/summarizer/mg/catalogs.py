#!/usr/bin/env python3

import yaml
from prettytable import PrettyTable

from mg.utils import printHeader

# process the catalog source information and show any catalogsources that have problems


def process_catalogsource(output_dir, catalogsource, catalogsource_table):
    catalogsourcename = catalogsource.rsplit()[0]
    catalogsource_yaml_file = output_dir + "/resources/openshift-marketplace/catalogsources/" + catalogsourcename + ".yaml"

    with open(catalogsource_yaml_file, 'r') as file:
        catalogsource_yaml = yaml.safe_load(file)

    catalogsource_table.add_row([catalogsourcename,
                                 catalogsource_yaml['spec']['displayName'],
                                 catalogsource_yaml['spec']['publisher'],
                                 catalogsource_yaml['status']['connectionState']['lastObservedState']])


# Create a report summarizing the catalog source status
def summarize(output_dir):
    catalogsource_file = output_dir + "/resources/openshift-marketplace/catalogsources.txt"
    catalogsource_table = PrettyTable()
    catalogsource_table.field_names = ["Name", "Display Name", "Publisher", "Status"]
    header = True
    with open(catalogsource_file) as file:
        for catalogsource in file:
            if header is True:
                header = False
            else:
                process_catalogsource(output_dir, catalogsource, catalogsource_table)

    printHeader("Catalog Sources")
    catalogsource_table.align = "l"
    print(catalogsource_table)
