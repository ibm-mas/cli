# This script allows you to record the results of the pipeline in a MongoDb database.
# To enable this capability you must set additional environment variables as follows:
#
# - DEVOPS_MONGO_URI="mongodb://user:password@host1:port1,host2:port2/admin?tls=true&tlsAllowInvalidCertificates=true"
#
import os
import xml.etree.ElementTree as ET
import sys
from datetime import datetime
from pymongo import MongoClient
from xmljson import Yahoo
import glob

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
    junitOutputDir = os.getenv("JUNIT_OUTPUT_DIR", "/tmp")
    productId = os.getenv("PRODUCT_ID", "ibm-mas-devops")

    channelId = "n/a"
    cliVersion = os.getenv("VERSION", "unknown")
    ansibleDevopsVersion = os.getenv("ANSIBLE_DEVOPS_VERSION", "unknown")

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

    print(f"Run ID ................. {runId}")
    print(f"Result ID .............. {resultId}")

    resultFiles = glob.glob(f'{junitOutputDir}/*.xml')
    for resultfile in resultFiles:
        try:
            tree = ET.parse(resultfile)
        except (IOError, ET.ParseError) as e:
            print(f"Functional Test result file was not generated for {suite} in build {build}: {e}")
            sys.exit(0)

        root = tree.getroot()

        # Convert junit xml to json
        bf = Yahoo(dict_type=dict)
        resultDoc = bf.data(root)

        if isinstance(resultDoc["testsuites"]["testsuite"]["testcase"], list):
            for testcase in resultDoc["testsuites"]["testsuite"]["testcase"]:
                testcase["name"] = testcase["name"].replace("[localhost] localhost: ", "")
                # Playbooks don't have ibm/mas_devops in the classname but do have /opt/app-root.
                # Roles have both ibm/mas_devops and /opt/app-root.
                # Guard against both and remove when required.
                if "/opt/app-root/" in testcase["classname"]:
                    testcase["classname"] = testcase["classname"].split("/opt/app-root/")[1]
                if "ibm/mas_devops/" in testcase["classname"]:
                    testcase["classname"] = testcase["classname"].split("ibm/mas_devops/")[1]
        else:
            testcase = resultDoc["testsuites"]["testsuite"]["testcase"]
            testcase["name"] = testcase["name"].replace("[localhost] localhost: ", "")
            # Playbooks don't have ibm/mas_devops in the classname but do have /opt/app-root.
            # Roles have both ibm/mas_devops and /opt/app-root.
            # Guard against both and remove when required.
            if "/opt/app-root/" in testcase["classname"]:
                testcase["classname"] = testcase["classname"].split("/opt/app-root/")[1]
            if "ibm/mas_devops/" in testcase["classname"]:
                testcase["classname"] = testcase["classname"].split("ibm/mas_devops/")[1]
        # Enrich document
        resultDoc["_id"] = resultId
        resultDoc["build"] = build
        resultDoc["suite"] = suite
        resultDoc["timestamp"] = datetime.utcnow()
        resultDoc["target"] = {
            "instanceId": instanceId,
            "build": build,
            "productId": productId,
            "channelId": channelId,
            "version": cliVersion,
            "ansibleDevopsVersion": ansibleDevopsVersion
        }

        # Look for existing summary document
        suiteSummary = {
            "tests": int(resultDoc["testsuites"]["testsuite"]["tests"]),
            "errors": int(resultDoc["testsuites"]["testsuite"]["errors"]),
            "name": suite,
            "skipped": int(resultDoc["testsuites"]["testsuite"]["skipped"]),
            "time": float(resultDoc["testsuites"]["testsuite"]["time"]),
            "failures": int(resultDoc["testsuites"]["testsuite"]["failures"])
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
                    f"products.{productId}.results.{suite}": suiteSummary
                }
            },
            upsert=True
        )

        # Replace or create result doc
        result2 = db.resultsv2.replace_one(
            {"_id": resultId},
            resultDoc,
            upsert=True
        )
        print("Pipeline results saved to MongoDb (v2 data model)")
