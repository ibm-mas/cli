import os
import sys
from datetime import datetime
from pymongo import MongoClient
from kubernetes import client, config
from kubernetes.client import Configuration
from openshift.dynamic import DynamicClient
from slackclient import SlackClient
from jira import JIRA


# Post message to Slack
# -----------------------------------------------------------------------------
def postMessage(channelName, messageBlocks, threadId=None):
    if threadId is None:
        print(f"Posting {len(messageBlocks)} block message to {channelName} in Slack")
        response = sc.api_call("chat.postMessage", channel=channelName, blocks=messageBlocks, mrkdwn=True, parse="none", as_user=True )
    else:
        print(f"Posting {len(messageBlocks)} block message to {channelName} on thread {threadId} in Slack")
        response = sc.api_call("chat.postMessage", channel=channelName, thread_ts=threadId, blocks=messageBlocks, mrkdwn=True, parse="none", as_user=True )

    if not response['ok']:
      print(response)
      print("Failed to call Slack API")
    return response


# Build header block for Slack message
# -----------------------------------------------------------------------------
def buildHeader(title):
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
                "text": title,
                "emoji": True
        }
    }


# Build section block for Slack message
# -----------------------------------------------------------------------------
def buildSection(text):
  return {
    "type": "section",
    "text": {
      "type": "mrkdwn",
      "text": text
    }
  }


# Build context block for Slack message
# -----------------------------------------------------------------------------
def buildContext(texts):
    elements = []
    for text in texts:
        elements.append({ "type": "mrkdwn", "text": text })

    return {
        "type": "context",
        "elements": elements
    }


