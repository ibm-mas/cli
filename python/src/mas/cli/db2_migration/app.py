# -----------------------------------------------------------
# Licensed Materials - Property of IBM
# 5737-M66
# (C) Copyright IBM Corp. 2026 All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication, or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
# -----------------------------------------------------------

import logging

from typing import List, Dict, Any
from halo import Halo
from prompt_toolkit import print_formatted_text, HTML
from openshift.dynamic.exceptions import NotFoundError

from ..cli import BaseApp
from .argParser import db2MigrationArgParser
from mas.devops.ocp import createNamespace
from mas.devops.tekton import preparePipelinesNamespace, installOpenShiftPipelines, updateTektonDefinitions, launchDb2MigrationPipeline

logger = logging.getLogger(__name__)


class Db2MigrationApp(BaseApp):
    """Application class for Db2uCluster to Db2uInstance migration"""

    def detectDb2uClusters(self, namespace: str) -> List[Dict[str, Any]]:
        """Detect all Db2uCluster instances in the specified namespace.

        Args:
            namespace (str): Kubernetes namespace to search

        Returns:
            List[Dict[str, Any]]: List of Db2uCluster resources found
        """
        try:
            db2ClusterAPI = self.dynamicClient.resources.get(api_version="db2u.databases.ibm.com/v1", kind="Db2uCluster")
            db2_clusters = db2ClusterAPI.get(namespace=namespace)
            return db2_clusters.items if db2_clusters else []
        except NotFoundError:
            return []

    def promptForDb2Cluster(self, db2_clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prompt user to select a Db2uCluster from the detected list.

        Args:
            db2_clusters (List[Dict[str, Any]]): List of available Db2uCluster resources

        Returns:
            Dict[str, Any]: Selected Db2uCluster resource
        """
        if len(db2_clusters) == 1:
            db2_cluster = db2_clusters[0]
            db2ClusterName = db2_cluster.metadata.name
            self.printHighlight(f"Found 1 Db2uCluster: {db2ClusterName}")
            return db2_cluster

        # Multiple Db2uClusters - Prompt for selection
        # self.printH2("Available Db2uClusters")
        # options = []
        # for i, db2_cluster in enumerate(db2_clusters):
        #    name = db2_cluster.metadata.name
        #    version = db2_cluster.spec.version if hasattr(db2_cluster.spec, "version") else "unknown"
        #    status = db2_cluster.status.state if hasattr(db2_cluster, "status") and hasattr(db2_cluster.status, "state") else "unknown"
        #    options.append(f"{name} (version: {version}, status: {status})")

        # selectedIndex = self.promptForListSelect("Select Db2uCluster to migrate", options)
        # return db2_clusters[selectedIndex]

        self.printH2("Available Db2uClusters")
        for i, db2_cluster in enumerate(db2_clusters):
            name = db2_cluster.metadata.name
            version = db2_cluster.spec.version if hasattr(db2_cluster.spec, "version") else "unknown"
            status = db2_cluster.status.state if hasattr(db2_cluster, "status") and hasattr(db2_cluster.status, "state") else "unknown"
            print(f"  {i+1}. {name} (version: {version}, status: {status})")

        selectedIndex = self.promptForInt("Select Db2uCluster to migrate", min=1, max=len(db2_clusters))
        return db2_clusters[selectedIndex - 1]

    def promptForBackup(self) -> bool:
        """Prompt user whether to perform backup before migration.

        Returns:
            bool: True if backup should be performed, False otherwise
        """
        self.printH2("Backup Configuration")
        print_formatted_text(
            HTML(
                "<Yellow>It is strongly recommended to backup before migration.</Yellow>\n"
                "This will create a full database backup that can be used for rollback.\n"
            )
        )
        return self.yesOrNo("Perform backup before migration")

    def migrate(self, argv: List[str]) -> None:
        """Main entry point for DB2 migration command.

        Args:
            argv (List[str]): Command line arguments
        """
        args = db2MigrationArgParser.parse_args(argv)
        self.noConfirm = args.no_confirm

        # Connect to cluster
        self.connect()

        # Determine mode: interactive vs non-interactive
        isInteractive = args.namespace is None

        if isInteractive:
            # Interactive mode
            self.printH1("Db2uCluster to Db2uInstance Migration")

            # List db2u namespaces
            with Halo(text="Detecting db2u namespaces", spinner=self.spinner) as h:
                try:
                    namespaceAPI = self.dynamicClient.resources.get(api_version="v1", kind="Namespace")
                    allNamespaces = namespaceAPI.get()
                    db2uNamespaces = [ns.metadata.name for ns in allNamespaces.items if ns.metadata.name.startswith("db2u")]
                    # v1 = client.CoreV1Api()
                    # allNamespaces = v1.list_namespace()
                    # db2uNamespaces = [ns.metadata.name for ns in allNamespaces.items if ns.metadata.name.startswith("db2u")]

                    if db2uNamespaces:
                        h.succeed(f"Found {len(db2uNamespaces)} db2u namespace(s)")
                        print_formatted_text(HTML("<ansicyan>Available db2u namespaces:</ansicyan>"))
                        for ns in sorted(db2uNamespaces):
                            print(f"  - {ns}")
                        print()
                    else:
                        h.info("No db2u namespaces found")
                except Exception as e:
                    h.fail(f"Failed to list namespaces: {e}")

            # Prompt for namespace with default
            namespace = self.promptForString("Enter namespace containing Db2uClusters", default="db2u")

            # Detect Db2uClusters
            with Halo(text=f"Detecting Db2uClusters in namespace {namespace}", spinner=self.spinner) as h:
                db2_clusters = self.detectDb2uClusters(namespace)
                if not db2_clusters:
                    h.fail(f"No Db2uClusters found in namespace {namespace}")
                    self.fatalError(f"No Db2uClusters found in namespace {namespace}")
                h.succeed(f"Found {len(db2_clusters)} Db2uCluster(s)")

            # Select Db2uCluster
            selectedDb2Cluster = self.promptForDb2Cluster(db2_clusters)
            db2ClusterName = selectedDb2Cluster.metadata.name

            # Prompt for backup
            enableBackup = self.promptForBackup()

        else:
            # Non-interactive mode
            namespace = args.namespace
            db2ClusterName = args.db2_cluster_name
            enableBackup = args.backup == "true" if args.backup else True

            # Validate Db2uCluster exists if name provided
            if db2ClusterName:
                db2_clusters = self.detectDb2uClusters(namespace)
                db2ClusterNames = [c.metadata.name for c in db2_clusters]
                if db2ClusterName not in db2ClusterNames:
                    self.fatalError(f"Db2uCluster {db2ClusterName} not found in namespace {namespace}")
            else:
                # Auto-select if only one Db2uCluster
                db2_clusters = self.detectDb2uClusters(namespace)
                if len(db2_clusters) == 0:
                    self.fatalError(f"No Db2uClusters found in namespace {namespace}")
                elif len(db2_clusters) == 1:
                    db2ClusterName = db2_clusters[0].metadata.name
                else:
                    self.fatalError("Multiple Db2uClusters found. Please specify --db2-cluster-name")

        # Confirmation
        if not self.noConfirm:
            self.printH2("Migration Summary")
            print_formatted_text(
                HTML(
                    f"<Yellow>Namespace:</Yellow> {namespace}\n"
                    f"<Yellow>Db2uCluster:</Yellow> {db2ClusterName}\n"
                    f"<Yellow>Backup:</Yellow> {'Enabled' if enableBackup else 'Disabled'}\n"
                )
            )
            if not self.yesOrNo("Proceed with migration"):
                print_formatted_text(HTML("<Red>Migration cancelled</Red>"))
                return

        # Set parameters
        self.setParam("db2_migration_namespace", namespace)
        self.setParam("db2_migration_db2_cluster_name", db2ClusterName)
        self.setParam("db2_migration_backup_enabled", str(enableBackup).lower())

        # Prepare pipeline namespace
        pipelinesNamespace = "mas-pipelines"

        with Halo(text="Validating OpenShift Pipelines installation", spinner=self.spinner) as h:
            if installOpenShiftPipelines(self.dynamicClient):
                h.succeed("OpenShift Pipelines Operator is installed and ready")
            else:
                h.fail("OpenShift Pipelines Operator installation failed")
                self.fatalError("Installation failed")

        with Halo(text=f"Preparing namespace ({pipelinesNamespace})", spinner=self.spinner) as h:
            createNamespace(self.dynamicClient, pipelinesNamespace)
            preparePipelinesNamespace(dynClient=self.dynamicClient)
            h.succeed(f"Namespace {pipelinesNamespace} is ready")

        with Halo(text=f"Installing latest Tekton definitions (v{self.version})", spinner=self.spinner) as h:
            updateTektonDefinitions(self.dynamicClient, pipelinesNamespace, self.tektonDefsPath)
            h.succeed(f"Latest Tekton definitions are installed (v{self.version})")

        # Launch pipeline
        with Halo(text="Submitting PipelineRun for DB2 migration", spinner=self.spinner) as h:
            pipelineURL = launchDb2MigrationPipeline(dynClient=self.dynamicClient, params=self.params)
            if pipelineURL:
                h.succeed("PipelineRun for DB2 migration submitted")
                print_formatted_text(HTML(f"\nView progress:\n  <Cyan><u>{pipelineURL}</u></Cyan>\n"))
            else:
                h.fail("Failed to submit PipelineRun, see log file for details")
