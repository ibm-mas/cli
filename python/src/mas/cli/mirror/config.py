# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

# Each tuple: (section, argName, packageName, catalogKey, has_HelmCharts)
# has_HelmCharts=True for CPD CASE bundles that also ship Helm charts.
# These drive both image mirroring (via oc-mirror) and helm chart mirroring.
PACKAGE_CONFIGS = [
    ("Required Dependencies", "sls", "ibm-sls", "sls_version", False),
    ("Required Dependencies", "tsm", "ibm-truststore-mgr", "tsm_version", False),
    ("Optional Dependencies", "amlen", "amlen", "amlen_extras_version", False),
    ("Optional Dependencies", "aiservice", "ibm-aiservice", "aiservice_version", False),
    ("Optional Dependencies", "aiservice", "ibm-aiservice-tenant", "aiservice_tenant_version", False),
    ("Optional Dependencies", "aiservice", "opendatahub", "odh_version", False),
    ("Optional Dependencies", "aiservice", "minio", "minio_extras_version", False),
    ("Optional Dependencies", "data-dictionary", "ibm-data-dictionary", "dd_version", False),
    ("Optional Dependencies", "db2u-s11", "ibm-db2uoperator-s11", "db2u_version", False),
    ("Optional Dependencies", "db2u-s12", "ibm-db2uoperator-s12", "db2u_version", False),
    ("Optional Dependencies", "mongodb-ce", "mongodb-ce", "mongo_extras_version_default", False),
    ("Maximo Application Suite", "core", "ibm-mas", "mas_core_version", False),
    ("Maximo Application Suite", "assist", "ibm-mas-assist", "mas_assist_version", False),
    ("Maximo Application Suite", "assist", "ibm-couchdb", "couchdb_version", False),
    ("Maximo Application Suite", "iot", "ibm-mas-iot", "mas_iot_version", False),
    ("Maximo Application Suite", "facilities", "ibm-mas-facilities", "mas_facilities_version", False),
    ("Maximo Application Suite", "manage", "ibm-mas-manage", "mas_manage_version", False),
    ("Maximo Application Suite", "manage-icd", "ibm-mas-manage-icd", "mas_manage_version", False),
    ("Maximo Application Suite", "monitor", "ibm-mas-monitor", "mas_monitor_version", False),
    ("Maximo Application Suite", "predict", "ibm-mas-predict", "mas_predict_version", False),
    ("Maximo Application Suite", "optimizer", "ibm-mas-optimizer", "mas_optimizer_version", False),
    ("Maximo Application Suite", "visualinspection", "ibm-mas-visualinspection", "mas_visualinspection_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cp-common-services", "common_svcs_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-zen", "ibm_zen_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cp-datacore", "cp4d_platform_version", True),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-licensing", "ibm_licensing_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-ccs", "ccs_build", True),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-cloud-native-postgresql", "postgress_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-datarefinery", "datarefinery_version", True),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-elasticsearch-operator", "elasticsearch_version", False),
    ("Cloud Pak for Data - Platform", "cp4d-platform", "ibm-opensearch-operator", "opensearch_version", False),
    ("Cloud Pak for Data - WSL", "cp4d-wsl", "ibm-wsl", "wsl_version", True),
    ("Cloud Pak for Data - WSL", "cp4d-wsl", "ibm-wsl-runtimes", "wsl_runtimes_version", True),
    ("Cloud Pak for Data - WML", "cp4d-wml", "ibm-wml-cpd", "wml_version", True),
    ("Cloud Pak for Data - WML", "cp4d-wml", "ibm-redis-cp", "redis_version", True),
    ("Cloud Pak for Data - Spark", "cp4d-spark", "ibm-analyticsengine", "spark_version", True),
    ("Cloud Pak for Data - Cognos", "cp4d-cognos", "ibm-cognos-analytics-prod", "cognos_version", True),
]

# Helm-chart-only CASE bundles: no standalone ISC image files exist for these.
# Their images are bundled inside their parent CASE (e.g. ibm-opencontent-opensearch
# images come with ibm-opensearch-operator).
# Each tuple: (caseName, catalogKey, argName)
HELM_ONLY_CHART_CONFIGS = [
    ("ibm-opencontent-opensearch", "opensearch_version", "cp4d-platform"),
]