# Script start
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if "DEVOPS_MONGO_URI" not in os.environ or os.environ['DEVOPS_MONGO_URI'] == "":
        sys.exit(0)

    DRY_RUN = False
    if "DRY_RUN" in os.environ:
        DRY_RUN = True

    print("MongoDb integration enabled (v2 data model)")

    # Initialize the properties we need
    # -------------------------------------------------------------------------
    # Note: We don't use MAS_INSTANCE_ID to remove the confusion between when a role actually
    # needs MAS_INSTANCE_ID and when we are providing it just for the reporting framework
    instanceId = os.getenv("DEVOPS_ENVIRONMENT")
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

        print(f"Looking for info about {productId}")
        # Lookup version
        try:
            crs = dynClient.resources.get(api_version=apiVersion, kind=kind)
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
    if not DRY_RUN:
        result1 = db.runsv2.find_one_and_update(
            {"_id": runId},
            {'$set': setObject},
            upsert=False
        )
        print(f"Run information updated in MongoDb (v2 data model) {setObject}")
    else:
        print(f"Run information NOT updated in MongoDb because DRY_RUN is set")


    # Check pre-reqs for Slack integration
    # -------------------------------------------------------------------------
    FVT_SLACK_TOKEN = os.getenv("FVT_SLACK_TOKEN")
    if FVT_SLACK_TOKEN is None or FVT_SLACK_TOKEN == "":
        print("FVT_SLACK_TOKEN is not set")
        sys.exit(0)

    FVT_SLACK_CHANNEL = os.getenv("FVT_SLACK_CHANNEL")
    if FVT_SLACK_CHANNEL is None or FVT_SLACK_CHANNEL == "":
        print("FVT_SLACK_CHANNEL is not set")
        sys.exit(0)

    FVT_JIRA_TOKEN = os.getenv("FVT_JIRA_TOKEN")
    if FVT_JIRA_TOKEN is None or FVT_JIRA_TOKEN == "":
        print("FVT_JIRA_TOKEN is not set")
        sys.exit(0)

    sc = SlackClient(FVT_SLACK_TOKEN)
    jira = JIRA(server="https://jsw.ibm.com", token_auth=FVT_JIRA_TOKEN)


    # Lookup test results
    # -------------------------------------------------------------------------
    result = db.runsv2.find_one({"_id": runId})


    # Generate main message
    # -------------------------------------------------------------------------
    messageBlocks = []
    messageBlocks.append(buildHeader(f"FVT Report: {instanceId} #{build}"))
    messageBlocks.append(buildSection(f"Test result summary for *<https://dashboard.masdev.wiotp.sl.hursley.ibm.com/tests/{instanceId}|{instanceId}#{build}>*"))

    for product in sorted(result["products"]):
        version = result["products"][product]["version"]
        tests = 0
        skipped = 0
        errors = 0
        failures = 0
        if "results" in result["products"][product]:
            for suite in result["products"][product]["results"]:
                suiteResults = result["products"][product]["results"][suite]

                tests += suiteResults["tests"]
                skipped += suiteResults["skipped"]
                errors += suiteResults["errors"]
                failures += suiteResults["failures"]

        # print(f"{product} - {tests} tests {skipped} skipped {errors} errors {failures} failures")

        if failures > 0:
            icon = ":large_red_square:"
        elif errors > 0:
            icon = ":large_yellow_square:"
        else:
            icon = ":large_green_square:"

        context = [
            f"{icon} *{product}* {version}",
            f"*{tests}* tests"
        ]
        if skipped > 0:
            context.append(f"*{skipped}* skipped")
        if errors > 0:
            context.append(f"*{errors}* errors")
        if failures > 0:
            context.append(f"*{failures}* failures")

        messageBlocks.append(buildContext(context))

    messageBlocks.append(buildSection(f"Download Must Gather from <https://na.artifactory.swg-devops.com/ui/repos/tree/General/wiotp-generic-logs/mas-fvt/{instanceId}/{build}|Artifactory> (may not be available yet), see thread for more information ..."))
    response = postMessage(FVT_SLACK_CHANNEL, messageBlocks)
    threadId = response["ts"]


    # Generate threaded messages with failure details
    # -------------------------------------------------------------------------
    for product in result["products"]:
        messageBlocks = []
        messageBlocks.append(buildHeader(f"{product}"))
        messageBlocks.append(buildSection(f"The following testsuites reported one or more failures or errors during *<https://dashboard.masdev.wiotp.sl.hursley.ibm.com/tests/{instanceId}|{instanceId}#{build}>*"))

        if "results" in result["products"][product]:
            for suite in result["products"][product]["results"]:
                suiteResults = result["products"][product]["results"][suite]

                tests = suiteResults["tests"]
                skipped = suiteResults["skipped"]
                errors = suiteResults["errors"]
                failures = suiteResults["failures"]

                if errors > 0 or failures > 0:
                    if failures > 0:
                        icon = ":large_red_square:"
                    elif errors > 0:
                        icon = ":large_yellow_square:"

                    # Find Jira issues
                    openIssues = []
                    results = jira.search_issues(f'status != "Done" AND status != "Cancelled" AND type = "Bug" AND labels = "masfvt" AND labels="suite:{product}/{suite}" ORDER BY team,severity', maxResults=-1)
                    for issue in results:
                        key = issue.key
                        summary = issue.fields.summary
                        summary = summary.replace(">", "&gt;")
                        if len(summary) > 60:
                            summary = summary[:57] + "..."

                        if issue.fields.assignee is None:
                            assignee = ":interrobang: Unassigned Person"
                            assignedType = "unassigned"
                        else:
                            assignee = issue.fields.assignee.displayName
                            assignedType = "assigned"

                        if issue.fields.customfield_11600 is None:
                            team = ":interrobang: Unassigned Team"
                        else:
                            team = issue.fields.customfield_11600.name

                        if issue.fields.customfield_10700 is None:
                            severity = ":interrobang: Unknown"
                        else:
                            severity = issue.fields.customfield_10700.value

                        status = issue.fields.status.statusCategory.name

                        if status == "To Do":
                            statusIcon = ":black_circle:"
                        elif status in ["In Progress","Reviewing"]:
                            statusIcon = ":large_blue_circle:"
                        elif status == "Blocked":
                            statusIcon = ":large_red_circle:"
                        else:
                            statusIcon = ":interrobang:"

                        openIssues.append(f"{statusIcon} <https://jsw.ibm.com/browse/{key}|{key}> {summary} ({assignee})")

                    context = [
                        f"{icon} *<https://dashboard.masdev.wiotp.sl.hursley.ibm.com/tests/{instanceId}/testsuite/{product}/{suite}|{product}/{suite}>*",
                        f"*{tests}* tests",
                        f"*{skipped}* skipped",
                        f"*{errors}* errors",
                        f"*{failures}* failures"
                    ]
                    messageBlocks.append(buildContext(context))
                    if len(openIssues) > 0:
                        messageBlocks.append(buildContext(["\n".join(openIssues)]))
                    else:
                        messageBlocks.append(buildContext(["• No open issues - <https://jsw.ibm.com/secure/CreateIssue!default.jspa|create one>"]))

        if len(messageBlocks) > 2 and len(messageBlocks) <= 50:
            postMessage(FVT_SLACK_CHANNEL, messageBlocks, threadId)

        if len(messageBlocks) > 50:
            messageBlocks = []
            messageBlocks.append(buildHeader(f"{product}"))
            messageBlocks.append(buildSection(f"Test result summary for *<https://dashboard.masdev.wiotp.sl.hursley.ibm.com/tests/{instanceId}|{instanceId}#{build}>*"))
            messageBlocks.append(buildSection(f"Sorry.  The build is so bad it can't even be summarized within the size limit of a Slack message!"))
            postMessage(FVT_SLACK_CHANNEL, messageBlocks, threadId)
