# This script allows you to record the a timestamp  in a MongoDb database whenever invoked in task or worker.
# To enable this capability you must set additional environment variables as follows:
#
#
import os
import sys
from datetime import datetime, UTC
from pymongo import MongoClient


def invalid_timestamp_key(key: str) -> bool:
    return key == "" or "." in key or key.startswith("$")


if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        sys.exit(0)

    print("MongoDb integration enabled (v2 data model)")

    if len(sys.argv) != 2:
        print("Usage: record-run-timestamp.py <timestampKey>")
        print("Example: record-run-timestamp.py deploymentCompleted")
        sys.exit(1)

    timestampKey = sys.argv[1]
    if invalid_timestamp_key(timestampKey):
        print("Invalid timestamp key")
        sys.exit(1)

    # Initialize the properties we need

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
    currentTime = datetime.now(UTC)

    print(f"Instance ID ............ {instanceId}")
    print(f"Build .................. {build}")

    print(f"Run ID ................. {runId}")

    # Connect to mongoDb
    client = MongoClient(os.getenv("DEVOPS_MONGO_URI"))
    db = client.masfvt

    # Update or create summary doc
    db.runsv2.find_one_and_update(
        {"_id": runId},
        {
            '$setOnInsert': {
                "_id": runId,
                "target": {
                    "instanceId": instanceId,
                    "buildId": build,
                }
            },
            '$set': {
                timestampKey: currentTime,
            }
        },
        upsert=True
    )

    print(f"Recorded timestamp for {timestampKey} at {currentTime} to MongoDb (v2 data model)")
