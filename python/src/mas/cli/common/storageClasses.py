# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Storage class selection shared by the install and upgrade commands.

One implementation of the RWO / RWX storage class selection, covering both
the classic interactive CLI flow (prompt_toolkit prompts validated against
the cluster) and the Textual TUI flow (dropdowns populated from the same
lookup, with the auto-detected provider's classes pre-selected), so that
neither the commands nor their future TUI workflows re-implement it:

- **Lookup** (:meth:`StorageClassMixin.lookupStorageClasses`): the sorted
  cluster storage class names plus ``mas.devops`` provider detection
  (``KNOWN_STORAGE_PROVIDERS``), memoized for the session.  This single
  lookup feeds the TUI dropdown options, the pre-selected defaults, the
  detected-provider context row, and the non-TUI prompt flows.

- **Selection** (:meth:`StorageClassMixin.configStorageClasses`): the
  resolution flow with two knobs for the commands' policy differences.
  ``cliArgsWin`` (upgrade) validates already-provided values and uses them
  as-is; the install flavour offers the auto-detected classes as the
  default and lets the user confirm or override.  ``allowRwxNone``
  (install) permits ``"none"`` as the RWX class for clusters with no
  suitable ReadWriteMany class.
"""

import logging
from types import SimpleNamespace
from typing import List, Optional

from prompt_toolkit import HTML, print_formatted_text, prompt

from mas.cli.validators import StorageClassValidator
from mas.devops.mas import getDefaultStorageClasses
from mas.devops.ocp import getStorageClass, getStorageClasses

logger = logging.getLogger(__name__)


class StorageClassMixin:
    """RWO / RWX storage class selection shared by install and upgrade.

    Mixed into ``InstallApp`` and ``UpgradeApp``.  Requires the host class
    to provide ``self.dynamicClient``, ``self.params``, ``self.tuiMode``,
    ``self.noConfirm``, ``self.getParam`` / ``self.setParam``,
    ``self.printDescription``, ``self.yesOrNo`` and ``self.fatalError``
    (any ``BaseApp`` subclass).

    Attributes populated by :meth:`lookupStorageClasses`:
        detectedStorageClasses: The ``mas.devops.mas.getDefaultStorageClasses``
            result (provider / providerName / rwo / rwx), or None-equivalent
            when no known provider is detected.
        detectedStorageProviderName: Human-readable detected provider name,
            or None — surfaced by the TUI storage class step's context row
            and usable in review summaries.
        storageClassProvider: Provider identifier ("ocs", "ibmc", …) or
            "custom" once the user overrides the detected classes.
    """

    def lookupStorageClasses(self) -> List[str]:
        """Return the cluster's storage class names, caching provider detection.

        Memoized for the session (one CLI session talks to one cluster):
        the first call lists the storage classes and runs the supported-
        provider detection, caching both on the app; subsequent calls (the
        RWO and RWX dropdowns each load their options, the non-TUI flow
        re-checks) reuse the cached result.

        Returns:
            list[str]: Sorted storage class names available on the cluster.
        """
        cached = getattr(self, "_storageClassOptions", None)
        if cached is not None:
            return cached

        names = sorted(storageClass.metadata.name for storageClass in getStorageClasses(self.dynamicClient))
        detected: SimpleNamespace = getDefaultStorageClasses(self.dynamicClient)
        self.detectedStorageClasses = detected
        self.detectedStorageProviderName = detected.providerName if detected.provider is not None else None
        self._storageClassOptions = names
        logger.debug(f"Storage class lookup: {len(names)} classes, detected provider: {detected.provider}")
        return names

    def _printDetectedStorageClasses(self, detected: SimpleNamespace) -> None:
        """Print the auto-detected provider and its classes (non-TUI flows).

        Args:
            detected (SimpleNamespace): The getDefaultStorageClasses result
                with a non-None provider.
        """
        print_formatted_text(HTML(f"<MediumSeaGreen>Storage provider auto-detected: {detected.providerName}</MediumSeaGreen>"))
        print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteOnce): {detected.rwo}</LightSlateGrey>"))
        print_formatted_text(HTML(f"<LightSlateGrey>  - Storage class (ReadWriteMany): {detected.rwx}</LightSlateGrey>"))

    def promptForStorageClasses(self, allowRwxNone: bool = False, onlyMissing: bool = False) -> None:
        """Prompt for the RWO and RWX storage classes (classic interactive flow).

        Lists the cluster's storage classes, then prompts for both classes
        with ``StorageClassValidator`` so a typo fails at the prompt rather
        than when the pipeline provisions volumes.

        Args:
            allowRwxNone (bool): When True, note that ``"none"`` is a valid
                ReadWriteMany answer for clusters without a suitable class
                (the install flavour).  Defaults to False.
            onlyMissing (bool): When True, skip the prompt for a class whose
                param is already set (the upgrade flavour preserves a
                partially-provided CLI arg).  Defaults to False.
        """
        description = ["Select the ReadWriteOnce and ReadWriteMany storage classes to use from the list below:"]
        if allowRwxNone:
            description.append(
                "Enter 'none' for the ReadWriteMany storage class if you do not have a suitable class available in the cluster, however this will limit what can be installed"
            )
        self.printDescription(description)
        for storageClass in getStorageClasses(self.dynamicClient):
            print_formatted_text(HTML(f"<LightSlateGrey>  - {storageClass.metadata.name}</LightSlateGrey>"))
        print()

        validator = StorageClassValidator()
        if not onlyMissing or not self.getParam("storage_class_rwo"):
            self.params["storage_class_rwo"] = prompt(
                HTML("<Yellow>ReadWriteOnce (RWO) storage class</Yellow> "),
                validator=validator,
                validate_while_typing=False,
            )
        if not onlyMissing or not self.getParam("storage_class_rwx"):
            self.params["storage_class_rwx"] = prompt(
                HTML("<Yellow>ReadWriteMany (RWX) storage class</Yellow> "),
                validator=validator,
                validate_while_typing=False,
            )
        self.storageClassProvider = "custom"

    def configStorageClasses(
        self,
        cliArgsWin: bool = True,
        allowRwxNone: bool = False,
        intro: Optional[List[str]] = None,
        noDetectionTuiMessage: str = "No storage classes could be detected. Enter the ReadWriteOnce and ReadWriteMany storage classes to use on this step.",
        noDetectionFatalMessage: str = "No storage classes could be detected and --no-confirm is set. Please re-run with --storage-class-rwo and --storage-class-rwx.",
    ) -> None:
        """Resolve the ``storage_class_rwo`` and ``storage_class_rwx`` params.

        Shared resolution flow, in priority order:

        1. Values already provided (CLI flags on the non-TUI path, dropdown
           selections on the TUI path) are validated against the cluster.
        2. The auto-detected provider's classes — displayed (non-TUI) and
           either used directly or offered for confirmation, per ``cliArgsWin``.
        3. The interactive prompt pair (non-TUI) / a fatal error naming the
           step's inputs (TUI) / a fatal error naming the flags
           (``--no-confirm``).

        Args:
            cliArgsWin (bool): Upgrade semantics — fully-provided values are
                used as-is and the detected classes are auto-accepted under
                ``--no-confirm``.  When False (install semantics), the
                detected classes are written as the offered default and the
                user confirms or overrides them.  Defaults to True.
            allowRwxNone (bool): Permit ``"none"`` as the ReadWriteMany
                class (install flavour — clusters with no suitable RWX
                class).  Defaults to False.
            intro (list[str], optional): Optional heading paragraphs printed
                before resolution starts (the install flavour's "Configure
                Storage Class Usage" block).  Defaults to None.
            noDetectionTuiMessage (str): Fatal error shown when no provider
                is detected in TUI mode; names the step's inputs.
            noDetectionFatalMessage (str): Fatal error shown when no provider
                is detected and ``--no-confirm`` is set; names the CLI flags.
        """
        if intro is not None:
            self.printDescription(intro)

        # 1. Validate any values already provided (CLI args / TUI dropdown
        #    selections).  "none" is a valid RWX answer in the install
        #    flavour, exempt from cluster validation.
        rwo = self.getParam("storage_class_rwo")
        rwx = self.getParam("storage_class_rwx")
        if rwo and getStorageClass(self.dynamicClient, rwo) is None:
            self.fatalError(f"Storage class '{rwo}' specified via --storage-class-rwo is not available on this cluster.")
            return
        if rwx and not (allowRwxNone and rwx == "none") and getStorageClass(self.dynamicClient, rwx) is None:
            self.fatalError(f"Storage class '{rwx}' specified via --storage-class-rwx is not available on this cluster.")
            return

        if cliArgsWin:
            # Both provided and valid — nothing more to do
            if rwo and rwx:
                logger.debug(f"Using storage classes from CLI args: RWO={rwo} RWX={rwx}")
                return

        # 2. Auto-detection (memoized; also populates the TUI dropdown data)
        self.lookupStorageClasses()
        detected = getattr(self, "detectedStorageClasses", None)

        if not cliArgsWin:
            # Install flavour: the detected classes are written as the
            # offered default; when values were already provided (CLI flags
            # without detection) the same confirmation question effectively
            # asks whether to keep them.
            if detected is not None and detected.provider is not None:
                self.storageClassProvider = detected.provider
                if not self.tuiMode:
                    self._printDetectedStorageClasses(detected)
                self.params["storage_class_rwo"] = detected.rwo
                self.params["storage_class_rwx"] = detected.rwx

            overrideStorageClasses = False
            if self.getParam("storage_class_rwx"):
                overrideStorageClasses = not self.yesOrNo("Use the auto-detected storage classes")

            if not self.getParam("storage_class_rwx") or overrideStorageClasses:
                self.promptForStorageClasses(allowRwxNone=allowRwxNone)
            return

        # Upgrade flavour: detected classes are used directly (auto-accepted
        # under --no-confirm and in the TUI, where the dropdowns already
        # pre-selected them), or offered for confirmation.
        if detected is not None and detected.provider is not None:
            self.storageClassProvider = detected.provider
            if not self.tuiMode:
                self._printDetectedStorageClasses(detected)

            useDetected = True
            if not self.noConfirm:
                useDetected = self.yesOrNo("Use the auto-detected storage classes")

            if useDetected:
                self.params["storage_class_rwo"] = detected.rwo
                self.params["storage_class_rwx"] = detected.rwx
                logger.debug(f"Using auto-detected storage classes: RWO={detected.rwo} RWX={detected.rwx}")
                return

        # 3. No provider detected or user declined — fail fast in
        #    non-interactive modes
        if self.noConfirm:
            if self.tuiMode:
                # The storage class step's dropdowns are the TUI equivalent
                # of the CLI flags named in the classic message
                self.fatalError(noDetectionTuiMessage)
            self.fatalError(noDetectionFatalMessage)
            return

        self.promptForStorageClasses(allowRwxNone=allowRwxNone, onlyMissing=True)
