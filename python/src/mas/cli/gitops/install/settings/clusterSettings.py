# *****************************************************************************
# Copyright (c) 2024, 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import logging
from typing import List
from prompt_toolkit import prompt, print_formatted_text, HTML

from mas.devops.ocp import getStorageClasses
from mas.devops.mas import getDefaultStorageClasses
from mas.cli.validators import StorageClassValidator

logger = logging.getLogger(__name__)


class GitOpsInstallClusterSettingsMixin():
    """
    Mixin class for managing cluster-level configuration settings.

    This class provides methods for configuring cluster-wide resources:
    - IBM Operator Catalog
    - Certificate Manager (Red Hat Cert Manager)
    - Storage classes (RWO and RWX)
    - Optional cluster operators (DRO, GPU, etc.)
    """

    # Type stubs for methods provided by BaseApp (available at runtime through multiple inheritance)
    def printH2(self, message: str) -> None:
        ...  # type: ignore

    def printDescription(self, content: List[str]) -> None:
        ...  # type: ignore

    def yesOrNo(self, message: str, param: str = None) -> bool:
        ...  # type: ignore

    def setParam(self, param: str, value: str) -> None:
        ...  # type: ignore

    def getParam(self, param: str) -> str:
        ...  # type: ignore

    def promptForString(self, message: str, param: str = None, default: str = "", isPassword: bool = False) -> str:
        ...  # type: ignore

    showAdvancedOptions: bool  # type: ignore
    dynamicClient: any  # type: ignore
    params: dict  # type: ignore

    def configStorageClasses(self) -> None:
        """
        Configure storage classes for ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes.

        This method auto-detects available storage classes and allows the user to:
        - Accept auto-detected storage classes
        - Override with custom storage classes
        - Set 'none' for RWX if not available (limits installation options)
        """
        logger.debug("Configuring storage classes")

        self.printH2("Storage Classes")
        self.printDescription([
            "Maximo Application Suite and its dependencies require storage classes that support ReadWriteOnce (RWO) and ReadWriteMany (RWX) access modes:",
            "  - ReadWriteOnce volumes can be mounted as read-write by multiple pods on a single node.",
            "  - ReadWriteMany volumes can be mounted as read-write by multiple pods across many nodes.",
            ""
        ])

        # Auto-detect storage classes
        defaultStorageClasses = getDefaultStorageClasses(self.dynamicClient)
        if defaultStorageClasses.provider is not None:
            print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {defaultStorageClasses.providerName}</MediumSeaGreen>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteOnce): {defaultStorageClasses.rwo}</LightSlateGrey>"))
            print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteMany): {defaultStorageClasses.rwx}</LightSlateGrey>"))
            self.params["storage_class_rwo"] = defaultStorageClasses.rwo
            self.params["storage_class_rwx"] = defaultStorageClasses.rwx

        overrideStorageClasses = False
        if "storage_class_rwx" in self.params and self.params["storage_class_rwx"] != "":
            overrideStorageClasses = not self.yesOrNo("Use the auto-detected storage classes")

        if "storage_class_rwx" not in self.params or self.params["storage_class_rwx"] == "" or overrideStorageClasses:
            self.printDescription([
                "Select the ReadWriteOnce and ReadWriteMany storage classes to use from the list below:",
                "Enter 'none' for the ReadWriteMany storage class if you do not have a suitable class available in the cluster, however this will limit what can be installed"
            ])
            for storageClass in getStorageClasses(self.dynamicClient):
                print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))

            self.params["storage_class_rwo"] = prompt(message=HTML('<Yellow>ReadWriteOnce (RWO) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)
            self.params["storage_class_rwx"] = prompt(message=HTML('<Yellow>ReadWriteMany (RWX) storage class</Yellow> '), validator=StorageClassValidator(), validate_while_typing=False)

    def configClusterOperators(self) -> None:
        """
        Configure optional cluster operators.

        Collects selections for:
        - DRO (Data Reporter Operator) - for license reporting
        - GPU Operator - for GPU workloads
        - Cert Manager - Red Hat Certificate Manager
        - NFD (Node Feature Discovery) - for GPU operator
        - Other cluster-level operators
        """
        logger.debug("Configuring cluster operators")

        self.printH2("Cluster Operators")
        self.printDescription([
            "Select which cluster-level operators to install.",
            "These operators provide cluster-wide capabilities."
        ])

        # DRO (Data Reporter Operator) - typically required for licensing
        if not hasattr(self, 'install_dro'):
            self.install_dro = self.yesOrNo("Install Data Reporter Operator (DRO)")
            self.setParam("install_dro", str(self.install_dro).lower())

        # GPU Operator (requires NFD)
        if not hasattr(self, 'install_gpu_operator'):
            self.install_gpu_operator = self.yesOrNo("Install NVIDIA GPU Operator")
            self.setParam("install_gpu_operator", str(self.install_gpu_operator).lower())

            if self.install_gpu_operator:
                # NFD is required for GPU operator
                self.setParam("install_nfd", "true")

        # Certificate Manager
        if not hasattr(self, 'install_cert_manager'):
            self.install_cert_manager = self.yesOrNo("Install Red Hat Certificate Manager")
            self.setParam("install_cert_manager", str(self.install_cert_manager).lower())

    def configClusterCatalog(self) -> None:
        """
        Configure IBM Operator Catalog settings.

        Collects:
        - mas_catalog_version: Catalog version (e.g., v9-260305-amd64)
        - mas_catalog_image: Custom catalog image (optional)
        - ibm_entitlement_key: IBM entitlement key for pulling images
        """
        logger.debug("Configuring IBM Operator Catalog")

        self.printH2("IBM Operator Catalog")
        self.printDescription([
            "Configure the IBM Maximo Operator Catalog.",
            "The catalog version determines which MAS versions are available."
        ])

        # Check if values are already set (non-interactive mode)
        if not self.getParam("mas_catalog_version"):
            self.promptForString("Catalog version", "mas_catalog_version",
                                 default="v9-260305-amd64")

        # IBM Entitlement Key
        if not self.getParam("ibm_entitlement_key"):
            self.promptForString("IBM entitlement key", "ibm_entitlement_key", isPassword=True)

        # Optional: Custom catalog image (for development/testing)
        if self.showAdvancedOptions:
            if self.yesOrNo("Use custom catalog image"):
                self.promptForString("Custom catalog image", "mas_catalog_image")

    def validateClusterSettings(self) -> tuple[bool, list[str]]:
        """
        Validate cluster configuration settings.

        Checks:
        - Catalog version is valid
        - Storage classes exist
        - Required operators are configured

        Returns:
            tuple: (is_valid, list of error messages)
        """
        # TODO: Implement cluster settings validation in Phase 3
        logger.info("Validating cluster settings (stub)")
        return True, []
