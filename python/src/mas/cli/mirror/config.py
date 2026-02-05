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
    ("Required Dependencies", "sls", "ibm-sls", "sls_version", "IBM Suite License Service"),
    ("Required Dependencies", "tsm", "ibm-truststore-mgr", "tsm_version", "IBM Truststore Manager"),

    ("Optional Dependencies", "amlen", "amlen", "amlen_extras_version", "Eclipse Amlen"),

    ("Optional Dependencies", "aiservice", "ibm-aiservice", "aiservice_version", "IBM Maximo AI Service"),
    ("Optional Dependencies", "data-dictionary", "ibm-data-dictionary", "dd_version", "IBM Data Dictionary"),

    ("Optional Dependencies", "db2u-s11", "ibm-db2uoperator-s11", "db2u_version", "IBM Db2 Universal Operator (s11)"),
    ("Optional Dependencies", "db2u-s12", "ibm-db2uoperator-s12", "db2u_version", "IBM Db2 Universal Operator (s12)"),

    ("Optional Dependencies", "mongodb-ce", "mongodb-ce", "mongo_extras_version_default", "MongoDb (CE)"),

    # TODO: Support CP4D ("MAS", "manage", "mongodb-ce", "mas_manage_version", "MongoDb (CE)"),
    # TODO: Support CP4D - WSL ("MAS", "manage", "mongodb-ce", "mas_manage_version", "MongoDb (CE)"),
    # TODO: Support CP4D - WML ("MAS", "manage", "mongodb-ce", "mas_manage_version", "MongoDb (CE)"),
    # TODO: Support CP4D - Spark ("MAS", "manage", "mongodb-ce", "mas_manage_version", "MongoDb (CE)"),
    # TODO: Support CP4D - Cognos ("MAS", "manage", "mongodb-ce", "mas_manage_version", "MongoDb (CE)"),

    ("Maximo Application Suite", "core", "ibm-mas", "mas_core_version", "Core"),
    ("Maximo Application Suite", "assist", "ibm-mas-assist", "mas_assist_version", "Assist"),
    ("Maximo Application Suite", "iot", "ibm-mas-iot", "mas_iot_version", "IoT"),
    ("Maximo Application Suite", "facilities", "ibm-mas-facilities", "mas_facilities_version", "Facilities"),
    ("Maximo Application Suite", "manage", "ibm-mas-manage", "mas_manage_version", "Manage"),
    ("Maximo Application Suite", "manage-icd", "ibm-mas-manage-icd", "mas_manage_version", "Manage (ICD)"),
    ("Maximo Application Suite", "monitor", "ibm-mas-monitor", "mas_monitor_version", "Monitor"),
    ("Maximo Application Suite", "predict", "ibm-mas-predict", "mas_predict_version", "Predict"),
    ("Maximo Application Suite", "optimizer", "ibm-mas-optimizer", "mas_optimizer_version", "Optimizer"),
    ("Maximo Application Suite", "visualinspection", "ibm-mas-visualinspection", "mas_visualinspection_version", "Visual Inspection"),
]
