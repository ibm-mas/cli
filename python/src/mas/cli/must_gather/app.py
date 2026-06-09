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
from typing import Optional

import requests
from mas.cli import BaseApp
from .arg_parser import createArgumentParser
from .output import OutputManager
from .timer import Timer
from . import ocp
from .dependencies import sls
from .mas import core as mas_core, apps as mas_apps, pipelines as mas_pipelines
from .aiservice import instance as aiservice_instance
from .argo import applications as argo
from .common.task_generation import generateNamespaceCollectionTasks
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
        """Execute must-gather collection using 4-phase approach.

        Phases:
        1. Discovery - Build complete collection plan
        2. Collection - Execute plan with parallel threadpool
        3. Summary - Generate subscriptions summary and web viewer
        4. Packaging - Create archive and upload

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

        # Process CRDs first (always, before discovery phase)
        # This is needed for printer columns and IBM CRD discovery
        from mas.cli.must_gather.common.crd_processor import processCRDs

        if self.dynClient is None:
            raise RuntimeError("Kubernetes client not initialized")

        self.printerColumnsCache, self.ibmCRDsList = processCRDs(self.dynClient, outputManager.outputDir)

        # ============================================================
        # PHASE 1: DISCOVERY
        # ============================================================
        self.printH1("Discovery")
        discoveryTimer = Timer()
        discoveryTimer.start()

        with Halo(text="Discovering resources to collect", spinner=self.spinner) as h:
            plan = self.planCollection(parsedArgs, outputManager.outputDir)
            h.stop_and_persist(symbol="✅", text=f"Discovered {plan.total_tasks} collection tasks across {plan.total_groups} groups")

        elapsed = discoveryTimer.stop()
        self.printHighlight(f"Discovery completed in {elapsed} seconds")

        # ============================================================
        # PHASE 2: COLLECTION
        # ============================================================
        self.printH1("Collection")
        collectionTimer = Timer()
        collectionTimer.start()

        if plan.total_groups > 0:
            self.executeCollectionPlan(plan)
            elapsed = collectionTimer.stop()
            print()
            self.printHighlight(f"Collection completed in {elapsed} seconds")
        else:
            elapsed = collectionTimer.stop()
            print("No resources to collect")

        # ============================================================
        # PHASE 3: SUMMARY
        # ============================================================
        self.printH1("Summary")
        summaryTimer = Timer()
        summaryTimer.start()

        # Generate subscriptions summary (only if OCP was collected)
        if not parsedArgs.no_ocp:
            self.generateSubscriptionsSummary(outputDir=outputManager.outputDir)

        # Generate web viewer
        with Halo(text="Generating web viewer", spinner=self.spinner) as h:
            if web_viewer.generateWebViewer(outputManager.outputDir):
                h.stop_and_persist(symbol="✅", text="Web viewer generated")
                self.printHighlight(f"Run must-gather serve --dir {outputManager.outputDir} to view the must-gather")
            else:
                h.stop_and_persist(symbol="⚠️", text="Web viewer generation failed (must-gather data is still available)")

        elapsed = summaryTimer.stop()
        self.printHighlight(f"Summary generation completed in {elapsed} seconds")

        # ============================================================
        # PHASE 4: PACKAGING
        # ============================================================
        self.printH1("Packaging")
        packagingTimer = Timer()
        packagingTimer.start()

        # Create archive
        with Halo(text="Creating archive", spinner=self.spinner) as h:
            archivePath = outputManager.createArchive()
            h.stop_and_persist(symbol="✅", text=f"Archive created: {archivePath}")

        # Upload to Artifactory if configured
        if parsedArgs.artifactory_token and parsedArgs.artifactory_upload_dir:
            with Halo(text="Uploading to Artifactory", spinner=self.spinner) as h:
                if self.uploadToArtifactory(
                    archivePath=archivePath, artifactoryToken=parsedArgs.artifactory_token, artifactoryUploadDir=parsedArgs.artifactory_upload_dir
                ):
                    h.stop_and_persist(symbol="✅", text="Upload completed")
                else:
                    h.stop_and_persist(symbol="❌", text="Upload failed")

        elapsed = packagingTimer.stop()
        self.printHighlight(f"Packaging completed in {elapsed} seconds")

        # Cleanup
        outputManager.cleanup()

        # Print completion message
        elapsed = overallTimer.stop()
        self.printH1("Completion")
        print(f"Must-gather completed in {elapsed} seconds")
        self.printHighlight(f"Must gather successfully saved to: {archivePath}")

        return 0

    def planCollection(self, parsedArgs, outputDir: str):
        """Discover all resources and generate collection plan.

        This method performs fast discovery of all resources to collect and
        generates a complete collection plan with all tasks defined. It does
        NOT collect any actual data.

        Args:
            parsedArgs: Parsed command-line arguments
            outputDir (str): Base output directory for collected resources

        Returns:
            CollectionPlan: Complete plan with all collection tasks organized into groups
        """
        from .collection_plan import CollectionPlan
        from .dependencies import kafka, mongodb, grafana, cert_manager, db2, cp4d

        # Type assertion: dynClient is guaranteed to be non-None by _initializeKubernetesClient()
        assert self.dynClient is not None, "Kubernetes client must be initialized before planning collection"

        logger.info("🔍 Starting collection plan discovery")
        plan = CollectionPlan()

        # OCP Discovery
        logger.info("💭 Planning OCP resource collection")
        ocpTasks = [
            ("cluster_resources", ocp.collectClusterResources, self.dynClient, outputDir, parsedArgs.summary_only),
            ("nodes", ocp.collectNodes, self.dynClient, outputDir, parsedArgs.summary_only),
            ("airgap_resources", ocp.collectAirgapResources, self.dynClient, outputDir, parsedArgs.summary_only),
            ("marketplace_resources", ocp.collectMarketplaceResources, self.dynClient, outputDir, parsedArgs.summary_only),
        ]
        plan.addGroup("OpenShift Container Platform", ocpTasks)
        logger.debug("Added OCP collection group with 4 tasks to plan")

        # Dependencies Discovery
        if not parsedArgs.no_dependencies:
            logger.debug("Discovering dependency namespaces")

            # Kafka
            kafka.addKafkaToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
            )

            # MongoDB
            mongodb.addMongoDBToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
            )

            # Grafana
            grafana.addGrafanaToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
            )

            # Certificate Manager
            cert_manager.addCertManagerToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
            )

            # DB2
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            db2.addDb2ToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
                masInstanceIds=masInstanceIds,
            )

            # CP4D
            cp4d.addCP4DToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
            )
        else:
            logger.debug("Skipping dependency discovery (--no-dependencies flag set)")

        # SLS
        masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
        sls.addSLSToCollectionPlan(
            plan=plan,
            dynClient=self.dynClient,
            outputDir=outputDir,
            noDetail=parsedArgs.summary_only,
            noLogs=parsedArgs.no_logs,
            ibmCRDs=self.ibmCRDsList,
            masInstanceIds=masInstanceIds,
        )

        # MAS Discovery
        try:
            masInstanceIds = parsedArgs.mas_instance_ids.split(",") if parsedArgs.mas_instance_ids else None
            masAppIds = parsedArgs.mas_app_ids.split(",") if parsedArgs.mas_app_ids else None

            # Add MAS Core collection tasks
            coreNamespaces = mas_core.addMASCoreToCollectionPlan(
                plan=plan,
                dynClient=self.dynClient,
                outputDir=outputDir,
                noDetail=parsedArgs.summary_only,
                noLogs=parsedArgs.no_logs,
                ibmCRDs=self.ibmCRDsList,
                masInstanceIds=masInstanceIds,
            )

            if coreNamespaces:
                # Add MAS Apps collection tasks for discovered instances
                mas_apps.addMASAppsToCollectionPlan(
                    plan=plan,
                    dynClient=self.dynClient,
                    outputDir=outputDir,
                    noDetail=parsedArgs.summary_only,
                    noLogs=parsedArgs.no_logs,
                    ibmCRDs=self.ibmCRDsList,
                    coreNamespaces=coreNamespaces,
                    masAppIds=masAppIds,
                )

                # Add MAS Pipelines collection tasks
                mas_pipelines.addMASPipelinesToCollectionPlan(
                    plan=plan,
                    dynClient=self.dynClient,
                    outputDir=outputDir,
                    noDetail=parsedArgs.summary_only,
                    noLogs=parsedArgs.no_logs,
                    ibmCRDs=self.ibmCRDsList,
                )
            else:
                logger.debug("No MAS instances discovered")
        except Exception as e:
            logger.warning(f"⚠️ MAS discovery failed: {e}")

        # AI Service Discovery
        aiservice_instance.addAIServiceToCollectionPlan(
            plan=plan,
            dynClient=self.dynClient,
            outputDir=outputDir,
            noDetail=parsedArgs.summary_only,
            noLogs=parsedArgs.no_logs,
            ibmCRDs=self.ibmCRDsList,
        )

        # Argo Discovery
        argo.addArgoToCollectionPlan(
            plan=plan,
            dynClient=self.dynClient,
            outputDir=outputDir,
            noDetail=parsedArgs.summary_only,
            noLogs=parsedArgs.no_logs,
            ibmCRDs=self.ibmCRDsList,
        )

        # Extra Namespaces Discovery
        if parsedArgs.extra_namespaces:
            namespaceList = [ns.strip() for ns in parsedArgs.extra_namespaces.split(",") if ns.strip()]
            logger.debug(f"Adding {len(namespaceList)} extra namespace(s): {', '.join(namespaceList)}")
            for namespace in namespaceList:
                # Generate tasks for extra namespace using common task generation
                tasks = generateNamespaceCollectionTasks(
                    dynClient=self.dynClient,
                    namespace=namespace,
                    outputDir=outputDir,
                    noDetail=parsedArgs.summary_only,
                    noLogs=parsedArgs.no_logs,
                    includeSecrets=True,
                    secretData=False,
                    customResources=None,
                    ibmCRDs=self.ibmCRDsList,
                )
                plan.addGroup(f"Extra Namespace ({namespace})", tasks)
                logger.debug(f"Added extra namespace collection group for {namespace} with {len(tasks)} tasks")
        else:
            logger.debug("No extra namespaces specified")

        logger.info(f"✅ Collection plan complete: {len(plan.groups)} groups, {sum(len(g.tasks) for g in plan.groups)} total tasks")
        return plan

    def executeCollectionPlan(self, plan):
        """Execute all collection tasks in parallel with sequential display.

        This method executes all tasks from the collection plan using a shared
        threadpool, displaying progress sequentially by group with Halo spinners.

        Args:
            plan (CollectionPlan): The collection plan containing all tasks

        Returns:
            bool: True if execution completed (even if some tasks failed)
        """
        from .parallel_executor import executeCollection

        # Handle empty plan
        if not plan.groups:
            return True

        # Define display callback for Halo spinner updates
        def displayCallback(groupName: str, taskType: str, completed: int, total: int):
            """Update progress display (placeholder for Halo integration)."""
            # This will be enhanced with Halo spinner integration
            logger.info(f"✅ {groupName}: {taskType} ({completed}/{total})")
            print(f"✅ {groupName}: {taskType} ({completed}/{total})")

        # Execute collection with parallel executor
        return executeCollection(plan=plan, maxWorkers=50, displayCallback=displayCallback)

    def packageResults(self, parsedArgs, outputManager):
        """Package results into archive and optionally upload.

        This method creates the final archive, optionally uploads to Artifactory,
        and performs cleanup.

        Args:
            parsedArgs: Parsed command-line arguments
            outputManager (OutputManager): Output manager instance

        Returns:
            str: Path to the created archive
        """
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
                archivePath=archivePath,
                artifactoryToken=parsedArgs.artifactory_token,
                artifactoryUploadDir=parsedArgs.artifactory_upload_dir,
            ):
                elapsed = uploadTimer.stop()
                print(f"Upload completed in {elapsed} seconds")
            else:
                elapsed = uploadTimer.stop()
                print(f"❌ Upload failed after {elapsed} seconds")

        # Cleanup
        outputManager.cleanup()

        return archivePath

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
                logger.info(f"✅ Successfully generated subscriptions summary: {outputFile}")
                return True

        except FileNotFoundError as e:
            print(f"⚠️  Required files not found for subscriptions summary: {e}")
            logger.warning(f"⚠️ Subscriptions summary skipped due to missing files: {e}")
            return False
        except Exception as e:
            print(f"❌  Error generating subscriptions summary: {e}")
            logger.error(f"❌ Error generating subscriptions summary: {e}")
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
            logger.error(f"❌ Archive file not found: {archivePath}")
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
                    logger.info(f"✅ Successfully uploaded archive to {targetUrl}")
                    return True
                else:
                    h.stop_and_persist(symbol="❌", text=f"Upload failed with status {response.status_code}: {response.text}")
                    logger.error(f"❌ Upload failed with status {response.status_code}: {response.text}")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Upload failed: {e}")
            logger.error(f"❌ Upload failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            logger.error(f"❌ Error during upload: {e}")
            return False
