# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openshift.dynamic import DynamicClient


@dataclass
class InstallContext:
    """Centralized state for MAS installation.

    This is a Python dataclass - a special class decorator that automatically generates
    common methods like __init__, __repr__, and __eq__ based on the class attributes.
    Think of it as a structured container for related data with type hints.

    Benefits of dataclasses:
    - Automatic __init__ method (no need to write self.x = x for every attribute)
    - Type hints for all attributes (better IDE support and type checking)
    - Less boilerplate code compared to regular classes

    This class separates Tekton pipeline parameters (all strings) from CLI runtime state (typed).
    This eliminates the need for extensive TYPE_CHECKING stubs in mixins.

    The params dict contains string-only values that are passed to Tekton PipelineRun.
    All other attributes are typed CLI runtime state.
    """

    # ============================================================================
    # Tekton Pipeline Parameters (all strings, passed to PipelineRun)
    # ============================================================================
    params: dict[str, str] = field(default_factory=dict)

    # ============================================================================
    # CLI Runtime State (typed attributes)
    # ============================================================================

    # Mode flags
    devMode: bool = False
    showAdvancedOptions: bool = False
    noConfirm: bool = False
    isInteractiveMode: bool = True
    licenseAccepted: bool = False

    # Application installation flags
    installAssist: bool = False
    installIoT: bool = False
    installManage: bool = False
    installMonitor: bool = False
    installPredict: bool = False
    installInspection: bool = False
    installOptimizer: bool = False
    installFacilities: bool = False
    installAIService: bool = False
    installArcgis: bool = False

    # Application-specific state
    isManageFoundation: bool = False
    manageAppName: str = "Manage"
    enableKafkaImageProcessor: bool = False
    # Note: Using tuple instead of list for supportedLanguages because:
    # 1. It's immutable (constant data that never changes)
    # 2. Can be assigned directly in dataclass (mutable defaults like lists require field(default_factory=...))
    # 3. More memory efficient for constant data
    supportedLanguages: tuple[str, ...] = (
        "AR",
        "CS",
        "DA",
        "DE",
        "EN",
        "ES",
        "FI",
        "FR",
        "HE",
        "HR",
        "HU",
        "IT",
        "JA",
        "KO",
        "NL",
        "NO",
        "PL",
        "PT-BR",
        "RU",
        "SK",
        "SL",
        "SV",
        "TR",
        "UK",
        "ZH-CN",
        "ZH-TW",
    )

    # Cluster state
    dynamicClient: DynamicClient | None = None
    isSNO: bool | None = None
    isAirgap: bool | None = None
    architecture: str | None = None

    # Catalog state
    chosenCatalog: dict[str, str] | None = None
    catalogDigest: str = ""
    catalogMongoDbVersion: str = ""
    catalogDb2Channel: str = ""
    catalogCp4dVersion: str = ""

    # File paths
    localConfigDir: str | None = None
    manualCertsDir: str | None = None
    slsLicenseFileLocal: str | None = None
    db2LicenseFileLocal: str | None = None
    aiserviceTenantSchedulingConfigFileLocal: str | None = None

    # Secrets (for Tekton pipeline)
    additionalConfigsSecret: dict[str, str] | None = None
    podTemplatesSecret: dict[str, str] | None = None
    slsLicenseFileSecret: dict[str, str] | None = None
    db2LicenseFileSecret: dict[str, str] | None = None
    certsSecret: dict[str, str] | None = None
    aiserviceConfigSecret: dict[str, str] | None = None

    # Storage configuration
    pipelineStorageClass: str = ""
    pipelineStorageAccessMode: str = ""

    # Operational mode
    operationalMode: int = 1  # 1=production, 2=non-production

    # SLS configuration
    slsMode: int = 1

    # Templates directory
    templatesDir: str = ""

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def getParam(self, key: str, default: str = "") -> str:
        """Get Tekton pipeline parameter.

        Args:
            key: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value as string
        """
        return self.params.get(key, default)

    def setParam(self, key: str, value: str) -> None:
        """Set Tekton pipeline parameter.

        Args:
            key: Parameter name
            value: Parameter value (must be string)

        Raises:
            TypeError: If value is not a string (runtime check for untyped callers)
        """
        # Runtime type check for safety when called from untyped code
        # Type checkers will flag this as unreachable, which is expected
        if not isinstance(value, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(  # pyright: ignore[reportUnreachable]
                f"Pipeline params must be strings, got {type(value).__name__} for {key}"
            )
        self.params[key] = value

    def getSelectedApps(self) -> list[str]:
        """Get list of selected applications for installation.

        Returns:
            List of application names (always includes 'core')
        """
        apps = ["core"]
        if self.installAssist:
            apps.append("assist")
        if self.installIoT:
            apps.append("iot")
        if self.installManage:
            apps.append("manage")
        if self.installMonitor:
            apps.append("monitor")
        if self.installPredict:
            apps.append("predict")
        if self.installInspection:
            apps.append("visualinspection")
        if self.installOptimizer:
            apps.append("optimizer")
        if self.installFacilities:
            apps.append("facilities")
        if self.installAIService:
            apps.append("aiservice")
        if self.installArcgis:
            apps.append("arcgis")
        return apps
