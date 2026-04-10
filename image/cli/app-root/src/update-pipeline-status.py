#!/usr/bin/env python3

# This script allows you to record the results of the pipeline in a MongoDb database.
# To enable this capability you must set additional environment variables as follows:
#
# - DEVOPS_MONGO_URI="mongodb://user:password@host1:port1,host2:port2/admin?tls=true&tlsAllowInvalidCertificates=true"
#

import os
import sys
import subprocess
from datetime import datetime, UTC
from pymongo import MongoClient


def send_slack_notification(action, pipeline_name, instance_id, rc=0):
    """
    Send Slack notification for pipeline start or completion using CLI command.

    Args:
        action: Either 'pipeline-start' or 'pipeline-complete'
        pipeline_name: Name of the pipeline
        instance_id: MAS instance ID
        rc: Return code (0 for success, non-zero for failure)
    """
    slack_token = os.getenv("SLACK_TOKEN", "")
    slack_channel = os.getenv("SLACK_CHANNEL", "")

    if not slack_token or not slack_channel:
        return

    try:
        print(f"Sending Slack notification: action={action}, pipeline={pipeline_name}, instance={instance_id}")

        if action == "pipeline-start":
            cmd = [
                "python3", "/opt/app-root/bin/mas-devops-notify-slack",
                "--action", "pipeline-start",
                "--instance-id", instance_id,
                "--pipeline-name", pipeline_name
            ]
        elif action == "pipeline-complete":
            cmd = [
                "python3", "/opt/app-root/bin/mas-devops-notify-slack",
                "--action", "pipeline-complete",
                "--rc", str(rc),
                "--instance-id", instance_id,
                "--pipeline-name", pipeline_name
            ]
        else:
            print(f"Unknown action: {action}")
            return

        # Run the command, ignore errors (|| true equivalent)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Slack notification sent successfully")
        else:
            print(f"Slack notification command failed (ignored): {result.stderr}")

    except Exception as e:
        print(f"Error sending Slack notification (ignored): {e}")


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

        if "" in [instanceId, pipelineName, pipelineRunName, pipelineStatus]:
            print("Slack notification skipped: one or more required env vars are not set")
        elif pipelineName not in ["mas-install", "mas-update", "mas-upgrade", "mas-uninstall"]:
            print(f"No slack notifications for pipeline: {pipelineName}")
        else:
            if pipelineStatus == "Started":
                print("Sending pipeline start notification to Slack...")
                send_slack_notification("pipeline-start", pipelineRunName, instanceId)

            elif pipelineStatus in ["Completed", "Succeeded"]:
                print("Sending pipeline completion (success) notification to Slack...")
                send_slack_notification("pipeline-complete", pipelineRunName, instanceId, rc=0)

            elif pipelineStatus == "Failed":
                print("Sending pipeline completion (failure) notification to Slack...")
                send_slack_notification("pipeline-complete", pipelineRunName, instanceId, rc=1)
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
