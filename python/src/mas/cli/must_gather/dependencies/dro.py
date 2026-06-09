# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""IBM Data Reporter Operator dependency collector."""

import logging

logger = logging.getLogger(__name__)

# DRO-specific custom resources to collect (apiVersion, kind)
DRO_RESOURCES = [
    ("marketplace.redhat.com/v1alpha1", "DataReporterConfig"),
    ("marketplace.redhat.com/v1alpha1", "MarketplaceConfig"),
    ("marketplace.redhat.com/v1alpha1", "MeterReport"),
    ("marketplace.redhat.com/v1beta1", "MeterBase"),
    ("marketplace.redhat.com/v1alpha1", "RazeeDeployment"),
    ("marketplace.redhat.com/v1beta1", "MeterDefinition"),
]
