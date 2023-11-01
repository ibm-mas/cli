# This script allows you to record the results of the pipeline in a MongoDb database.
# To enable this capability you must set additional environment variables as follows:
#
# - DEVOPS_MONGO_URI="mongodb://user:password@host1:port1,host2:port2/admin?tls=true&tlsAllowInvalidCertificates=true"
#
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from kubernetes import client, config
from kubernetes.client import Configuration
from openshift.dynamic import DynamicClient

if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        sys.exit(0)

    print("MongoDb integration enabled (v2 data model)")

    # Initialize the properties we need
    # -------------------------------------------------------------------------
    # Note: We don't use MAS_INSTANCE_ID to remove the confusion between when a role actually
    # needs MAS_INSTANCE_ID and when we are providing it just for the reporting framework
    instanceId = os.getenv("DEVOPS_ENVIRONMENT", "none")
    build = os.getenv("DEVOPS_BUILD_NUMBER")

    if instanceId is None:
        print("Results not recorded because DEVOPS_ENVIRONMENT env var is not set")
        sys.exit(0)
    if build is None:
        print("Results not recorded because DEVOPS_BUILD_NUMBER env var is not set")
        sys.exit(0)

    runId = f"{instanceId}:{build}"

    print(f"Instance ID ............ {instanceId}")
    print(f"Build .................. {build}")
    print(f"Run ID ................. {runId}")

    # Create Kubernetes client
    # -------------------------------------------------------------------------
    if "KUBERNETES_SERVICE_HOST" in os.environ:
        config.load_incluster_config()
        k8s_config = Configuration.get_default_copy()
        k8s_client = client.api_client.ApiClient(configuration=k8s_config)
        dynClient = DynamicClient(k8s_client)
    else:
        k8s_client = config.new_client_from_config()
        dynClient = DynamicClient(k8s_client)

    setObject = {
        "timestampFinished": datetime.utcnow()
    }

    # Lookup OCP version
    # -------------------------------------------------------------------------
    cvs = dynClient.resources.get(api_version="config.openshift.io/v1", kind="ClusterVersion")
    cv = cvs.get(name="version")
    if cv.status and cv.status.desired and cv.status.desired.version:
        openshiftVersion = cv.status.desired.version
        setObject["target.ocpVersion"] = openshiftVersion
    else:
        print("Unable to lookup OCP version from ClusterVersion.config.openshift.io/v1 resource status")


    # Lookup version and build information for MAS Operators
    # -------------------------------------------------------------------------
    knownProductIds = {
        "ibm-mas": {
            "deployment": "ibm-mas-operator",
            "namespace": f"mas-{instanceId}-core",
            "apiVersion": "core.mas.ibm.com/v1",
            "kind": "Suite"
        },
        "ibm-mas-assist": {
            "deployment": "ibm-mas-assist-operator",
            "namespace": f"mas-{instanceId}-assist",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "AssistApp"
        },
        "ibm-mas-iot": {
            "deployment": "ibm-mas-iot-operator",
            "namespace": f"mas-{instanceId}-iot",
            "apiVersion": "iot.ibm.com/v1",
            "kind": "IoT"
        },
        "ibm-mas-manage": {
            "deployment": "ibm-mas-manage-operator",
            "namespace": f"mas-{instanceId}-manage",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "ManageApp"
        },
        "ibm-mas-monitor": {
            "deployment": "ibm-mas-monitor-operator",
            "namespace": f"mas-{instanceId}-monitor",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "MonitorApp"
        },
        "ibm-mas-optimizer": {
            "deployment": "ibm-mas-optimizer-operator",
            "namespace": f"mas-{instanceId}-optimizer",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "OptimizerApp"
        },
        "ibm-mas-predict": {
            "deployment": "ibm-mas-predict-operator",
            "namespace": f"mas-{instanceId}-predict",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "PredictApp"
        },
        "ibm-mas-visualinspection": {
            "deployment": "ibm-mas-visualinspection-operator",
            "namespace": f"mas-{instanceId}-visualinspection",
            "apiVersion": "apps.mas.ibm.com/v1",
            "kind": "VisualInspectionApp"
         }
    }

    for productId in knownProductIds:
        apiVersion = knownProductIds[productId]["apiVersion"]
        kind = knownProductIds[productId]["kind"]
        deploymentName = knownProductIds[productId]["deployment"]
        deploymentNamespace = knownProductIds[productId]["namespace"]

        # Lookup version
        try:
            crs = k8sUtil.dynClient.resources.get(api_version=apiVersion, kind=kind)
            cr = crs.get(name=instanceId, namespace=deploymentNamespace)
            if cr.status and cr.status.versions:
                productVersion = cr.status.versions.reconciled

                setObject[f"products.{productId}.productId"] = productId
                setObject[f"products.{productId}.version"] = productVersion

                # Lookup build information
                try:
                    deployments = dynClient.resources.get(api_version='v1', kind='Deployment')
                    deploymentObj = deployments.get(name=deploymentName, namespace=deploymentNamespace)
                    if deploymentObj is not None:
                        deploymentDict = deploymentObj.to_dict()
                        if "mas.ibm.com/buildId" in deploymentDict["metadata"]["labels"]:
                            productBuildId = deploymentDict["metadata"]["labels"]["mas.ibm.com/buildId"]
                            productBuildNumber = deploymentDict["metadata"]["labels"]["mas.ibm.com/buildNumber"]

                            setObject[f"products.{productId}.buildId"] = productBuildId
                            setObject[f"products.{productId}.buildNumber"] = productBuildNumber
                    else:
                        print(f"Unable to determine {deploymentName} build information: deployment is none")
                except Exception as e:
                    print(f"Unable to determine {productId} build information: {e}")
            else:
                print(f"Unable to determine {productId} version: status.versions.reconciled unavailable")
        except Exception as e:
            print(f"Unable to determine {productId} version: {e}")

    # Connect to mongoDb
    # -------------------------------------------------------------------------
    client = MongoClient(os.getenv("DEVOPS_MONGO_URI"))
    db = client.masfvt

    # Update the summary document
    # -------------------------------------------------------------------------
    result1 = db.runsv2.find_one_and_update(
        {"_id": runId},
        {'$set': setObject},
        upsert=False
    )

    print("Run information updated in MongoDb (v2 data model)")
