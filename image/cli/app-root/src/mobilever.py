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


class RunCmdResult(object):
    def __init__(self, returnCode, output, error):
        self.rc = returnCode
        self.out = output
        self.err = error

    def successful(self):
        return self.rc == 0

    def failed(self):
        return self.rc != 0


class MobVer(object):

    def __init__(self, instanceId, dynClient):

        if dynClient is None:
            if "KUBERNETES_SERVICE_HOST" in os.environ:
                config.load_incluster_config()
                k8s_config = Configuration.get_default_copy()
                k8s_client = client.api_client.ApiClient(configuration=k8s_config)
                self.dynClient = DynamicClient(k8s_client)
            else:
                k8s_client = config.new_client_from_config()
                self.dynClient = DynamicClient(k8s_client)
        else:
            self.dynClient = dynClient

        self.instanceId = (
            instanceId if instanceId is not None else os.getenv("INSTANCE_ID")
        )
        self.uploadFile = os.getenv("UPLOAD_FILE")
        self.buildNum = os.getenv("BUILD_NUM")
        self.artKey = os.getenv("ARTIFACTORY_TOKEN")
        self.artDir = os.getenv("ARTIFACTORY_UPLOAD_DIR")
        self.output_filename = (
            f"{self.instanceId}-{self.buildNum}-mobile-is-versions.json"
        )

    def run_cmd(self, cmdArray, timeout=630):
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
                return RunCmdResult(127, "TimeoutExpired", str(e))

    def get_maxinst_and_mobileapi_pods(self):

        podName = []
        # retrieving maxinst pod in manage namespace
        try:
            pods = self.dynClient.resources.get(api_version="v1", kind="Pod")
            podList = pods.get(
                namespace=f"mas-{self.instanceId}-manage",
                label_selector="mas.ibm.com/appType=maxinstudb",
            )

            if podList is None or podList.items is None or len(podList.items) == 0:
                print("Pod with label mas.ibm.com/appType=maxinstudb was not found")
            else:
                podName.append(podList.items[0].metadata.name)

        except Exception as e:
            print(f"Unable to download mobile packages from maxinst pod: {e}")
            sys.exit(1)

        # retrieving mobile api pod in core namespace
        try:
            pods = self.dynClient.resources.get(api_version="v1", kind="Pod")
            podList = pods.get(
                namespace=f"mas-{self.instanceId}-core",
                label_selector=f"app={self.instanceId}-mobileapi",
            )

            if podList is None or podList.items is None or len(podList.items) == 0:
                print(f"Pod with label app={self.instanceId}-mobileapi was not found")
            else:
                podName.append(podList.items[0].metadata.name)

        except Exception as e:
            print(
                f"Unable to download mobileapi navigator package from mobileapi pod: {e}"
            )
            sys.exit(1)

        return podName

    def download_mobile_packages(self, podName):
        # list all graphite zip packages in maxinst pod
        ocExecCommand = [
            "oc",
            "exec",
            "-n",
            f"mas-{self.instanceId}-manage",
            podName,
            "--",
            "ls",
            "/opt/IBM/SMP/maximo/tools/maximo/en/graphite/apps",
        ]
        result = self.run_cmd(ocExecCommand)
        ls_result = result.out.decode("utf-8")
        apps_list = ls_result.split("\n")
        # removes last empty value from the list
        apps_list.pop()

        # Download all packages that were found
        for a in apps_list:
            ocExecCommand = [
                "oc",
                "cp",
                "-n",
                f"mas-{self.instanceId}-manage",
                f"{podName}:/opt/IBM/SMP/maximo/tools/maximo/en/graphite/apps/{a}",
                f"./{a}",
                "--retries=10",
            ]
            self.run_cmd(ocExecCommand)

    def download_navigator_package(self, podName):

        ocExecCommand = [
            "oc",
            "exec",
            "-n",
            f"mas-{self.instanceId}-core",
            podName,
            "--",
            "ls",
            "/etc/mobile/packages",
        ]
        result = self.run_cmd(ocExecCommand)
        ls_result = result.out.decode("utf-8")
        apps_list = ls_result.split("\n")
        # removes last empty value from the list
        apps_list.pop()

        for a in apps_list:
            ocExecCommand = [
                "oc",
                "cp",
                "-n",
                f"mas-{self.instanceId}-core",
                f"{podName}:/etc/mobile/packages/{a}",
                f"./{a}",
                "--retries=10",
            ]
            self.run_cmd(ocExecCommand)

    def extract_build_json_from_zip_files(self, source_zip_files_path):
        # Extracting build.json from each file and deleting zip
        pathlist = Path(source_zip_files_path).glob("*.zip")

        for app_zip_file in pathlist:

            zip_file_path = f"{source_zip_files_path}/{str(app_zip_file)}"
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                try:
                    zip_ref.extract("build.json", ".")
                except KeyError:
                    print(f"There is no build.json file in {app_zip_file}")
                    with open("build.json", "w", encoding="utf-8") as dummy_file:
                        warn_json = {
                            "WARN": {
                                str(
                                    app_zip_file
                                ): "File does not contain version information"
                            }
                        }
                        json.dump(warn_json, dummy_file, indent=4)
                zip_ref.close()

            zip_file_prefix = zip_file_path.split(".zip")
            os.rename(
                f"{source_zip_files_path}/build.json", f"{zip_file_prefix[0]}.json"
            )
            os.remove(zip_file_path)

    def extract_build_info_from_json_files(self, source_json_files_path):
        # dictionary that will contain all graphite versions for all found zips
        graphite_json = {}

        pathlist = Path(source_json_files_path).glob("*.json")
        for path in pathlist:
            path_in_str = str(path)

            with open(path_in_str, "r", encoding="utf-8") as openfile:
                json_object = json.load(openfile)

            if json_object.get("WARN") is not None:
                graphite_json.update({"WARN": json_object.get("WARN")})
            else:
                graphite_json.update(
                    {
                        json_object.get("applicationId"): {
                            "version": json_object.get("version"),
                            "applicationId": json_object.get("applicationId"),
                            "applicationTitle": json_object.get("applicationTitle"),
                            "mobileVersion": json_object.get("mobileVersion"),
                            "buildToolsVersion": json_object.get("buildToolsVersion"),
                            "appProcessorVersion": json_object.get(
                                "appProcessorVersion"
                            ),
                        }
                    }
                )

                # removing empty mobile version or non mobile apps
                if json_object.get("mobileVersion") is None:
                    del graphite_json[json_object.get("applicationId")]["mobileVersion"]

                # removing empty title from apps with no title
                if json_object.get("applicationTitle") is None:
                    del graphite_json[json_object.get("applicationId")][
                        "applicationTitle"
                    ]

            # delete build.json file
            os.remove(path_in_str)

        # ordering json file
        graphite_json_sorted = OrderedDict(sorted(graphite_json.items()))

        return graphite_json_sorted

    def get_graphite_versions(self):
        # This list will contains all files found in the maxinst pod
        pods_list = self.get_maxinst_and_mobileapi_pods()

        maxinst_pod = pods_list[0]
        mobileapi_pod = pods_list[1]

        self.download_mobile_packages(podName=maxinst_pod)

        self.download_navigator_package(podName=mobileapi_pod)

        self.extract_build_json_from_zip_files(source_zip_files_path=".")

        graphite_ver = self.extract_build_info_from_json_files(
            source_json_files_path="."
        )

        return graphite_ver

    def get_mobile_and_is_image_tags(self):

        images_json = {}

        # getting mobileapi image version from entitymgr-suite pod
        try:
            pods = self.dynClient.resources.get(api_version="v1", kind="Pod")
            podList = pods.get(
                namespace=f"mas-{self.instanceId}-core",
                label_selector=f"app={self.instanceId}-entitymgr-suite",
            )

            if podList is None or podList.items is None or len(podList.items) == 0:
                pass
            else:
                podName = podList.items[0].metadata.name

                # list navigator zip packages in mobileapi pod
                ocExecCommand = [
                    "oc",
                    "exec",
                    "-n",
                    f"mas-{self.instanceId}-core",
                    podName,
                    "--",
                    "cat",
                    "/opt/ansible/roles/suite/vars/images.yml",
                ]
                result = self.run_cmd(ocExecCommand)
                cat_result = result.out.decode("utf-8")
                images = yaml.safe_load(cat_result)
                images_json.update({"mobileapi": images["defaultTags"]["mobileapi"]})
        except Exception as e:
            print(f"Unable to catch images file from core's entitymgr-suite pod: {e}")
            sys.exit(1)

        # getting industry solutions images version from entitymgr-ws
        try:
            pods = self.dynClient.resources.get(api_version="v1", kind="Pod")
            podList = pods.get(
                namespace=f"mas-{self.instanceId}-manage",
                label_selector="mas.ibm.com/appType=entitymgr-ws-operator",
            )

            if podList is None or podList.items is None or len(podList.items) == 0:
                pass
            else:
                podName = podList.items[0].metadata.name

                # list navigator zip packages in mobileapi pod
                ocExecCommand = [
                    "oc",
                    "exec",
                    "-n",
                    f"mas-{self.instanceId}-manage",
                    podName,
                    "--",
                    "cat",
                    "/opt/ansible/roles/workspace/vars/images.yml",
                ]
                result = self.run_cmd(ocExecCommand)
                cat_result = result.out.decode("utf-8")
                images = yaml.safe_load(cat_result)
                images_json.update(images["defaultTags"])

        except Exception as e:
            print(f"Unable to catch images file from Manage's entitymgr-ws pod: {e}")
            sys.exit(1)

        images_json_sorted = OrderedDict(sorted(images_json.items()))

        return images_json_sorted

    def artifactory_upload(self):

        url = self.artDir + "/fvt-mobile/" + self.output_filename
        bearer = f"Bearer {self.artKey}"
        headers = {"content-type": "application/json", "Authorization": bearer}

        with open(self.output_filename, "rb") as f:
            r = requests.put(url, data=f, headers=headers, timeout=10)

        if r.status_code != 201:
            print("Upload failed.")
        else:
            print("Upload successful")
            print("Download URL:", r.json()["downloadUri"])


if __name__ == "__main__":

    MobVersion = MobVer(instanceId=None, dynClient=None)

    if os.path.isfile(MobVersion.output_filename):
        print("Found an existing output file. Deleting...")
        os.remove(MobVersion.output_filename)

    print("Retrieving Graphite versions for Manage apps")
    graphite_versions = MobVersion.get_graphite_versions()

    print("Retrieving image versions for Manage IS and Add-ons ")
    img_versions = MobVersion.get_mobile_and_is_image_tags()

    print("Generating output file with versions")
    mobile_is_versions = {}
    mobile_is_versions.update(
        {"graphite_versions": graphite_versions, "images_versions": img_versions}
    )

    with open(MobVersion.output_filename, "w", encoding="utf-8") as outfile:
        json.dump(mobile_is_versions, outfile, indent=4)

    print("Printing gererated file:")
    print("************************************************")
    with open(MobVersion.output_filename, "r", encoding="utf-8") as readfile:
        print(readfile.read())
    print("************************************************")

    # Upload logs conditionally based o env var
    if MobVersion.uploadFile:
        print("Uploading file to artifactory")
        MobVersion.artifactory_upload()

    print("Done")
