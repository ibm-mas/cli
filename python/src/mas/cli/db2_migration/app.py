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
    """Application class for DB2 cluster migration"""

    def detectDb2uClusters(self, namespace: str) -> List[Dict[str, Any]]:
        """Detect all Db2uCluster instances in the specified namespace.

        Args:
            namespace (str): Kubernetes namespace to search

        Returns:
            List[Dict[str, Any]]: List of Db2uCluster resources found
        """
        try:
            db2ClusterAPI = self.dynamicClient.resources.get(api_version="db2u.databases.ibm.com/v1", kind="Db2uCluster")
            clusters = db2ClusterAPI.get(namespace=namespace)
            return clusters.items if clusters else []
        except NotFoundError:
            return []

    def promptForCluster(self, clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prompt user to select a cluster from the detected list.

        Args:
            clusters (List[Dict[str, Any]]): List of available clusters

        Returns:
            Dict[str, Any]: Selected cluster resource
        """
        if len(clusters) == 1:
            cluster = clusters[0]
            clusterName = cluster.metadata.name
            self.printHighlight(f"Found 1 Db2uCluster: {clusterName}")
            return cluster

        # Multiple clusters - prompt for selection
        # self.printH2("Available Db2uClusters")
        # options = []
        # for i, cluster in enumerate(clusters):
        #    name = cluster.metadata.name
        #    version = cluster.spec.version if hasattr(cluster.spec, "version") else "unknown"
        #    status = cluster.status.state if hasattr(cluster, "status") and hasattr(cluster.status, "state") else "unknown"
        #    options.append(f"{name} (version: {version}, status: {status})")

        # selectedIndex = self.promptForListSelect("Select cluster to migrate", options)
        # return clusters[selectedIndex]

        self.printH2("Available Db2uClusters")
        for i, cluster in enumerate(clusters):
            name = cluster.metadata.name
            version = cluster.spec.version if hasattr(cluster.spec, "version") else "unknown"
            status = cluster.status.state if hasattr(cluster, "status") and hasattr(cluster.status, "state") else "unknown"
            print(f"  {i+1}. {name} (version: {version}, status: {status})")

        selectedIndex = self.promptForInt("Select cluster to migrate", min=1, max=len(clusters))
        return clusters[selectedIndex - 1]

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
            self.printH1("DB2 Cluster Migration")

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

            # Detect clusters
            with Halo(text=f"Detecting Db2uClusters in namespace {namespace}", spinner=self.spinner) as h:
                clusters = self.detectDb2uClusters(namespace)
                if not clusters:
                    h.fail(f"No Db2uClusters found in namespace {namespace}")
                    self.fatalError(f"No Db2uClusters found in namespace {namespace}")
                h.succeed(f"Found {len(clusters)} Db2uCluster(s)")

            # Select cluster
            selectedCluster = self.promptForCluster(clusters)
            clusterName = selectedCluster.metadata.name

            # Prompt for backup
            enableBackup = self.promptForBackup()

        else:
            # Non-interactive mode
            namespace = args.namespace
            clusterName = args.cluster_name
            enableBackup = args.backup == "true" if args.backup else True

            # Validate cluster exists if name provided
            if clusterName:
                clusters = self.detectDb2uClusters(namespace)
                clusterNames = [c.metadata.name for c in clusters]
                if clusterName not in clusterNames:
                    self.fatalError(f"Cluster {clusterName} not found in namespace {namespace}")
            else:
                # Auto-select if only one cluster
                clusters = self.detectDb2uClusters(namespace)
                if len(clusters) == 0:
                    self.fatalError(f"No Db2uClusters found in namespace {namespace}")
                elif len(clusters) == 1:
                    clusterName = clusters[0].metadata.name
                else:
                    self.fatalError("Multiple clusters found. Please specify --cluster-name")

        # Confirmation
        if not self.noConfirm:
            self.printH2("Migration Summary")
            print_formatted_text(
                HTML(
                    f"<Yellow>Namespace:</Yellow> {namespace}\n"
                    f"<Yellow>Cluster:</Yellow> {clusterName}\n"
                    f"<Yellow>Backup:</Yellow> {'Enabled' if enableBackup else 'Disabled'}\n"
                )
            )
            if not self.yesOrNo("Proceed with migration"):
                print_formatted_text(HTML("<Red>Migration cancelled</Red>"))
                return

        # Set parameters
        self.setParam("db2_migration_namespace", namespace)
        self.setParam("db2_migration_cluster_name", clusterName)
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
