# Contributing to MAS CLI

## Contents
1. Building the Tekton definitions
2. Building the container image locally
3. Using the docker image
4. Generate a Github SSH key
5. Building your local development environment
6. Pull Requests
7. Pulling MAS Ansible Devops into MAS Command Line Interface

## 1. Building the Tekton definitions
The tekton defintions can be built locally using `build/bin/build-tekton.sh`:

```bash
# Build, and install the MAS Pipeline & Task definitions
DEV_MODE=true VERSION=9.0.0-pre.majorup build/bin/build-tekton.sh && oc apply -f tekton/target/ibm-mas-tekton-fvt.yaml

# Build, and install the MAS Pipeline & Task definitions 1-by-1
DEV_MODE=true VERSION=7.8.0-pre.fvtsplit build/bin/build-tekton.sh && tekton/test.sh
```

Once built, use `tekton/test-install.sh` to apply the definitions to a cluster one-by-one.  This makes it much easier to determine where any problems in the built definition lay versus applying the combined `ibm-mas-tekton.yaml` file directly (although both achieves the same end result):

```bash
tekton/test-install.sh
```


## 2. Building the container image locally
```bash
# Build & install ansible collections, save them to image/cli/, build the docker container, then run the container
make
docker run -ti --rm quay.io/ibmmas/cli:local
```


## 3. Using the docker image
This is a great way to test in a clean environment (e.g. to ensure the myriad of environment variables that you no doubt have set up are not impacting your test scenarios).  After you commit your changes to the repository a pre-release container image will be built, which contains your in-development version of the collection:

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli:x.y.z-pre.mybranch
oc login --token=xxxx --server=https://myocpserver
export STUFF
ansible localhost -m include_role -a name=ibm.mas_devops.ocp_verify
ansible-playbook ibm.mas_devops.oneclick_core
mas install
```


## 4. Generate a Github SSH key
Follow this instructions to [generate a new SSH key and add it to your Github account to link with this repository](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent).

This will allow you authenticate to this repository and raise pull requests with your own changes and request review and merge approval for the code owners.


## 5. Building your local development environment
Here's how you could get started developing within a new working branch:

1. Clone MAS CLI repository locally.
2. Create your own branch.
3. Set the new branch as active working branch.

```
git clone git@github.com:ibm-mas/cli.git
git checkout -b name-your-branch
git checkout name-your-branch
```

## 6. Pull Requests
This repository uses a common build system to enable proper versioning. This build system is triggered when including specific tags at the beginning of your [commits](https://github.com/ibm-mas/cli/commits/master) and [pull requests](https://github.com/ibm-mas/cli/pulls) titles.

### Breaking Changes
`[major]` - This tag triggers a major pre-release version build out of your branch. Only use this tag when there are breaking or potential disruptive changes being introduced i.e existing ansible roles being removed.

**For example:** Latest MAS Command Line Interface version is at `1.0.0`. When submitting a `[major]` commit/pull request, it will build a pre-release version of MAS Command Line Interface as `2.0.0-pre.your-branch`. When merging it to master branch and releasing a new MAS CLI version, it will become `2.0.0` version.

### New Capability
`[minor]` - This tag triggers a minor pre-release version build out of your branch. Use this tag when adding new features to existing roles or creating new ansible roles.

**For example:** Latest MAS Command Line Interface version is at `1.0.0`. When submitting a `[minor]` commit/pull request. It will build a pre-release version of MAS Command Line Interface as `1.1.0-pre.your-branch`. When merging it to master branch and releasing a new MAS CLI version, it will become `1.1.0` version.

### Fixes
`[patch]` - This tag triggers a patch pre-release version build out of your branch. Use this tag when making small changes such as code/documentation fixes and non-disruptive changes.

**For example:** Latest MAS Command Line Interface version is at `1.0.0`. When submitting a `[patch]` commit/pull request, it will build a pre-release version of MAS Command Line Interface as `1.0.1-pre.your-branch`. When merging it to master branch and releasing a new MAS CLI version, it will become `1.0.1` version.

### Pre-requisites for new pull requests
For `major` and `minor` pull requests mainly, make sure you follow the standard approach new while developing new code:

- Ensure you have tested your changes and they do what is supposed to from an "end-to-end" perspective. Attaching screenshots of the end goal in your `pull request` are always welcome so everyone knows what to expect by the change, and that it does not break existing role functionalities around your change (basic regression test).
- Ensure that a MAS install test runs successfully from an `end-to-end` via cli (basic regression test). See more information about it in [MAS CLI documentation](https://github.com/ibm-mas/cli).
- If tekton tasks were modified please use the following test procedure from a linux environment that has ansible installed, the `oc` command and access to modified cli repo (your test branch):
  - Change directory to the cli/tekton directory
  - login to your cluster (oc login command)
  - Execute `ansible-playbook generate-tekton-tasks.yml`
  - Execute `ansible-playbook generate-tekton-pipelines.yml`
  - Execute `./test.sh`  This will try to create or recreate all the tekton resources in the default pipeline, make sure there are no errors.


Here's how you could get started with a new pull request from your branch:

1. Create your local commit.
2. Stage your code changes locally in order to prepare for remote push.
3. Push the staged changes from your local branch to the remote repository.

```
git commit -m "[minor] - my own changes to mas cli"
git add .
git push --set-upstream origin your-new-branch
```

When pushing a change with the proper tag in the commit, it will trigger the build system and your pull request will undergo with the proper build checks such as documentation build process and the actual MAS CLI package build. Once they pass all the validations, the PR can be flagged as ready to review.

As part of a successful MAS CLI build, a new pre-release docker image version will be pushed to [`Red Hat quay.io` image registry](https://quay.io/repository/ibmmas/cli?tab=tags)


## 7. Pulling MAS Ansible Devops into MAS Command Line Interface

MAS Command line Interface is powered by [Red Hat Openshift Tekton Pipelines](https://docs.openshift.com/container-platform/4.10/cicd/pipelines/understanding-openshift-pipelines.html#understanding-openshift-pipelines) and [MAS Ansible Devops collection](https://github.com/ibm-mas/ansible-devops).

The MAS Ansible Devops collection contains the ansible roles that are used to automate a particular task in the MAS CLI. For example, when you run `mas install` command via MAS CLI, when the installation begins, a tekton pipeline will be triggered in your cluster, and that will orchestrate the execution of a sequence of tasks, each of then invoking a particular MAS Ansible Devops role i.e `suite_install` role will perform the actual MAS installation.

When building a MAS CLI pre-release image version, the build system will embed the MAS Ansible Devops `tar.gz` following the rule:

- By default, MAS CLI will build its pre-release image using [the latest MAS Ansible Devops released version](https://github.com/ibm-mas/ansible-devops/releases).
- **To use a custom MAS Ansible Devops collection within MAS CLI:**  If you are developing a custom MAS Ansible Devops collection and you want to build a MAS CLI image that will make use of this ansible collection, from the `cli` root folder, you can run `make ansible-build` to build and place your MAS Ansible Devops `tar.gz` into [`cli/image/cli/install`](image/cli/install/), that's the folder that CLI uses to install the MAS Ansible Devops collection that will be used within the MAS CLI container during the image build process.
