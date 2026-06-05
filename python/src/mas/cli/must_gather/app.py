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

from typing import Optional, List
from mas.cli import BaseApp
from .arg_parser import createArgumentParser
from .output import OutputManager
from .timer import Timer
from .common import collectResourcesParallel, collectSecrets, collectPods, getIBMCRDs
from . import ocp
from . import dependencies
from .sls import license_service as sls
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from halo import Halo


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

    def _initializeKubernetesClient(self):
        """Initialize Kubernetes Dynamic Client.

        Loads kubeconfig and creates a DynamicClient for API access.
        """
        if not self.dynClient:
            config.load_kube_config()
            self.dynClient = DynamicClient(config.new_client_from_config())

    def mustGather(self, args):
        """Execute must-gather collection.

        Args:
            args: Command-line arguments list

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Parse arguments
        parser = createArgumentParser()
        parsedArgs = parser.parse_args(args)

        # Initialize output manager
        outputManager = OutputManager(parsedArgs.directory, parsedArgs.keep_files)
        outputManager.initialize()

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

        # Collect OCP resources (unless --no-ocp flag is set)
        if not parsedArgs.no_ocp:
            self.printH1("OpenShift Container Platform")
            ocpTimer = Timer()
            ocpTimer.start()
            self.collectOCP(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only)
            elapsed = ocpTimer.stop()
            self.printHighlight(f"OCP collection completed in {elapsed} seconds")

        # Collect dependency resources (unless --no-dependencies flag is set)
        if not parsedArgs.no_dependencies:
            self.printH1("In-Cluster Dependencies")
            depTimer = Timer()
            depTimer.start()
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            self.collectDependencies(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only, masInstanceIds=masInstanceIds)
            elapsed = depTimer.stop()
            self.printHighlight(f"Dependencies collection completed in {elapsed} seconds")

        # Collect SLS resources (unless --no-sls flag is set)
        if not parsedArgs.no_sls:
            self.printH1("Suite License Service")
            slsTimer = Timer()
            slsTimer.start()
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            self.collectSLS(outputDir=outputManager.outputDir, noDetail=parsedArgs.summary_only, masInstanceIds=masInstanceIds)
            elapsed = slsTimer.stop()
            self.printHighlight(f"SLS collection completed in {elapsed} seconds")

        # Create archive
        self.printH2("Creating Archive")
        archivePath = outputManager.createArchive()
        self.printHighlight(f"Archive created: {archivePath}")

        # Cleanup
        outputManager.cleanup()

        # Print completion message
        elapsed = overallTimer.stop()
        self.printH2("Completion")
        self.printHighlight(f"Must-gather completed in {elapsed} seconds")
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
            ibmCRDsWithInstances = []
            try:
                ibmCRDs = getIBMCRDs(self.dynClient)

                # Check which IBM CRDs have instances in the namespace
                for kind, apiVersion in ibmCRDs:
                    try:
                        api = self.dynClient.resources.get(api_version=apiVersion, kind=kind)
                        resources = api.get(namespace=namespace)
                        if resources.items:
                            ibmCRDsWithInstances.append((apiVersion, kind))
                    except Exception:
                        pass
            except Exception as e:
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
                            outputDir=f"{outputDir}/resources",
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
            with Halo(text=f"Collecting secrets from {namespace}", spinner=self.spinner) as h:
                try:
                    if collectSecrets(dynClient=self.dynClient, namespace=namespace, outputDir=outputDir, secretData=secretData, allNamespaces=False):
                        h.stop_and_persist(symbol=self.successIcon, text=f"Secrets collected from {namespace}")
                    else:
                        h.stop_and_persist(symbol="❌", text=f"Failed to collect secrets from {namespace} (check logs)")
                        success = False
                except Exception as e:
                    h.stop_and_persist(symbol="❌", text=f"Failed to collect secrets from {namespace}: {str(e)}")
                    success = False

        # Collect pods
        with Halo(text=f"Collecting pods from {namespace}", spinner=self.spinner) as h:
            try:
                if collectPods(dynClient=self.dynClient, namespace=namespace, outputDir=outputDir, podLogs=not noLogs, noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text=f"Pods collected from {namespace}")
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

        # Collect cluster resources
        totalCount += 1
        with Halo(text="Collecting OCP cluster resources", spinner=self.spinner) as h:
            try:
                if ocp.collectClusterResources(dynClient=self.dynClient, outputDir=f"{outputDir}/resources", noDetail=noDetail):
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
                if ocp.collectNodes(dynClient=self.dynClient, outputDir=f"{outputDir}/resources", noDetail=noDetail):
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
                if ocp.collectAirgapResources(dynClient=self.dynClient, outputDir=f"{outputDir}/resources", noDetail=noDetail):
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
                if ocp.collectMarketplaceResources(dynClient=self.dynClient, outputDir=f"{outputDir}/resources", noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text="OCP marketplace resources collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP marketplace resources (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP marketplace resources: {str(e)}")

        # Collect Kubernetes Operators
        totalCount += 1
        with Halo(text="Collecting OCP operator resources", spinner=self.spinner) as h:
            try:
                if ocp.collectOperatorResources(dynClient=self.dynClient, outputDir=f"{outputDir}/resources", noDetail=noDetail):
                    h.stop_and_persist(symbol=self.successIcon, text="OCP operator resources collected")
                    successCount += 1
                else:
                    h.stop_and_persist(symbol="❌", text="Failed to collect OCP operator resources (check logs for details)")
            except Exception as e:
                h.stop_and_persist(symbol="❌", text=f"Failed to collect OCP operator resources: {str(e)}")

        return successCount > 0

    def collectDependencies(self, outputDir: str, noDetail: bool = False, masInstanceIds: Optional[List[str]] = None) -> bool:
        """Collect in-cluster dependency resources.

        Orchestrates collection of dependency resources including IBM Common Services,
        CP4D, Db2, DRO, Certificate Manager, Kafka, Grafana, MongoDB, and SLS.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            masInstanceIds (list, optional): List of MAS instance IDs for Db2 discovery. Defaults to None.

        Returns:
            bool: True if any collection succeeded
        """
        if not self.dynClient:
            self._initializeKubernetesClient()

        assert self.dynClient is not None, "Kubernetes client must be initialized"
        successCount = 0
        totalCount = 0

        # IBM Common Services
        self.printH2("IBM CloudPak Foundation Services")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectCommonServices(
                dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather
            )
            if result:
                print(f"{self.successIcon} IBM CloudPak Foundation Services collected")
                successCount += 1
            else:
                print("⊘ IBM CloudPak Foundation Services skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect IBM CloudPak Foundation Services: {str(e)}")

        # IBM CloudPak for Data
        self.printH2("IBM CloudPak for Data")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectCP4D(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} IBM CloudPak for Data collected")
                successCount += 1
            else:
                print("⊘ IBM CloudPak for Data skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect IBM CloudPak for Data: {str(e)}")

        # IBM Db2 Universal Operator
        self.printH2("IBM Db2 Universal Operator")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectDb2(
                dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, masInstanceIds=masInstanceIds, genericMustGather=self.genericMustGather
            )
            if result:
                print(f"{self.successIcon} IBM Db2 Universal Operator collected")
                successCount += 1
            else:
                print("⊘ IBM Db2 Universal Operator skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect IBM Db2 Universal Operator: {str(e)}")

        # IBM Data Reporter Operator
        self.printH2("IBM Data Reporter Operator")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectDRO(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} IBM Data Reporter Operator collected")
                successCount += 1
            else:
                print("⊘ IBM Data Reporter Operator skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect IBM Data Reporter Operator: {str(e)}")

        # Red Hat Certificate Manager
        self.printH2("Red Hat Certificate Manager")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectCertManager(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} Red Hat Certificate Manager collected")
                successCount += 1
            else:
                print("⊘ Red Hat Certificate Manager skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect Red Hat Certificate Manager: {str(e)}")

        # Kafka
        self.printH2("Kafka")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectKafka(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} Kafka collected")
                successCount += 1
            else:
                print("⊘ Kafka skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect Kafka: {str(e)}")

        # Grafana
        self.printH2("Grafana")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectGrafana(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} Grafana collected")
                successCount += 1
            else:
                print("⊘ Grafana skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect Grafana: {str(e)}")

        # MongoDB Community
        self.printH2("MongoDB Community")  # type: ignore[attr-defined]
        totalCount += 1
        try:
            result = dependencies.collectMongoDB(dynClient=self.dynClient, outputDir=outputDir, noDetail=noDetail, genericMustGather=self.genericMustGather)
            if result:
                print(f"{self.successIcon} MongoDB Community collected")
                successCount += 1
            else:
                print("⊘ MongoDB Community skipped (not found)")
        except Exception as e:
            print(f"❌ Failed to collect MongoDB Community: {str(e)}")

        return successCount > 0

    def collectSLS(self, outputDir: str, noDetail: bool = False, masInstanceIds: Optional[List[str]] = None) -> bool:
        """Collect IBM Suite License Service resources.

        Discovers SLS namespaces from slscfg CRs (when MAS instance IDs provided) or
        LicenseService CRs directly, then collects resources from each discovered namespace.

        Args:
            outputDir (str): Base output directory for collected resources
            noDetail (bool, optional): If True, only collect summary without detailed YAML. Defaults to False.
            masInstanceIds (list, optional): List of MAS instance IDs for slscfg-based discovery. Defaults to None.

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
            self.printH2(f"Namespace: {namespace}")  # type: ignore[attr-defined]
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

        return successCount > 0


# Made with Bob
