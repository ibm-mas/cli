# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

PACKAGE_CONFIGS = [
    ("Required Dependencies", "sls", "ibm-sls", "sls_version"),
    ("Required Dependencies", "tsm", "ibm-truststore-mgr", "tsm_version"),

    ("Optional Dependencies", "amlen", "amlen", "amlen_extras_version"),

    ("Optional Dependencies", "aiservice", "ibm-aiservice", "aiservice_version"),
    ("Optional Dependencies", "data-dictionary", "ibm-data-dictionary", "dd_version"),

    ("Optional Dependencies", "db2u-s11", "ibm-db2uoperator-s11", "db2u_version"),
    ("Optional Dependencies", "db2u-s12", "ibm-db2uoperator-s12", "db2u_version"),

    ("Optional Dependencies", "mongodb-ce", "mongodb-ce", "mongo_extras_version_default"),

    ("Maximo Application Suite", "core", "ibm-mas", "mas_core_version"),
    ("Maximo Application Suite", "assist", "ibm-mas-assist", "mas_assist_version"),
    ("Maximo Application Suite", "iot", "ibm-mas-iot", "mas_iot_version"),
    ("Maximo Application Suite", "facilities", "ibm-mas-facilities", "mas_facilities_version"),
    ("Maximo Application Suite", "manage", "ibm-mas-manage", "mas_manage_version"),
    ("Maximo Application Suite", "manage-icd", "ibm-mas-manage-icd", "mas_manage_version"),
    ("Maximo Application Suite", "monitor", "ibm-mas-monitor", "mas_monitor_version"),
    ("Maximo Application Suite", "predict", "ibm-mas-predict", "mas_predict_version"),
    ("Maximo Application Suite", "optimizer", "ibm-mas-optimizer", "mas_optimizer_version"),
    ("Maximo Application Suite", "visualinspection", "ibm-mas-visualinspection", "mas_visualinspection_version"),

    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cp-common-services", "common_svcs_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-zen", "ibm_zen_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cp-datacore", "cp4d_platform_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-licensing", "ibm_licensing_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-ccs", "ccs_build"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cloud-native-postgresql", "postgress_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-datarefinery", "datarefinery_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-elasticsearch-operator", "elasticsearch_version"),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-opensearch-operator", "opensearch_version"),
    ("Cloud Pak for Data - WSL", "cp4d-wsl", "ibm-wsl", "wsl_version"),
    ("Cloud Pak for Data - WSL", "cp4d-wsl", "ibm-wsl-runtimes", "wsl_runtimes_version"),
    ("Cloud Pak for Data - WML", "cp4d-wml", "ibm-wml-cpd", "wml_version"),
    ("Cloud Pak for Data - Spark", "cp4d-spark", "ibm-analyticsengine", "spark_version"),
    ("Cloud Pak for Data - Cognos", "cp4d-cognos", "ibm-cognos-analytics-prod", "cognos_version"),
]
