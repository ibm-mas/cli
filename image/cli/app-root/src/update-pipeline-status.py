#!/usr/bin/env python3

# This script allows you to record the results of the pipeline in a MongoDb database.
# To enable this capability you must set additional environment variables as follows:
#
# - DEVOPS_MONGO_URI="mongodb://user:password@host1:port1,host2:port2/admin?tls=true&tlsAllowInvalidCertificates=true"
#

import os
import sys
from datetime import datetime, UTC
from pymongo import MongoClient

if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        sys.exit(0)

    print("MongoDb integration enabled (v2 data model)")

    # Initialize the properties we need

    # Note: We don't use MAS_INSTANCE_ID to remove the confusion between when a role actually
    # needs MAS_INSTANCE_ID and when we are providing it just for the reporting framework
    instanceId = os.getenv("DEVOPS_ENVIRONMENT", "")
    build = os.getenv("DEVOPS_BUILD_NUMBER", "")
    pipelineName = os.getenv("PIPELINE_NAME", "")
    pipelineStatus = os.getenv("PIPELINE_STATUS", "")
    pipelineRunName = os.getenv("PIPELINERUN_NAME", "")
    pipelineRunNamespace = os.getenv("PIPELINERUN_NAMESPACE", "")

    if "" in [instanceId, build, pipelineName, pipelineStatus, pipelineRunName, pipelineRunNamespace]:
        print("Pipeline status not recorded because one or more required env vars are not set")
        sys.exit(0)

    runId = f"{instanceId}:{build}"

    print(f"Instance ID .............. {instanceId}")
    print(f"Build .................... {build}")
    print(f"Pipeline Name ............ {pipelineName}")
    print(f"PipelineRun Name ......... {pipelineRunName}")
    print(f"PipelineRun Namespace .... {pipelineRunNamespace}")
    print(f"Status ................... {pipelineStatus}")

    # Connect to mongoDb
    client = MongoClient(os.getenv("DEVOPS_MONGO_URI"))
    db = client.masfvt

    updates = {
        f"pipelines.{pipelineName}.name": pipelineRunName,
        f"pipelines.{pipelineName}.namespace": pipelineRunNamespace
    }

    if pipelineStatus == "Started":
        updates = {
            f"pipelines.{pipelineName}.status": "Started",
            f"pipelines.{pipelineName}.timestamp": datetime.now(UTC)
        }
    elif pipelineStatus in ["Completed", "Succeeded"]:
        updates = {
            f"pipelines.{pipelineName}.status": "Completed",
            f"pipelines.{pipelineName}.timestampFinished": datetime.now(UTC)
        }
    elif pipelineStatus == "Failed":
        updates = {
            f"pipelines.{pipelineName}.status": "Failed",
            f"pipelines.{pipelineName}.timestampFinished": datetime.now(UTC)
        }
    else:
        print("Unexpected state detected")
        sys.exit(0)

    # Update or create summary doc
    result1 = db.runsv2.find_one_and_update(
        {"_id": runId},
        {
            '$setOnInsert': {
                "_id": runId,
                "timestamp": datetime.now(UTC),
                "target": {
                    "instanceId": instanceId,
                    "buildId": build,
                }
            },
            '$set': updates
        },
        upsert=True
    )
