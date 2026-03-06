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

# Import Slack notification functions directly
try:
    from mas.devops.slack import notifyPipelineStart, notifyPipelineComplete
    SLACK_AVAILABLE = True
except ImportError:
    print("Warning: mas.devops.slack module not available, Slack notifications will be disabled")
    SLACK_AVAILABLE = False


def send_slack_notification(action, pipeline_name, pipelinerun_name, pipelinerun_namespace, instance_id, rc=0):
    """
    Send Slack notification for pipeline start or completion using direct function calls.

    Args:
        action: Either 'pipeline-start' or 'pipeline-complete'
        pipeline_name: Name of the pipeline
        pipelinerun_name: Name of the pipeline run
        pipelinerun_namespace: Namespace of the pipeline run
        instance_id: MAS instance ID
        rc: Return code (0 for success, non-zero for failure)
    """
    if not SLACK_AVAILABLE:
        print("Slack notification skipped: mas.devops.slack module not available")
        return

    slack_token = os.getenv("SLACK_TOKEN", "")
    slack_channel = os.getenv("SLACK_CHANNEL", "")

    if not slack_token or not slack_channel:
        print("Slack notification skipped: SLACK_TOKEN or SLACK_CHANNEL not set")
        return

    # Parse comma-separated channel list
    channel_list = [ch.strip() for ch in slack_channel.split(",")]

    try:
        print(f"Sending Slack notification: action={action}, pipeline={pipeline_name}, instance={instance_id}")

        if action == "pipeline-start":
            result = notifyPipelineStart(channel_list, instance_id, pipeline_name)
            if result:
                print("Pipeline start notification sent successfully")
            else:
                print("Failed to send pipeline start notification")

        elif action == "pipeline-complete":
            result = notifyPipelineComplete(channel_list, rc, instance_id, pipeline_name)
            if result:
                print(f"Pipeline complete notification sent successfully (rc={rc})")
            else:
                print("Failed to send pipeline complete notification")
        else:
            print(f"Unknown action: {action}")

    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Initialize the properties we need
    # Note: We don't use MAS_INSTANCE_ID to remove the confusion between when a role actually
    # needs MAS_INSTANCE_ID and when we are providing it just for the reporting framework
    instanceId = os.getenv("DEVOPS_ENVIRONMENT", "")
    build = os.getenv("DEVOPS_BUILD_NUMBER", "")
    pipelineName = os.getenv("PIPELINE_NAME", "")
    pipelineStatus = os.getenv("PIPELINE_STATUS", "")
    pipelineRunName = os.getenv("PIPELINERUN_NAME", "")
    pipelineRunNamespace = os.getenv("PIPELINERUN_NAMESPACE", "")

    # =========================================================================
    # Slack Notification Logic (runs independently)
    # =========================================================================
    SLACK_TOKEN = os.getenv("SLACK_TOKEN", "")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")

    if SLACK_TOKEN and SLACK_CHANNEL:
        print("\nSlack integration enabled")

        if "" in [instanceId, pipelineName, pipelineStatus, pipelineRunName, pipelineRunNamespace]:
            print("Slack notification skipped: one or more required env vars are not set")
        else:
            if pipelineStatus == "Started":
                print("Sending pipeline start notification to Slack...")
                send_slack_notification("pipeline-start", pipelineName, pipelineRunName, pipelineRunNamespace, instanceId)

            elif pipelineStatus in ["Completed", "Succeeded"]:
                print("Sending pipeline completion (success) notification to Slack...")
                send_slack_notification("pipeline-complete", pipelineName, pipelineRunName, pipelineRunNamespace, instanceId, rc=0)

            elif pipelineStatus == "Failed":
                print("Sending pipeline completion (failure) notification to Slack...")
                send_slack_notification("pipeline-complete", pipelineName, pipelineRunName, pipelineRunNamespace, instanceId, rc=1)
    else:
        print("\nSlack integration disabled (SLACK_TOKEN or SLACK_CHANNEL not set)")

    # =========================================================================
    # MongoDB Integration Logic (runs independently)
    # =========================================================================
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        print("\nMongoDb integration disabled (DEVOPS_MONGO_URI not set)")
        sys.exit(0)

    print(f"Instance ID .............. {instanceId}")
    print(f"Build .................... {build}")
    print(f"Pipeline Name ............ {pipelineName}")
    print(f"PipelineRun Name ......... {pipelineRunName}")
    print(f"PipelineRun Namespace .... {pipelineRunNamespace}")
    print(f"Status ................... {pipelineStatus}")

    print("\nMongoDb integration enabled (v2 data model)")

    if "" in [instanceId, build, pipelineName, pipelineStatus, pipelineRunName, pipelineRunNamespace]:
        print("Pipeline status not recorded because one or more required env vars are not set")
        sys.exit(0)

    runId = f"{instanceId}:{build}"

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

    print("Pipeline status recorded in MongoDB successfully")
