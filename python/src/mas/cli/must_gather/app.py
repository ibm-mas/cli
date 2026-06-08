# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Main application class for must-gather command."""

import hashlib
import logging
import os
from typing import Optional, List

import requests
from mas.cli import BaseApp
from .arg_parser import createArgumentParser
from .output import OutputManager
from .timer import Timer
from .common import collectResourcesParallel, collectSecrets, collectPods, getIBMCRDs
from . import ocp
from . import dependencies
from .dependencies import sls
from .mas import core as mas_core
from .mas import apps as mas_apps
from .mas import pipelines as mas_pipelines
from .aiservice import instance as aiservice_instance
from .aiservice import pipelines as aiservice_pipelines
from .aiservice import tenant as aiservice_tenant
from .argo import applications as argo
from . import web_viewer
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from halo import Halo

logger = logging.getLogger(__name__)


class MustGatherApp(BaseApp):
    """Must-gather application for collecting diagnostic information.

    This class orchestrates the collection of diagnostic information from
    MAS clusters, including OCP resources, dependencies, MAS instances,
    and AI Service instances.
    """

    def __init__(self):
        """Initialize must-gather application."""
        super().__init__()
        self.dynClient: Optional[DynamicClient] = None
        self.printerColumnsCache: dict = {}
        self.ibmCRDsList: list = []

    def _initializeKubernetesClient(self):
        """Initialize Kubernetes Dynamic Client.

        Loads kubeconfig and creates a DynamicClient for API access.
        """
        if not self.dynClient:
            config.load_kube_config()
            self.dynClient = DynamicClient(config.new_client_from_config())

    def mustGather(self, args):
        """Execute must-gather collection or serve web viewer.

        Args:
            args: Command-line arguments list

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Parse arguments
        parser = createArgumentParser()
        parsedArgs = parser.parse_args(args)

        # Handle serve command
        if parsedArgs.command == "serve":
            from mas.cli.must_gather.web_viewer.__main__ import serve_viewer

            return serve_viewer(directory=parsedArgs.dir, port=parsedArgs.port)

        # Handle collect command (default) or when no command specified
        # If no command specified, treat as collect for backward compatibility
        if parsedArgs.command is None or parsedArgs.command == "collect":
            return self._collectMustGather(parsedArgs)

        # Unknown command
        parser.print_help()
        return 1

    def _collectMustGather(self, parsedArgs):
        """Execute must-gather collection.

        Args:
            parsedArgs: Parsed command-line arguments

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """

        # Initialize output manager
        outputManager = OutputManager(parsedArgs.directory, parsedArgs.keep_files)
        outputManager.initialize()
        outputManager.setupLogging()

        # Print header information
        self.printH1("MAS Must-Gather")
        self.printDescription(
            [
                f"Must gather will be saved to: {outputManager.getArchivePath()}",
                "For help reviewing the content refer to:",
                "https://www.ibm.com/support/pages/how-review-maximo-application-suite-must-gather",
            ]
        )

        # Start overall timer
        overallTimer = Timer()
        overallTimer.start()

        # Initialize Kubernetes client
        self._initializeKubernetesClient()

        # Process CRDs first (always, even with --no-ocp)
        # This is needed for printer columns and IBM CRD discovery
        if parsedArgs.no_ocp:
            # Process CRDs without collecting other OCP resources
            from mas.cli.must_gather.common.crd_processor import processCRDs

            if self.dynClient is None:
                raise RuntimeError("Kubernetes client not initialized")

            logger.info("Processing CRDs for printer columns (--no-ocp mode)")
            self.printerColumnsCache, self.ibmCRDsList = processCRDs(self.dynClient, outputManager.outputDir)
            logger.info(f"Processed {len(self.printerColumnsCache)} CRDs, identified {len(self.ibmCRDsList)} IBM CRDs")

        # Collect OCP resources (unless --no-ocp flag is set)
        if not parsedArgs.no_ocp:
            self.printH1("OpenShift Container Platform")
            ocpTimer = Timer()
            ocpTimer.start()
            collectionResult = self.collectOCP(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only)
            elapsed = ocpTimer.stop()
            if collectionResult:
                print()
                self.printHighlight(f"OCP collection completed in {elapsed} seconds")

        # Collect dependency resources (unless --no-dependencies flag is set)
        if not parsedArgs.no_dependencies:
            self.printH1("In-Cluster Dependencies")
            depTimer = Timer()
            depTimer.start()
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            collectionResult = self.collectDependencies(
                outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only, noLogs=parsedArgs.no_logs, masInstanceIds=masInstanceIds
            )
            elapsed = depTimer.stop()
            if collectionResult:
                print()
                self.printHighlight(f"Dependencies collection completed in {elapsed} seconds")

        # Collect SLS resources (unless --no-sls flag is set)
        if not parsedArgs.no_sls:
            self.printH1("Suite License Service")
            slsTimer = Timer()
            slsTimer.start()
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            collectionResult = self.collectSLS(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only, masInstanceIds=masInstanceIds)
            elapsed = slsTimer.stop()
            if collectionResult:
                print()
                self.printHighlight(f"SLS collection completed in {elapsed} seconds")

        # Collect MAS resources
        self.printH1("IBM Maximo Application Suite")
        masTimer = Timer()
        masTimer.start()
        masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
        masAppIds = parsedArgs.mas_app_ids.split(",") if parsedArgs.mas_app_ids else None
        collectionResult = self.collectMAS(
            outputDir=outputManager.outputDir,
            noDetail=parsedArgs.summary_only,
            noLogs=parsedArgs.no_logs,
            masInstanceIds=masInstanceIds,
            masAppIds=masAppIds,
        )
        elapsed = masTimer.stop()
        if collectionResult:
            print()
            self.printHighlight(f"MAS collection completed in {elapsed} seconds")

        # Collect AI Service resources
        self.printH1("IBM Maximo AI Service")
        aiserviceTimer = Timer()
        aiserviceTimer.start()
        collectionResult = self.collectAIService(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only, noLogs=parsedArgs.no_logs)
        elapsed = aiserviceTimer.stop()
        if collectionResult:
            print()
            self.printHighlight(f"AI Service collection completed in {elapsed} seconds")

        # Collect Argo resources
        self.printH1("Argo CD")
        argoTimer = Timer()
        argoTimer.start()
        collectionResult = self.collectArgo(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only)
        elapsed = argoTimer.stop()
        if collectionResult:
            print()
            self.printHighlight(f"Argo collection completed in {elapsed} seconds")

        # Collect extra namespaces if specified
        if parsedArgs.extra_namespaces and not parsedArgs.summary_only:
            self.printH1("Extra Namespaces")
            extraTimer = Timer()
            extraTimer.start()
            collectionResult = self.collectExtraNamespaces(
                outputDir=outputManager.outputDir, extraNamespaces=parsedArgs.extra_namespaces, noDetail=parsedArgs.summary_only, noLogs=parsedArgs.no_logs
            )
            elapsed = extraTimer.stop()
            if collectionResult:
                print()
                self.printHighlight(f"Extra namespaces collection completed in {elapsed} seconds")

        # Generate cluster-wide subscriptions summary (only if OCP was collected)
        if not parsedArgs.no_ocp:
            self.printH1("Generating Subscriptions Summary")
            summaryTimer = Timer()
            summaryTimer.start()
            self.generateSubscriptionsSummary(outputDir=outputManager.outputDir)
            elapsed = summaryTimer.stop()
            self.printHighlight(f"Subscriptions summary generated in {elapsed} seconds")

        # Generate web viewer
        self.printH1("Generating Web Viewer")
        viewerTimer = Timer()
        viewerTimer.start()
        if web_viewer.generateWebViewer(outputManager.outputDir):
            elapsed = viewerTimer.stop()
            print(f"Web viewer generated in {elapsed} seconds")
            self.printHighlight(f"Run must-gather serve --dir {outputManager.outputDir} to view the must-gather")
        else:
            elapsed = viewerTimer.stop()
            print(f"⚠️  Web viewer generation failed after {elapsed} seconds (must-gather data is still available)")

        # Create archive
        self.printH1("Creating Archive")
        archivePath = outputManager.createArchive()
        print(f"Archive created: {archivePath}")

        # Upload to Artifactory if configured
        if parsedArgs.artifactory_token and parsedArgs.artifactory_upload_dir:
            self.printH2("Uploading to Artifactory")
            uploadTimer = Timer()
            uploadTimer.start()
            if self.uploadToArtifactory(
                archivePath=archivePath, artifactoryToken=parsedArgs.artifactory_token, artifactoryUploadDir=parsedArgs.artifactory_upload_dir
            ):
                elapsed = uploadTimer.stop()
                print(f"Upload completed in {elapsed} seconds")
            else:
                elapsed = uploadTimer.stop()
                print(f"❌ Upload failed after {elapsed} seconds")

        # Cleanup
        outputManager.cleanup()

        # Print completion message
        elapsed = overallTimer.stop()
        self.printH1("Completion")
        print(f"Must-gather completed in {elapsed} seconds")
        self.printHighlight(f"Must gather successfully saved to: {archivePath}")

        return 0

    def genericMustGather(
        self,
        namespace: str,
        outputDir: str,
        podsOnly: bool = False,
        secretData: bool = False,
        noLogs: bool = True,
        noDetail: bool = False,
        additionalResources: Optional[List[tuple[str, str]]] = None,
    ) -> bool:
        """Orchestrate generic must-gather collection for a namespace.

        Collects IBM custom resources, standard Kubernetes resources, secrets, and pods
        from a namespace. This is the core collection function used by various collectors.

        Args:
            namespace (str): Target namespace for collection
            outputDir (str): Base output directory
            podsOnly (bool, optional): If True, only collect pods. Defaults to False.
            secretData (bool, optional): If True, include secret data in YAML. Defaults to False.
            noLogs (bool, optional): If True, skip pod log collection. Defaults to True.
            noDetail (bool, optional): If True, skip detailed YAML collection. Defaults to False.
            additionalResources (list, optional): Additional resource types as (apiVersion, kind) tuples. Defaults to None.

        Returns:
            bool: True if collection succeeded, False if errors occurred
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"
        success = True

        # Collect IBM custom resources in parallel with Halo spinner showing progress
        if not podsOnly:
            # Discover IBM CRDs (silently - no UI output, just logging)
            # Use precomputed list if available from CRD processing
            ibmCRDsWithInstances = []
            try:
                ibmCRDs = getIBMCRDs(self.dynClient, precomputedList=self.ibmCRDsList if self.ibmCRDsList else None)
                logger.debug(f"Checking {len(ibmCRDs)} IBM CRDs for instances in namespace {namespace}")

                # Check which IBM CRDs have instances in the namespace
                for kind, apiVersion in ibmCRDs:
                    try:
                        api = self.dynClient.resources.get(api_version=apiVersion, kind=kind)
                        resources = api.get(namespace=namespace)
                        if resources.items:
                            ibmCRDsWithInstances.append((apiVersion, kind))
                            logger.debug(f"Found {len(resources.items)} {kind} instances in {namespace}")
                        else:
                            logger.debug(f"No {kind} instances in {namespace}")
                    except Exception as e:
                        logger.debug(f"Could not check {kind} in {namespace}: {e}")

                logger.info(f"Found {len(ibmCRDsWithInstances)} IBM resource types with instances in {namespace}")
            except Exception as e:
                logger.error(f"Failed to discover IBM custom resources: {str(e)}")
                print(f"❌ Failed to discover IBM custom resources: {str(e)}")
                success = False

            # Collect IBM custom resources in parallel with Halo spinner showing progress
            if ibmCRDsWithInstances:
                try:
                    totalCount = len(ibmCRDsWithInstances)
                    with Halo(text=f"Collected 0/{totalCount} IBM resource types from {namespace}", spinner=self.spinner) as h:

                        def updateProgress(completed: int, total: int):
                            h.text = f"Collected {completed}/{total} IBM resource types from {namespace}"

                        if collectResourcesParallel(
                            dynClient=self.dynClient,
                            namespace=namespace,
                            resources=ibmCRDsWithInstances,
                            outputDir=outputDir,
                            noDetail=noDetail,
                            progressCallback=updateProgress,
                        ):
                            h.stop_and_persist(symbol=self.successIcon, text=f"Collected {totalCount} IBM resource types from {namespace}")
                        else:
                            h.stop_and_persist(symbol="❌", text=f"Failed to collect some IBM resource types from {namespace} (check logs)")
                            success = False
                except Exception as e:
                    print(f"❌ Failed to collect IBM custom resources from {namespace}: {str(e)}")
                    success = False

        # Collect standard Kubernetes resources in parallel with Halo spinner showing progress
        if not podsOnly:
            standardResources = [
                ("v1", "ConfigMap"),
                ("v1", "Service"),
                ("apps/v1", "Deployment"),
                ("apps/v1", "StatefulSet"),
                ("apps/v1", "DaemonSet"),
                ("apps/v1", "ReplicaSet"),
                ("batch/v1", "Job"),
                ("batch/v1", "CronJob"),
                ("v1", "PersistentVolumeClaim"),
                ("v1", "ServiceAccount"),
                ("rbac.authorization.k8s.io/v1", "Role"),
                ("rbac.authorization.k8s.io/v1", "RoleBinding"),
                ("networking.k8s.io/v1", "NetworkPolicy"),
                ("networking.k8s.io/v1", "Ingress"),
                # Operator resources (namespace-scoped)
                ("operators.coreos.com/v1alpha1", "Subscription"),
                ("operators.coreos.com/v1alpha1", "InstallPlan"),
                ("operators.coreos.com/v2", "OperatorCondition"),
            ]

            # Add any additional resources
            if additionalResources:
                standardResources.extend(additionalResources)

            # Collect all resource types in parallel with Halo spinner showing progress
            totalCount = len(standardResources)
            with Halo(text=f"Collected 0/{totalCount} resource types from {namespace}", spinner=self.spinner) as h:

                def updateProgress(completed: int, total: int):
                    h.text = f"Collected {completed}/{total} resource types from {namespace}"

                if collectResourcesParallel(
                    dynClient=self.dynClient,
                    namespace=namespace,
                    resources=standardResources,
                    outputDir=outputDir,
                    noDetail=noDetail,
                    progressCallback=updateProgress,
                ):
                    h.stop_and_persist(symbol=self.successIcon, text=f"Collected {totalCount} resource types from {namespace}")
                else:
                    h.stop_and_persist(symbol="❌", text=f"Failed to collect some resource types from {namespace} (check logs)")
                    success = False

        # Collect secrets
        if not podsOnly:
            dataStatus = "with data" if secretData else "without data"
            with Halo(text=f"Collecting secrets from {namespace} ({dataStatus})", spinner=self.spinner) as h:
                try:
                    secretSuccess, secretCount = collectSecrets(
                        dynClient=self.dynClient, namespace=namespace, outputDir=outputDir, secretData=secretData, allNamespaces=False
                    )
                    if secretSuccess:
                        dataStatus = "with data" if secretData else "without data"
                        h.stop_and_persist(symbol=self.successIcon, text=f"Collected {secretCount} secrets from {namespace} ({dataStatus})")
                    else:
                        h.stop_and_persist(symbol="❌", text=f"Failed to collect secrets from {namespace} (check logs)")
                        success = False
                except Exception as e:
                    h.stop_and_persist(symbol="❌", text=f"Failed to collect secrets from {namespace}: {str(e)}")
                    success = False

        # Collect pods with progress tracking
        logStatus = "without logs" if noLogs else "with logs"
        with Halo(text=f"Collecting pods from {namespace} ({logStatus})", spinner=self.spinner) as h:
            try:

                def updateProgress(completed: int, total: int) -> None:
                    h.text = f"Collecting {completed}/{total} pods from {namespace} ({logStatus})"

                podSuccess, podCount = collectPods(
                    dynClient=self.dynClient,
                    namespace=namespace,
                    outputDir=outputDir,
                    podLogs=not noLogs,
                    noDetail=noDetail,
                    progressCallback=updateProgress,
                )
                if podSuccess:
                    logStatus = "without logs" if noLogs else "with logs"
                    h.stop_and_persist(symbol=self.successIcon, text=f"Collected {podCount} pods from {namespace} ({logStatus})")
                else:
                    h.stop_and_persist(symbol="❌", text=f"Failed to collect pods from {namespace} (check logs)")
                    success = False
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect pods from {namespace}: {str(e)}")
                success = False

        return success

    def collectOCP(self, outputDir: str, noDetail: bool = False) -> bool:
        """Collect OpenShift Container Platform resources.

        Orchestrates collection of OCP-specific resources including cluster resources,
        nodes, airgap configuration, marketplace resources, and operator resources.
        CRD processing results are stored in instance variables for use by other collectors.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

        Returns:
            bool: True if collection succeeded, False if errors occurred
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"
        successCount = 0
        totalCount = 0

        # Collect cluster resources (includes CRD processing)
        totalCount += 1
        with Halo(text="Collecting OCP cluster resources", spinner=self.spinner) as h:
            try:
                success, printerColumnsCache, ibmCRDsList = ocp.collectClusterResources(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail)
                if success:
                    # Store CRD processing results for use by other collectors
                    self.printerColumnsCache = printerColumnsCache
                    self.ibmCRDsList = ibmCRDsList
                    h.stop_and_persist(symbol=self.successIcon, text="OCP cluster resources collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP cluster resources (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP cluster resources: {str(e)}")

        # Collect nodes with describe output
        totalCount += 1
        with Halo(text="Collecting OCP nodes", spinner=self.spinner) as h:
            try:
                if ocp.collectNodes(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text="OCP nodes collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP nodes (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP nodes: {str(e)}")

        # Collect airgap resources (if applicable)
        totalCount += 1
        with Halo(text="Collecting OCP airgap resources", spinner=self.spinner) as h:
            try:
                if ocp.collectAirgapResources(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text="OCP airgap resources collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP airgap resources (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP airgap resources: {str(e)}")

        # Collect OpenShift Marketplace resources
        totalCount += 1
        with Halo(text="Collecting OCP marketplace resources", spinner=self.spinner) as h:
            try:
                if ocp.collectMarketplaceResources(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text="OCP marketplace resources collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP marketplace resources (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP marketplace resources: {str(e)}")

        # Note: Operator resources (Subscription, InstallPlan, OperatorCondition) are now
        # collected per-namespace as part of standard resource collection in genericMustGather()

        return successCount > 0

    def collectDependencies(self, outputDir: str, noDetail: bool = False, noLogs: bool = False, masInstanceIds: Optional[List[str]] = None) -> bool:
        """Collect in-cluster dependency resources.

        Orchestrates collection of dependency resources including IBM Common Services,
        CP4D, Db2, DRO, Certificate Manager, Kafka, Grafana, MongoDB, and SLS.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
            masInstanceIds (list, optional): List of MAS instance IDs for Db2 discovery. Defaults to None.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"
        successCount = 0
        totalCount = 0

        # IBM CloudPak for Data (includes Common Services / Foundation Services)
        self.printH2("IBM CloudPak for Data")
        totalCount += 2  # Count both Common Services and CP4D

        # Collect Common Services (Foundation Services)
        result = dependencies.collectCommonServices(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # Collect CP4D
        result = dependencies.collectCP4D(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # IBM Db2 Universal Operator
        self.printH2("IBM Db2 Universal Operator")
        totalCount += 1
        result = dependencies.collectDb2(
            dynClient=self.dynClient,
            outputDir=outputDir,
            noDetail=noDetail,
            noLogs=noLogs,
            masInstanceIds=masInstanceIds,
            genericMustGather=self.genericMustGather,
        )
        if result:
            successCount += 1

        # IBM Data Reporter Operator
        self.printH2("IBM Data Reporter Operator")
        totalCount += 1
        result = dependencies.collectDRO(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # Red Hat Certificate Manager
        self.printH2("Red Hat Certificate Manager")
        totalCount += 1
        result = dependencies.collectCertManager(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # Kafka
        self.printH2("Kafka")
        totalCount += 1
        result = dependencies.collectKafka(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # Grafana
        self.printH2("Grafana")
        totalCount += 1
        result = dependencies.collectGrafana(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        # MongoDB Community
        self.printH2("MongoDB Community")
        totalCount += 1
        result = dependencies.collectMongoDB(
            dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs, genericMustGather=self.genericMustGather
        )
        if result:
            successCount += 1

        return successCount > 0

    def collectSLS(self, outputDir: str, noDetail: bool = False, masInstanceIds: Optional[List[str]] = None) -> bool:
        """Collect IBM Suite License Service resources.

        Discovers SLS namespaces from LicenseService CRs and collects resources from each namespace.
        Note: The masInstanceIds parameter is kept for backward compatibility but is not used.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            masInstanceIds (list, optional): Unused - kept for backward compatibility. Defaults to None.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"

        # Discover SLS namespaces
        with Halo(text="Discovering SLS namespaces", spinner=self.spinner) as h:
            try:
                slsNamespaces = sls.discoverSLSNamespaces(self.dynClient, masInstanceIds=masInstanceIds)
                if slsNamespaces:
                    h.stop_and_persist(symbol=self.successIcon, text=f"Discovered {len(slsNamespaces)} SLS namespace(s): {', '.join(sorted(slsNamespaces))}")
                else:
                    h.stop_and_persist(symbol="⚠️", text="No SLS namespaces found")
                    return False
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to discover SLS namespaces: {str(e)}")
                return False

        # Collect from each discovered namespace
        successCount = 0
        for namespace in sorted(slsNamespaces):
            self.printH2(f"Namespace: {namespace}")
            try:
                with Halo(text=f"Collecting SLS resources from {namespace}", spinner=self.spinner) as h:
                    if sls.collectSLSNamespace(self.dynClient, namespace, outputDir, noDetail=noDetail):
                        h.stop_and_persist(symbol=self.successIcon, text=f"SLS resources collected from {namespace}")
                        successCount += 1
                    else:
                        h.stop_and_persist(symbol="❌", text=f"Failed to collect SLS resources from {namespace} (check logs)")
            except Exception as e:
                print(f"❌ Failed to collect SLS resources from {namespace}: {str(e)}")

        return successCount > 0

    def collectMAS(
        self,
        outputDir: str,
        noDetail: bool = False,
        noLogs: bool = False,
        masInstanceIds: Optional[List[str]] = None,
        masAppIds: Optional[List[str]] = None,
    ) -> bool:
        """Collect IBM Maximo Application Suite resources.

        Orchestrates collection of MAS Core, MAS Apps, and MAS Pipelines.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            noLogs (bool, optional): If True, skip pod log collection. Defaults to False.
            masInstanceIds (list, optional): List of MAS instance IDs to filter. If None, discovers all instances. Defaults to None.
            masAppIds (list, optional): List of MAS app IDs to collect. Defaults to None.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"

        # Discover MAS Core namespaces
        with Halo(text="Discovering MAS instances", spinner=self.spinner) as h:
            try:
                coreNamespaces = mas_core.discoverMASCoreNamespaces(self.dynClient, masInstanceIds=masInstanceIds)
                if coreNamespaces:
                    instanceCount = len(coreNamespaces)
                    instanceList = ", ".join([ns.replace("mas-", "").replace("-core", "") for ns in sorted(coreNamespaces)])
                    h.stop_and_persist(symbol=self.successIcon, text=f"Discovered {instanceCount} MAS instance(s): {instanceList}")
                else:
                    h.stop_and_persist(symbol="⚠️", text="No MAS instances found")
                    return False
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to discover MAS instances: {str(e)}")
                return False

        successCount = 0

        # Process each MAS instance
        for coreNamespace in sorted(coreNamespaces):
            # Extract instance ID from namespace (mas-{instance}-core)
            instanceId = coreNamespace[4:-5]  # Remove "mas-" prefix and "-core" suffix

            self.printH2(f"MAS Instance: {instanceId}")

            instanceTimer = Timer()
            instanceTimer.start()

            # Collect MAS Core
            self.printHighlight("Core")
            try:
                # Collect standard resources
                if self.genericMustGather(namespace=coreNamespace, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs):
                    successCount += 1
                else:
                    print(f"❌ Failed to collect MAS Core resources from {coreNamespace} (check logs)")

                # Collect reconcile logs from MAS Core operators
                mas_core.collectMASCore(dynClient=self.dynClient, namespace=coreNamespace, outputDir=outputDir, noDetail=noDetail)
            except Exception as e:
                print(f"❌ Failed to collect MAS Core from {coreNamespace}: {str(e)}")

            # Collect MAS Apps
            try:
                appNamespaces = mas_apps.discoverMASAppNamespaces(self.dynClient, masInstanceId=instanceId, masAppIds=masAppIds)
                if appNamespaces:
                    for appNamespace in sorted(appNamespaces):
                        # Extract app ID from namespace (mas-{instance}-{app})
                        appId = appNamespace[len(f"mas-{instanceId}-") :]
                        self.printHighlight(appId.capitalize())
                        try:
                            if not mas_apps.collectMASApp(
                                dynClient=self.dynClient,
                                namespace=appNamespace,
                                appId=appId,
                                outputDir=outputDir,
                                noDetail=noDetail,
                                noLogs=noLogs,
                                genericMustGather=self.genericMustGather,
                            ):
                                print(f"❌ Failed to collect {appId} resources from {appNamespace} (check logs)")
                        except Exception as e:
                            print(f"❌ Failed to collect {appId} from {appNamespace}: {str(e)}")
                else:
                    print("⏭️ No application namespaces found")
            except Exception as e:
                print(f"❌ Failed to discover MAS app namespaces for {instanceId}: {str(e)}")

            elapsed = instanceTimer.stop()
            print()
            self.printHighlight(f"Instance {instanceId} collection completed in {elapsed} seconds")

        # Collect cluster-level pipelines namespace if it exists
        # Note: Only collect mas-pipelines here; instance pipelines were already collected above
        try:
            clusterPipelineNamespaces = mas_pipelines.discoverMASPipelineNamespaces(self.dynClient, masInstanceIds=[], includeClusterLevel=True)
            if "mas-pipelines" in clusterPipelineNamespaces:
                self.printH2("Cluster-Level MAS Pipelines")
                try:
                    if not mas_pipelines.collectMASPipelines(
                        dynClient=self.dynClient,
                        namespace="mas-pipelines",
                        outputDir=outputDir,
                        noDetail=noDetail,
                        noLogs=noLogs,
                        genericMustGather=self.genericMustGather,
                    ):
                        print("❌ Failed to collect cluster-level pipeline resources from mas-pipelines (check logs)")
                except Exception as e:
                    print(f"❌ Failed to collect cluster-level pipelines: {str(e)}")
        except Exception as e:
            print(f"❌ Failed to discover cluster-level pipeline namespace: {str(e)}")

        return successCount > 0

    def collectAIService(self, outputDir: str, noDetail: bool = False, noLogs: bool = False) -> bool:
        """Collect IBM AI Service resources.

        Orchestrates collection of AI Service instances, tenants, and pipelines for each
        discovered AI Service instance.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            noLogs (bool, optional): If True, skip pod log collection. Defaults to False.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"

        # Discover AI Service instances
        with Halo(text="Discovering AI Service instances", spinner=self.spinner) as h:
            try:
                instanceIds = aiservice_instance.discoverAIServiceInstances(self.dynClient)
                if instanceIds:
                    instanceCount = len(instanceIds)
                    instanceList = ", ".join(sorted(instanceIds))
                    h.stop_and_persist(symbol=self.successIcon, text=f"Discovered {instanceCount} AI Service instance(s): {instanceList}")
                else:
                    h.stop_and_persist(symbol="⏭️", text="No AI Service instances found")
                    return False
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to discover AI Service instances: {str(e)}")
                return False

        successCount = 0

        # Process each AI Service instance
        for instanceId in sorted(instanceIds):
            self.printH2(f"AI Service Instance: {instanceId}")

            instanceTimer = Timer()
            instanceTimer.start()

            # Collect AI Service Instance
            self.printH2("AI Service Instance")
            try:
                with Halo(text=f"Collecting AI Service instance resources for {instanceId}", spinner=self.spinner) as h:
                    if aiservice_instance.collectAIServiceInstance(
                        dynClient=self.dynClient, instanceId=instanceId, outputDir=outputDir, genericMustGather=self.genericMustGather
                    ):
                        h.stop_and_persist(symbol=self.successIcon, text=f"AI Service instance resources collected for {instanceId}")
                        successCount += 1
                    else:
                        h.stop_and_persist(symbol="❌", text=f"Failed to collect AI Service instance resources for {instanceId} (check logs)")
            except Exception as e:
                print(f"❌ Failed to collect AI Service instance {instanceId}: {str(e)}")

            # Collect AI Service Tenants
            self.printH2("AI Service Tenants")
            try:
                tenantIds = aiservice_tenant.discoverAIServiceTenants(self.dynClient, instanceId=instanceId)
                if tenantIds:
                    print(f"Found {len(tenantIds)} tenant(s)")
                    for tenantId in sorted(tenantIds):
                        try:
                            with Halo(text=f"Collecting tenant resources for {tenantId}", spinner=self.spinner) as h:
                                namespace = f"aiservice-{instanceId}"
                                if aiservice_tenant.collectAIServiceTenant(
                                    dynClient=self.dynClient, instanceId=instanceId, tenantId=tenantId, namespace=namespace, outputDir=outputDir
                                ):
                                    h.stop_and_persist(symbol=self.successIcon, text=f"Tenant resources collected for {tenantId}")
                                else:
                                    h.stop_and_persist(symbol="❌", text=f"Failed to collect tenant resources for {tenantId} (check logs)")
                        except Exception as e:
                            print(f"❌ Failed to collect tenant {tenantId}: {str(e)}")
                else:
                    print("⏭️ No tenants found")
            except Exception as e:
                print(f"❌ Failed to discover AI Service tenants for {instanceId}: {str(e)}")

            # Collect AI Service Pipelines
            self.printH2("AI Service Pipelines")
            try:
                pipelineNamespaces = aiservice_pipelines.discoverAIServicePipelineNamespaces(self.dynClient, instanceIds=[instanceId])
                if pipelineNamespaces:
                    for pipelineNamespace in sorted(pipelineNamespaces):
                        try:
                            with Halo(text=f"Collecting pipeline resources from {pipelineNamespace}", spinner=self.spinner) as h:
                                if aiservice_pipelines.collectAIServicePipelines(
                                    dynClient=self.dynClient, namespace=pipelineNamespace, outputDir=outputDir, genericMustGather=self.genericMustGather
                                ):
                                    h.stop_and_persist(symbol=self.successIcon, text=f"Pipeline resources collected from {pipelineNamespace}")
                                else:
                                    h.stop_and_persist(symbol="❌", text=f"Failed to collect pipeline resources from {pipelineNamespace} (check logs)")
                        except Exception as e:
                            print(f"❌ Failed to collect pipelines from {pipelineNamespace}: {str(e)}")
                else:
                    print("⏭️ No pipeline namespaces found")
            except Exception as e:
                print(f"❌ Failed to discover AI Service pipeline namespaces for {instanceId}: {str(e)}")

            elapsed = instanceTimer.stop()
            print()
            print(f"Instance {instanceId} collection completed in {elapsed} seconds")

        return successCount > 0

    def collectArgo(self, outputDir: str, noDetail: bool = False) -> bool:
        """Collect Argo CD resources from openshift-gitops namespace.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.

        Returns:
            bool: True if collection succeeded, False if namespace not found
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"

        # Check if openshift-gitops namespace exists
        with Halo(text="Checking for Argo CD (openshift-gitops)", spinner=self.spinner) as h:
            if argo.checkArgoNamespace(self.dynClient):
                h.stop_and_persist(symbol=self.successIcon, text="Argo CD namespace found")
            else:
                h.stop_and_persist(symbol="⏭️", text="Argo CD not found (openshift-gitops namespace does not exist)")
                return False

        # Collect Argo resources
        try:
            with Halo(text="Collecting Argo CD resources from openshift-gitops", spinner=self.spinner) as h:
                if argo.collectArgo(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather):
                    h.stop_and_persist(symbol=self.successIcon, text="Argo CD resources collected from openshift-gitops")
                    return True
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect Argo CD resources from openshift-gitops (check logs)")
                    return False
        except Exception as e:
            print(f"❌ Failed to collect Argo CD resources: {str(e)}")
            return False

    def collectExtraNamespaces(self, outputDir: str, extraNamespaces: str, noDetail: bool = False, noLogs: bool = False) -> bool:
        """Collect resources from extra namespaces specified by user.

        Args:
            outputDir (str): Base output directory for collected resources
            extraNamespaces (str): Comma-separated list of namespace names
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            noLogs (bool, optional): If True, skip pod log collection. Defaults to False.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"

        # Parse namespace list
        namespaceList = [ns.strip() for ns in extraNamespaces.split(",") if ns.strip()]

        if not namespaceList:
            return False

        successCount = 0

        # Collect from each namespace
        for namespace in namespaceList:
            self.printH2(f"Extra Namespace: {namespace}")
            try:
                with Halo(text=f"Collecting resources from {namespace}", spinner=self.spinner) as h:
                    if self.genericMustGather(namespace=namespace, outputDir=outputDir, noDetail=noDetail, noLogs=noLogs):
                        h.stop_and_persist(symbol=self.successIcon, text=f"Resources collected from {namespace}")
                        successCount += 1
                    else:
                        h.stop_and_persist(symbol="❌", text=f"Failed to collect resources from {namespace} (check logs)")
            except Exception as e:
                print(f"❌ Failed to collect from {namespace}: {str(e)}")

        return successCount > 0

    def generateSubscriptionsSummary(self, outputDir: str) -> bool:
        """Generate cluster-wide subscriptions summary.

        Creates a unified subscriptions table at resources/_cluster/subscriptions.md
        aggregating subscriptions from all namespaces.

        Args:
            outputDir (str): Base output directory for must-gather

        Returns:
            bool: True if summary generation succeeded, False otherwise
        """
        logger = logging.getLogger(__name__)
        outputFile = os.path.join(outputDir, "resources", "_cluster", "subscriptions.md")

        try:
            with Halo(text="Generating subscriptions summary", spinner=self.spinner) as h:
                # Import subscriptions summarizer
                from .summarizer import subscriptions

                # Generate subscriptions summary (writes directly to file)
                subscriptions.summarize(outputDir)

                h.stop_and_persist(symbol=self.successIcon, text=f"Subscriptions summary generated: {outputFile}")
                logger.info(f"Successfully generated subscriptions summary: {outputFile}")
                return True

        except FileNotFoundError as e:
            print(f"⚠️  Required files not found for subscriptions summary: {e}")
            logger.debug(f"Subscriptions summary skipped due to missing files: {e}")
            return False
        except Exception as e:
            print(f"❌ Error generating subscriptions summary: {e}")
            logger.error(f"Error generating subscriptions summary: {e}")
            return False

    def uploadToArtifactory(self, archivePath: str, artifactoryToken: str, artifactoryUploadDir: str) -> bool:
        """Upload must-gather archive to Artifactory with checksums.

        Calculates MD5 and SHA1 checksums for the archive and uploads it to
        Artifactory with the checksums in HTTP headers.

        Args:
            archivePath (str): Path to the tar.gz archive file
            artifactoryToken (str): Bearer token for Artifactory authentication
            artifactoryUploadDir (str): Target URL directory in Artifactory

        Returns:
            bool: True if upload succeeded, False otherwise
        """
        logger = logging.getLogger(__name__)

        if not os.path.exists(archivePath):
            print(f"❌ Archive file not found: {archivePath}")
            logger.error(f"Archive file not found: {archivePath}")
            return False

        try:
            # Calculate checksums
            with Halo(text="Calculating checksums", spinner=self.spinner) as h:
                md5Hash = hashlib.md5()
                sha1Hash = hashlib.sha1()

                with open(archivePath, "rb") as f:
                    while chunk := f.read(8192):
                        md5Hash.update(chunk)
                        sha1Hash.update(chunk)

                md5Value = md5Hash.hexdigest()
                sha1Value = sha1Hash.hexdigest()
                h.stop_and_persist(symbol=self.successIcon, text=f"Checksums calculated (MD5: {md5Value[:8]}..., SHA1: {sha1Value[:8]}...)")

            # Construct target URL
            archiveFilename = os.path.basename(archivePath)
            targetUrl = f"{artifactoryUploadDir}/{archiveFilename}"

            # Upload to Artifactory
            with Halo(text=f"Uploading to {targetUrl}", spinner=self.spinner) as h:
                headers = {"Authorization": f"Bearer {artifactoryToken}", "X-Checksum-Md5": md5Value, "X-Checksum-Sha1": sha1Value}

                with open(archivePath, "rb") as f:
                    response = requests.put(targetUrl, data=f, headers=headers, timeout=600)

                if response.status_code in [200, 201]:
                    h.stop_and_persist(symbol=self.successIcon, text=f"Successfully uploaded to {targetUrl}")
                    logger.info(f"Successfully uploaded archive to {targetUrl}")
                    return True
                else:
                    h.stop_and_persist(symbol="❌", text=f"Upload failed with status {response.status_code}: {response.text}")
                    logger.error(f"Upload failed with status {response.status_code}: {response.text}")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Upload failed: {e}")
            logger.error(f"Upload failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            logger.error(f"Error during upload: {e}")
            return False
