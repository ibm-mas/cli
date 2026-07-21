# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Catalog validation and installed-instance review mixin for the update command.

Provides ``CatalogMixin`` which is mixed into ``UpdateApp`` to supply all
methods that answer "what is installed now and what catalog are we moving to?"
"""

import logging
from typing import Callable

from kubernetes.dynamic.exceptions import ResourceNotFoundError

from mas.devops.data import getCatalog
from mas.devops.ocp import getClusterVersion, isClusterVersionInRange
from mas.devops.mas import listMasInstances, getCurrentCatalog
from mas.devops.aiservice import listAiServiceInstances

logger = logging.getLogger(__name__)


class CatalogMixin:
    """Mixin providing catalog validation and installed-instance review for UpdateApp.

    All methods read from ``self.dynamicClient``, ``self.params`` (via
    ``getParam``/``setParam``), and the ``self.installedCatalogId`` attribute
    that is set by ``reviewCurrentCatalog()``.
    """

    def reviewCurrentCatalog(self) -> None:
        """Detect and display the currently installed Maximo Operator Catalog.

        Sets ``self.installedCatalogId`` to the catalog ID string, or ``None``
        when the identity cannot be determined.  Calls ``fatalError`` when no
        catalog is found at all.
        """
        catalogInfo = getCurrentCatalog(self.dynamicClient)
        self.installedCatalogId = None
        if catalogInfo is None:
            self.fatalError("Unable to locate existing install of the IBM Maximo Operator Catalog")
        elif catalogInfo["catalogId"] is None:
            self.printWarning("Unable to determine identity & version of currently installed ibm-maximo-operator-catalog")
        else:
            self.installedCatalogId = catalogInfo["catalogId"]
            self.printH1("Review Installed Catalog")
            self.printDescription(
                [f"The currently installed Maximo Operator Catalog is <u>{catalogInfo['displayName']}</u>", f" <u>{catalogInfo['image']}</u>"]
            )

    def reviewMASInstance(self) -> bool:
        """Review all MAS Suite instances on the cluster.

        Returns:
            bool: True when at least one Suite instance is found.
        """
        return self.reviewInstances(listMasInstances, "MAS", "Suite.core.mas.ibm.com/v1")

    def reviewAiServiceInstance(self) -> bool:
        """Review all AI Service instances on the cluster.

        Returns:
            bool: True when at least one AI Service instance is found.
        """
        return self.reviewInstances(listAiServiceInstances, "AI Service", "AIServiceApp.aiservice.ibm.com/v1", "aiservice_instance_ids")

    def reviewInstances(self, getInstances: Callable, name: str, kind: str, instanceParamKey: str = "") -> bool:
        """Review instances returned by a list function and print a summary.

        Args:
            getInstances (Callable): Zero-argument callable returning a list of
                instance dicts (e.g. ``listMasInstances``).
            name (str): Human-readable resource type label (e.g. "MAS").
            kind (str): Kubernetes kind string used in fallback messages.
            instanceParamKey (str, optional): Param key to populate with a
                comma-separated list of instance IDs.  Defaults to "".

        Returns:
            bool: True when at least one instance is found.
        """
        self.printH1(f"Review {name} Instances")
        try:
            instances = getInstances(self.dynamicClient)

            if len(instances) == 0:
                if instanceParamKey != "":
                    self.setParam(instanceParamKey, "")
                self.printDescription([f"No {name} instances were detected on the cluster"])
                return False

            if instanceParamKey != "":
                self.setParam(instanceParamKey, "")
                for instance in instances:
                    param = self.getParam(instanceParamKey)
                    self.setParam(instanceParamKey, f"{param},{instance['metadata']['name']}".lstrip(","))

            self.printDescription([f"The following {name} instances are installed on the target cluster and will be affected by the catalog update:"])
            for instance in instances:
                instanceId = instance["metadata"]["name"]
                reconciledVersion = self.getReconciledVersion(instance)
                self.printDescription([f"- <u>{instanceId}</u> v{reconciledVersion}"])
            return True
        except ResourceNotFoundError:
            if instanceParamKey != "":
                self.setParam(instanceParamKey, "")
            self.printDescription([f"No {name} instances were detected on the cluster ({kind} API is not available)"])
            return False

    def getCatalogOptions(self) -> list:
        """Return the update-eligible catalog version options.

        These are the same entries shown in the interactive ``chooseCatalog``
        prompt — a short, curated list of recent releases.

        Returns:
            list: Ordered list of catalog version strings, newest first.
        """
        return [
            "v9-260625-amd64",
            "v9-260527-amd64",
            "v9-260430-amd64",
        ]

    def chooseCatalog(self) -> None:
        """Interactively prompt the user to select a target catalog version."""
        self.printH1("Select IBM Maximo Operator Catalog Version")
        self.printDescription(
            [
                "Select MAS Catalog",
                "  1) Jun 25 2026 Update (MAS 9.2.0, 9.1.19, 9.0.27, 8.11.34, &amp; 8.10.37)",
                "  2) May 27 2026 Update (MAS 9.1.16, 9.0.24, 8.11.34, &amp; 8.10.37)",
                "  3) Apr 30 2026 Update (MAS 9.1.14, 9.0.23, 8.11.33, &amp; 8.10.36)",
            ]
        )
        self.promptForListSelect("Select catalog version", self.getCatalogOptions(), "mas_catalog_version", default=1)

    def checkCatalog(self) -> None:
        """Validate the chosen catalog against the current cluster state.

        Loads ``self.chosenCatalog`` and checks OCP compatibility and catalog
        ordering.  Raises ``ValueError`` on failure so it is safe to use as a
        TUI step validator.

        Raises:
            ValueError: When the catalog is incompatible with OCP or is older
                than the installed catalog.
        """
        ocpVersion = getClusterVersion(self.dynamicClient)
        self.chosenCatalog = getCatalog(self.getParam("mas_catalog_version"))
        supportedReleases = self.chosenCatalog.get("ocp_compatibility", [])
        if len(supportedReleases) > 0 and not isClusterVersionInRange(ocpVersion, supportedReleases):
            raise ValueError(
                f"IBM Maximo Operator Catalog {self.getParam('mas_catalog_version')} is not compatible with OpenShift v{ocpVersion}.  "
                f"Compatible OpenShift releases are {supportedReleases}"
            )

        if self.installedCatalogId is not None and self.installedCatalogId > self.getParam("mas_catalog_version"):
            raise ValueError(
                f"Selected catalog is older than the currently installed catalog.  "
                f"Unable to update catalog from {self.installedCatalogId} to {self.getParam('mas_catalog_version')}"
            )

    def validateCatalog(self) -> None:
        """Validate the chosen catalog, calling fatalError on failure.

        Wraps ``checkCatalog`` for the non-interactive path where a validation
        failure should terminate the process.
        """
        try:
            self.checkCatalog()
        except ValueError as e:
            self.fatalError(str(e))
