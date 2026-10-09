# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

requiredParams = [
    # MAS
    "mas_catalog_version",
    "mas_instance_id",
    # Storage classes
    "storage_class_rwo",
    "storage_class_rwx",
    # Entitlement
    "ibm_entitlement_key",
    # MCPI channel
    "mcpi_channel",
    # DRO
    "dro_contact_email",
    "dro_contact_firstname",
    "dro_contact_lastname",
]

optionalParams = [
    # Pipeline
    "image_pull_policy",
    "service_account_name",
    "skip_pre_check",
    # Catalogue
    "mas_catalog_digest",
    # Certificate Manager
    "cert_manager_provider",
    "cert_manager_action",
    # SLS
    "sls_namespace",
    "sls_channel",
    "sls_entitlement_file",
    "sls_action",
    # DRO
    "dro_action",
    "dro_namespace",
    # Dev Mode
    "artifactory_username",
    "artifactory_token",
    # Notifications
    "slack_token",
    "slack_channel",
]
