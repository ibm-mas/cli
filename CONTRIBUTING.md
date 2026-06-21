Contributing to MAS CLI
===============================================================================

Contents
-------------------------------------------------------------------------------
1. [Detect Secrets](#detect-secrets)
2. [Pre-Commit Hooks](#pre-commit-hooks)
3. [Testing Significant Changes](#)
4. [Building the Tekton definitions](#building-the-tekton-definitions)
5. [Building the Documentation](#building-the-documentation)
6. [Using the Docker Image](#using-the-docker-image)
7. [Working Across Repositories](#working-across-repositories)
8. [Pull Requests](#pull-requests)


Detect Secrets
-------------------------------------------------------------------------------
- Update the `.secrets.baseline` file using: `detect-secrets scan --update .secrets.baseline`
- Audit secrets using: `detect-secrets audit .secrets.baseline`


Pre-Commit Hooks
-------------------------------------------------------------------------------
The follow pre-commit hooks are enabled:

- **black**
- **flake8**
- **detect-secrets**

These hooks are also executed in a GitHub action in the [pre-commit workflow](.github/workflows/pre-commit.yml).

```bash
python -m pip install pre-commit --upgrade
pre-commit install

# Manually run the pre-commit hooks against changed files
pre-commit run

# Manually run the pre-commit hooks against all files
pre-commit run -a
```


Testing Significant Changes
-------------------------------------------------------------------------------
Manual testing for significant changes is sometimes appropriate:

If you don't already have a cluster, provision an appropriately sized OpenShift cluster:

```bash
podman run -e IBMCLOUD_APIKEY -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:mybranch \
  mas provision-roks -r mas-development -c clitesting -v 4.20_openshift  --worker-count 3 --worker-flavor b3c.8x32 --worker-zone lon02 --no-confirm
```

```bash
# Build the tekton definitions that will be installed
make tekton VERSION=mybranch

# If you are not making any changes that impact what happens inside the containers
#in the pipeline then you can use the master branch of the CLI
make tekton VERSION=master

# Run the install/update/upgrade/uninstall
mas-cli install
mas-cli update
mas-cli upgrade
mas-cli uninstall
```


Building the Tekton definitions
-------------------------------------------------------------------------------
The tekton defintions can be built locally using `build/bin/build-tekton.sh`:

```bash
# Build, and install the MAS Pipeline & Task definitions
DEV_MODE=true VERSION=100.0.0-pre.local build/bin/build-tekton.sh && oc apply -f tekton/target/ibm-mas-tekton-fvt.yaml

# Build and validate the MAS Pipeline & Task definitions
DEV_MODE=true VERSION=100.0.0-pre.local build/bin/build-tekton.sh && pytest tekton/test_schema.py -v
```

Note that we use the version `100.0.0-pre.local` as this is the version that is defaulted into the CLI Python code before it's modifyed during the build.

Once built, use `tekton/test-install.sh` to apply the definitions to a cluster one-by-one.  This makes it much easier to determine where any problems in the built definition lay versus applying the combined `ibm-mas-tekton.yaml` file directly (although both achieves the same end result):

```bash
tekton/test-install.sh
```


Building the Documentation
-------------------------------------------------------------------------------
```bash
python3 -m venv .venv-docs
source .venv-docs/bin/activate

# We need to install the python-devops and cli packages because we generate documentation from their code using mkdocs directives
python -m pip install -e ../python-devops
python -m pip install -e .

# Install mkdocs and the various plugins that we use, including our custom plugins
python -m pip install -q mkdocs mkdocs-carbon mkdocs-glightbox mkdocs-redirects
python -m pip install -e mkdocs_plugins

mkdocs serve --livereload
```


Using the docker image
-------------------------------------------------------------------------------
This is a great way to test in a clean environment (e.g. to ensure the myriad of environment variables that you no doubt have set up are not impacting your test scenarios).  After you commit your changes to the repository a pre-release container image will be built, which contains your in-development version of the collection:

```bash
podman run -ti --rm --pull always quay.io/ibmmas/cli:mybranch

# Login to a cluster
oc login --token=xxxx --server=https://myocpserver

# Set up environment variables
export STUFF

# Run a role
ansible localhost -m include_role -a name=ibm.mas_devops.ocp_verify

# Run a playbook
ansible-playbook ibm.mas_devops.mas_install_core

# Run a cli command
mas install
```


Working Across Repositories
-------------------------------------------------------------------------------
The **cli** build uses the output of the **ansible-devops** and **python-devops** builds, when you are making changes across all three repositories you should use the same branch name in all three, tihs will ensure that the **cli** build picks up the correct versions of the other two builds.

For example, if you are working on a new feature here in a branch called `rbacfix`, and you need to deliver changes in both **ansible-devops** and **python-devops** as well, ensure that you name those branches `rbacfix` too, and they the builds in those branches have completed before you build the **cli** branch. This will ensure that the **cli** build picks up the correct versions of the other two builds.


Pull Requests
-------------------------------------------------------------------------------
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
