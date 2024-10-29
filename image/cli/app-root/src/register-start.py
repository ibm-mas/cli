# This script allows you to record the results of the pipeline in a MongoDb database.
# To enable this capability you must set additional environment variables as follows:
#
# - DEVOPS_MONGO_URI="mongodb://user:password@host1:port1,host2:port2/admin?tls=true&tlsAllowInvalidCertificates=true"
#
import os
import sys
from datetime import datetime
from pymongo import MongoClient

if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        sys.exit(0)

    print("MongoDb integration enabled (v2 data model)")

    # Initialize the properties we need

    # Note: We don't use MAS_INSTANCE_ID to remove the confusion between when a role actually
    # needs MAS_INSTANCE_ID and when we are providing it just for the reporting framework
    instanceId = os.getenv("DEVOPS_ENVIRONMENT", "none")
    build = os.getenv("DEVOPS_BUILD_NUMBER")
    suite = os.getenv("DEVOPS_SUITE_NAME", "")
    productId = os.getenv("PRODUCT_ID", "ibm-mas-devops")

    channelId = "n/a"
    cliVersion = os.getenv("VERSION", "unknown")
    ansibleDevopsVersion = os.getenv("ANSIBLE_DEVOPS_VERSION", "unknown")
    gitopsVersion = os.getenv("GITOPS_VERSION", "unknown")

    if suite == "":
        print("Results not recorded because DEVOPS_SUITE_NAME is not defined")
        sys.exit(0)
    if instanceId is None:
        print("Results not recorded because DEVOPS_ENVIRONMENT env var is not set")
        sys.exit(0)
    if build is None:
        print("Results not recorded because DEVOPS_BUILD_NUMBER env var is not set")
        sys.exit(0)

    runId = f"{instanceId}:{build}"
    resultId = f"{instanceId}:{build}:{productId}:{suite}"

    print(f"Instance ID ............ {instanceId}")
    print(f"Product ID ............. {productId}")
    print(f"Build .................. {build}")
    print(f"Suite .................. {suite}")
    print(f"Channel ID ............. {channelId}")

    print(f"CLI Version ............ {cliVersion}")
    print(f"mas_devops Version ..... {ansibleDevopsVersion}")
    print(f"gitops Version ......... {gitopsVersion}")

    print(f"Run ID ................. {runId}")
    print(f"Result ID .............. {resultId}")

    # Generate placeholder that tells us "the test has started"
    suiteSummary = {
        "tests": 0,
        "errors": 0,
        "name": suite,
        "skipped": 0,
        "time": -1,
        "failures": 0,
        "startTime": datetime.utcnow()
    }

    # Connect to mongoDb
    client = MongoClient(os.getenv("DEVOPS_MONGO_URI"))
    db = client.masfvt

    # Update or create summary doc
    result1 = db.runsv2.find_one_and_update(
        {"_id": runId},
        {
            '$setOnInsert': {
                "_id": runId,
                "timestamp": datetime.utcnow(),
                "target": {
                    "instanceId": instanceId,
                    "buildId": build,
                }
            },
            '$set': {
                f"products.{productId}.productId": productId,
                f"products.{productId}.channelId": channelId,
                f"products.{productId}.version": cliVersion,
                f"products.{productId}.ansibleDevopsVersion": ansibleDevopsVersion,
                f"products.{productId}.gitopsVersion": gitopsVersion,
                f"products.{productId}.results.{suite}": suiteSummary
            }
        },
        upsert=True
    )
