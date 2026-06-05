# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""SLS (Suite License Service) must-gather collector."""

from .license_service import discoverSLSNamespaces, collectSLSNamespace, generateSLSSummary  # noqa: F401

__all__ = ["discoverSLSNamespaces", "collectSLSNamespace", "generateSLSSummary"]

# Made with Bob
