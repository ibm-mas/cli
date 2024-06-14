import os
import threading
import zipfile
import sys
import json
import yaml
import requests
from pathlib import Path
from collections import OrderedDict
from subprocess import PIPE, Popen, TimeoutExpired
from kubernetes.client import Configuration
from openshift.dynamic import DynamicClient
from kubernetes import client, config


instanceId = os.getenv("INSTANCE_ID")
workspaceId = os.getenv("WORKSPACE_ID")
uploadFile = os.getenv("UPLOAD_FILE")
artKey = os.getenv("ARTIFACTORY_TOKEN")
artDir = os.getenv("ARTIFACTORY_UPLOAD_DIR")
output_filename = "mobile-is-versions.json"

class RunCmdResult(object):
    def __init__(self, returnCode, output, error):
        self.rc = returnCode
        self.out = output
        self.err = error

    def successful(self):
        return self.rc == 0

    def failed(self):
        return self.rc != 0

def run_cmd(cmdArray, timeout=630):
    """
    Run a command on the local host.  This drives all the helm operations,
    as there is no python Helm client available.
    # Parameters
    cmdArray (list<string>): Command to execute
    timeout (int): How long to allow for the command to complete
    # Returns
    [int, string, string]: `returnCode`, `stdOut`, `stdErr`
    """

    lock = threading.Lock()

    with lock:
        p = Popen(cmdArray, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        try:
            output, error = p.communicate(timeout=timeout)
            return RunCmdResult(p.returncode, output, error)
        except TimeoutExpired as e:
            return RunCmdResult(127, 'TimeoutExpired', str(e))

def get_graphite_versions():
    # This list will contains all files found in the maxinst pod
    apps_list = []

    # Downloads all zip files from maxinst container
    try:
        pods = dynClient.resources.get(api_version="v1", kind="Pod")
        podList = pods.get(namespace=f"mas-{instanceId}-manage", label_selector='mas.ibm.com/appType=maxinstudb')

        if podList is None or podList.items is None or len(podList.items) == 0:
            pass
        else:
            podName = podList.items[0].metadata.name

            # list all graphite zip packages in maxinst pod
            ocExecCommand = ["oc", "exec", "-n", f"mas-{instanceId}-manage", podName, "--", "ls", "/opt/IBM/SMP/maximo/tools/maximo/en/graphite/apps"]
            result = run_cmd(ocExecCommand)
            ls_result = result.out.decode('utf-8')
            apps_list = ls_result.split("\n")
            # removes last empty value from the list
            apps_list.pop()

            # Download all packages that were found
            for a in apps_list:
                print("Downloading:", a)
                ocExecCommand = [
                    "oc", "cp", "-n", f"mas-{instanceId}-manage", 
                    f"{podName}:/opt/IBM/SMP/maximo/tools/maximo/en/graphite/apps/{a}",
                    f"./{a}",
                    "--retries=10"
                ]
                run_cmd(ocExecCommand)

    except Exception as e:
        print(f"Unable to download mobile packages from maxinst pod: {e}")
        sys.exit(1)


    # Downloading navigator from mobileapi pod
    try:
        pods = dynClient.resources.get(api_version="v1", kind="Pod")
        podList = pods.get(namespace=f"mas-{instanceId}-core", label_selector=f'app={instanceId}-mobileapi')

        if podList is None or podList.items is None or len(podList.items) == 0:
            pass
        else:
            podName = podList.items[0].metadata.name

            # list navigator zip packages in mobileapi pod
            ocExecCommand = ["oc", "exec", "-n", f"mas-{instanceId}-core", podName, "--", "ls", "/etc/mobile/packages"]
            result = run_cmd(ocExecCommand)
            ls_result = result.out.decode('utf-8')
            apps_list = ls_result.split("\n")
            # removes last empty value from the list
            apps_list.pop()

            for a in apps_list:
                print("Downloading:", a)
                ocExecCommand = [
                    "oc", "cp", "-n", f"mas-{instanceId}-core", 
                    f"{podName}:/etc/mobile/packages/{a}",
                    f"./{a}",
                    "--retries=10"
                ]
                run_cmd(ocExecCommand)
    except Exception as e:
        print(f"Unable to download mobileapi navigator package from mobileapi pod: {e}")
        sys.exit(1)


    # Extracting build.json from each file and deleting zip
    pathlist = Path(".").glob('*.zip')
    for app_zip_file in pathlist:
        zip_file_path = f"./{str(app_zip_file)}"
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extract('build.json', '.')
            zip_ref.close()
        zip_file_prefix = zip_file_path.split(".zip")
        os.rename('./build.json', f'{zip_file_prefix[0]}.json')
        os.remove(zip_file_path)

    # dictionary that will contain all graphite versions for all found zips
    graphite_json = {}

    pathlist = Path(".").glob('*.json')
    for path in pathlist:
        path_in_str = str(path)

        with open(path_in_str, 'r', encoding="utf-8") as openfile:
            json_object = json.load(openfile)

        graphite_json.update(
            {
                json_object.get("applicationId"): {
                    "version": json_object.get("version"),
                    "applicationId": json_object.get("applicationId"),
                    "applicationTitle": json_object.get("applicationTitle"),
                    "mobileVersion": json_object.get("mobileVersion"),
                    "buildToolsVersion": json_object.get("buildToolsVersion"),
                    "appProcessorVersion": json_object.get("appProcessorVersion")
                }
            }
        )

        # removing empty mobile version or non mobile apps
        if json_object.get("mobileVersion") is None:
            del graphite_json[json_object.get("applicationId")]["mobileVersion"]

        # removing empty title from apps with no title
        if json_object.get("applicationTitle") is None:
            del graphite_json[json_object.get("applicationId")]["applicationTitle"]

        # delete build.json file
        os.remove(path_in_str)

    # ordering json file
    graphite_json_sorted = OrderedDict(sorted(graphite_json.items()))

    return graphite_json_sorted

def get_mobile_and_is_image_tags():

    images_json = {}

    # getting mobileapi image version from entitymgr-suite pod
    try:
        pods = dynClient.resources.get(api_version="v1", kind="Pod")
        podList = pods.get(namespace=f"mas-{instanceId}-core", label_selector=f'app={instanceId}-entitymgr-suite')

        if podList is None or podList.items is None or len(podList.items) == 0:
            pass
        else:
            podName = podList.items[0].metadata.name

            # list navigator zip packages in mobileapi pod
            ocExecCommand = ["oc", "exec", "-n", f"mas-{instanceId}-core", podName, "--", "cat", "/opt/ansible/roles/suite/vars/images.yml"]
            result = run_cmd(ocExecCommand)
            cat_result = result.out.decode('utf-8')
            images = yaml.safe_load(cat_result)
            images_json.update({"mobileapi": images['defaultTags']['mobileapi']})
    except Exception as e:
        print(f"Unable to catch images file from entitymgr pod: {e}")
        sys.exit(1)

    # getting industry solutions images version from entitymgr-ws
    try:
        pods = dynClient.resources.get(api_version="v1", kind="Pod")
        podList = pods.get(namespace=f"mas-{instanceId}-manage", label_selector='mas.ibm.com/appType=entitymgr-ws-operator')

        if podList is None or podList.items is None or len(podList.items) == 0:
            pass
        else:
            podName = podList.items[0].metadata.name

            # list navigator zip packages in mobileapi pod
            ocExecCommand = ["oc", "exec", "-n", f"mas-{instanceId}-manage", podName, "--", "cat", "/opt/ansible/roles/workspace/vars/images.yml"]
            result = run_cmd(ocExecCommand)
            cat_result = result.out.decode('utf-8')
            images = yaml.safe_load(cat_result)
            images_json.update(images['defaultTags'])

    except Exception as e:
        print(f"Unable to catch images file from entitymgr pod: {e}")
        sys.exit(1)

    images_json_sorted = OrderedDict(sorted(images_json.items()))

    return images_json_sorted

def artifactory_upload():

    url = artDir + '/' + output_filename
    bearer = f"Bearer {artKey}"
    headers = {
        'content-type': 'application/json',
        'Authorization': bearer
    }

    with open(output_filename, 'rb') as f:
        r = requests.put(url, data=f, headers=headers, timeout=10)

    if r.status_code != 201:
        print("Upload failed.")
    else:
        print("Upload successful")
        print("Download URL:", r.json()['downloadUri'])


if __name__ == "__main__":

    if "KUBERNETES_SERVICE_HOST" in os.environ:
        config.load_incluster_config()
        k8s_config = Configuration.get_default_copy()
        k8s_client = client.api_client.ApiClient(configuration=k8s_config)
        dynClient = DynamicClient(k8s_client)
    else:
        k8s_client = config.new_client_from_config()
        dynClient = DynamicClient(k8s_client)

    if os.path.isfile(output_filename):
        print("Found an existing output file. Deleting...")
        os.remove(output_filename)

    print("Retrieving Graphite versions for Manage apps")
    graphite_versions = get_graphite_versions()

    print("Retrieving image versions for Manage IS and Add-ons ")
    img_versions = get_mobile_and_is_image_tags()

    print("Generating output file with versions")
    mobile_is_versions = {}
    mobile_is_versions.update(
        {
            "graphite_versions": graphite_versions,
            "images_versions": img_versions
        }
    )

    with open(output_filename, "w", encoding="utf-8") as outfile:
        json.dump(mobile_is_versions, outfile, indent=4)

    print("Printing gererated file:")
    print("************************************************")
    with open(output_filename, "r", encoding="utf-8") as readfile:
        print(readfile.read())
    print("************************************************")

    # Upload logs conditionally based o env var
    if uploadFile:
        print("Uploading file to artifactory")
        artifactory_upload()

    print("Done")
