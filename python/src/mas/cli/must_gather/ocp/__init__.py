# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""OCP resource collectors for must-gather."""

from .cluster import collectClusterResources  # noqa: F401
from .nodes import collectNodes  # noqa: F401
from .airgap import collectAirgapResources, detectAirgapEnvironment  # noqa: F401
from .marketplace import collectMarketplaceResources  # noqa: F401
from .operators import collectOperatorResources  # noqa: F401

__all__ = [
    "collectClusterResources",
    "collectNodes",
    "collectAirgapResources",
    "detectAirgapEnvironment",
    "collectMarketplaceResources",
    "collectOperatorResources",
]

# Made with Bob
