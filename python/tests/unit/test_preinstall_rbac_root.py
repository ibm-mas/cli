# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for locating the pre-install RBAC manifests (uvx, uv tool and container image)."""

import ast
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest

from mas.cli import rbac_utils
from mas.cli.cli import BaseApp
from mas.cli.rbac_utils import PREINSTALL_RBAC_DIR_ENV, getPreinstallRBACRootDir, getPreinstallRBACSource

SRC_DIR = Path(__file__).resolve().parents[2] / "src" / "mas" / "cli"
REPO_DIR = Path(__file__).resolve().parents[3]
PYPROJECT_PATH = REPO_DIR / "pyproject.toml"
BUNDLE_SCRIPT = REPO_DIR / "build" / "bin" / "bundle-preinstall-rbac.sh"


def makeRBACRoot(root: Path, catalog: str = "maximo-operator-catalog") -> Path:
    """Create a minimal pre-install RBAC tree below root.

    Args:
        root (Path): Directory to populate.
        catalog (str, optional): Catalog folder to create. Defaults to "maximo-operator-catalog".

    Returns:
        Path: The populated root directory.
    """
    rbacDir = root / catalog / "operators" / "ibm-mas" / "rbac" / "9.2"
    rbacDir.mkdir(parents=True)
    (rbacDir / "cluster-role-core-coreapi.yml").write_text("kind: ClusterRole\n")
    return root


@pytest.fixture
def isolatedEnvironment(tmp_path, monkeypatch):
    """Point every candidate location at an empty directory and clear the env override."""
    monkeypatch.delenv(PREINSTALL_RBAC_DIR_ENV, raising=False)
    monkeypatch.setattr(rbac_utils, "PACKAGED_PREINSTALL_RBAC_DIR", str(tmp_path / "packaged"))
    monkeypatch.setattr(rbac_utils, "LEGACY_PREINSTALL_RBAC_DIR", str(tmp_path / "legacy"))
    return tmp_path


def test_env_override_takes_priority(isolatedEnvironment, monkeypatch):
    """Test that the environment override wins over every other location.

    GIVEN manifests in the env override, the legacy image path and the package
    WHEN getPreinstallRBACRootDir() is called
    THEN the env override directory is returned.
    """
    override = makeRBACRoot(isolatedEnvironment / "override")
    makeRBACRoot(isolatedEnvironment / "legacy")
    makeRBACRoot(isolatedEnvironment / "packaged")
    monkeypatch.setenv(PREINSTALL_RBAC_DIR_ENV, str(override))

    assert getPreinstallRBACRootDir() == str(override)


def test_env_override_that_is_not_a_directory_is_fatal(isolatedEnvironment, monkeypatch):
    """Test that an invalid env override fails instead of falling back.

    GIVEN an env override pointing at a path that does not exist and valid manifests in the package
    WHEN getPreinstallRBACRootDir() is called
    THEN FileNotFoundError is raised naming the env var.
    """
    makeRBACRoot(isolatedEnvironment / "packaged")
    monkeypatch.setenv(PREINSTALL_RBAC_DIR_ENV, str(isolatedEnvironment / "missing"))

    with pytest.raises(FileNotFoundError, match=PREINSTALL_RBAC_DIR_ENV):
        getPreinstallRBACRootDir()


def test_legacy_image_location_preferred_over_package(isolatedEnvironment):
    """Test that the container image behaviour is unchanged.

    GIVEN manifests in both the legacy image path and the package
    WHEN getPreinstallRBACRootDir() is called
    THEN the legacy image path is returned.
    """
    legacy = makeRBACRoot(isolatedEnvironment / "legacy")
    makeRBACRoot(isolatedEnvironment / "packaged")

    assert getPreinstallRBACRootDir() == str(legacy)


def test_packaged_manifests_are_used_when_no_image_path(isolatedEnvironment):
    """Test that a uvx install uses the manifests shipped in the package.

    GIVEN manifests only inside the mas.cli package
    WHEN getPreinstallRBACRootDir() is called
    THEN the packaged directory is returned.
    """
    packaged = makeRBACRoot(isolatedEnvironment / "packaged")

    assert getPreinstallRBACRootDir() == str(packaged)


def test_openshift_platform_only_tree_is_recognised(isolatedEnvironment):
    """Test that a tree with only openshift-platform operators is accepted.

    GIVEN a packaged tree that only has openshift-platform operators
    WHEN getPreinstallRBACRootDir() is called
    THEN the packaged directory is returned.
    """
    packaged = makeRBACRoot(isolatedEnvironment / "packaged", catalog="openshift-platform")

    assert getPreinstallRBACRootDir() == str(packaged)


def test_existing_directory_is_accepted_without_inspecting_its_contents(isolatedEnvironment):
    """Test that which manifests apply is left to python-devops.

    GIVEN an existing legacy directory with no recognisable layout and valid manifests in the package
    WHEN getPreinstallRBACRootDir() is called
    THEN the legacy directory is returned, exactly as it was before uvx support.
    """
    legacy = isolatedEnvironment / "legacy"
    legacy.mkdir()
    makeRBACRoot(isolatedEnvironment / "packaged")

    assert getPreinstallRBACRootDir() == str(legacy)


def test_no_manifests_anywhere_is_fatal(isolatedEnvironment):
    """Test that missing manifests fail loudly instead of silently applying nothing.

    GIVEN no candidate directory exists
    WHEN getPreinstallRBACRootDir() is called
    THEN FileNotFoundError is raised with guidance for the user.
    """
    with pytest.raises(FileNotFoundError, match="Could not find the pre-install RBAC manifests"):
        getPreinstallRBACRootDir()


def test_base_app_reports_missing_manifests_as_fatal_error(isolatedEnvironment):
    """Test that BaseApp turns a missing manifest tree into a fatal CLI error.

    GIVEN no manifests anywhere
    WHEN BaseApp.getPreinstallRBACRootDir() is called
    THEN the app exits with status 1.
    """
    app = BaseApp.__new__(BaseApp)

    with pytest.raises(SystemExit) as exitInfo:
        app.getPreinstallRBACRootDir()

    assert exitInfo.value.code == 1


def test_base_app_returns_resolved_root(isolatedEnvironment):
    """Test that BaseApp returns the resolved manifest root.

    GIVEN manifests inside the package
    WHEN BaseApp.getPreinstallRBACRootDir() is called
    THEN the packaged directory is returned.
    """
    packaged = makeRBACRoot(isolatedEnvironment / "packaged")
    app = BaseApp.__new__(BaseApp)

    assert app.getPreinstallRBACRootDir() == str(packaged)


def test_every_apply_call_passes_rbac_root_dir():
    """Test that no command falls back to the hardcoded container path.

    GIVEN the mas.cli source tree
    WHEN every applyPreInstallMASRBAC(...) call is inspected
    THEN each one passes rbacRootDir explicitly.
    """
    calls = []
    for sourceFile in SRC_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(sourceFile.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "applyPreInstallMASRBAC":
                calls.append((sourceFile.name, {keyword.arg for keyword in node.keywords}))

    assert len(calls) == 4
    for fileName, keywords in calls:
        assert "rbacRootDir" in keywords, f"{fileName} calls applyPreInstallMASRBAC without rbacRootDir"


def test_preinstall_rbac_tree_is_declared_as_package_data():
    """Test that pyproject.toml ships the bundled pre-install RBAC tree.

    GIVEN the root pyproject configuration
    WHEN the mas.cli package-data globs are inspected
    THEN both .yml and .yaml files below rbac/preinstall are included.
    """
    pyprojectData = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    packageData = pyprojectData["tool"]["setuptools"]["package-data"]["mas.cli"]

    assert "rbac/preinstall/**/*.yml" in packageData
    assert "rbac/preinstall/**/*.yaml" in packageData


def test_source_is_read_from_source_json(isolatedEnvironment):
    """Test that provenance is read from SOURCE.json beside the manifests.

    GIVEN a root containing a SOURCE.json
    WHEN getPreinstallRBACSource() is called
    THEN the recorded dictionary is returned.
    """
    root = makeRBACRoot(isolatedEnvironment / "packaged")
    recorded = {"repository": "https://github.com/ibm-mas/pre-install.git", "branch": "master", "commit": "abc123"}
    (root / "SOURCE.json").write_text(json.dumps(recorded))

    assert getPreinstallRBACSource(str(root)) == recorded


def test_source_is_none_when_not_recorded(isolatedEnvironment):
    """Test that a missing SOURCE.json is not an error.

    GIVEN a root without a SOURCE.json, such as the container image or a user override
    WHEN getPreinstallRBACSource() is called
    THEN None is returned.
    """
    root = makeRBACRoot(isolatedEnvironment / "packaged")

    assert getPreinstallRBACSource(str(root)) is None


def test_source_is_none_when_source_json_is_corrupt(isolatedEnvironment):
    """Test that a corrupt SOURCE.json never blocks the command.

    GIVEN a SOURCE.json that is not valid JSON
    WHEN getPreinstallRBACSource() is called
    THEN None is returned.
    """
    root = makeRBACRoot(isolatedEnvironment / "packaged")
    (root / "SOURCE.json").write_text("{not json")

    assert getPreinstallRBACSource(str(root)) is None


def test_resolver_logs_provenance(isolatedEnvironment, caplog):
    """Test that the resolved location and commit are written to the log.

    GIVEN packaged manifests with a SOURCE.json
    WHEN getPreinstallRBACRootDir() is called
    THEN the log names the directory and the pre-install commit.
    """
    root = makeRBACRoot(isolatedEnvironment / "packaged")
    (root / "SOURCE.json").write_text(json.dumps({"branch": "master", "commit": "deadbeef"}))

    with caplog.at_level(logging.INFO, logger="mas.cli.rbac_utils"):
        getPreinstallRBACRootDir()

    assert str(root) in caplog.text
    assert "deadbeef" in caplog.text


def test_pyproject_ships_source_json():
    """Test that pyproject.toml ships the provenance file.

    GIVEN the root pyproject configuration
    WHEN the mas.cli package-data globs are inspected
    THEN rbac/preinstall/SOURCE.json is included.
    """
    pyprojectData = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    assert "rbac/preinstall/SOURCE.json" in pyprojectData["tool"]["setuptools"]["package-data"]["mas.cli"]


@pytest.fixture
def bundledWorkspace(tmp_path):
    """Run the bundle script against a local pre-install archive in a throwaway workspace.

    Returns:
        Path: The workspace root, with python/src/mas/cli/rbac/preinstall populated.
    """
    source = tmp_path / "src" / "pre-install" / "catalogs" / "maximo-operator-catalog" / "operators" / "ibm-mas" / "rbac" / "9.2"
    source.mkdir(parents=True)
    (source / "cluster-role-core-coreapi.yml").write_text("kind: ClusterRole\n")
    (tmp_path / "src" / "pre-install" / ".git").mkdir()

    workspace = tmp_path / "ws"
    (workspace / "image" / "cli" / "install").mkdir(parents=True)
    with tarfile.open(workspace / "image" / "cli" / "install" / "pre-install.tar.gz", "w:gz") as archive:
        archive.add(tmp_path / "src" / "pre-install", arcname="pre-install")

    result = subprocess.run(
        ["bash", str(BUNDLE_SCRIPT)],
        env={"GITHUB_WORKSPACE": str(workspace), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return workspace


def test_bundle_script_writes_source_json(bundledWorkspace):
    """Test that the bundle script records where the manifests came from.

    GIVEN a bundle built from a local archive
    WHEN SOURCE.json is read
    THEN it names the repository, a branch, a commit field and the manifest count.
    """
    recorded = json.loads((bundledWorkspace / "python/src/mas/cli/rbac/preinstall/SOURCE.json").read_text())

    assert recorded["repository"] == "https://github.com/ibm-mas/pre-install.git"
    assert recorded["branch"]
    assert "commit" in recorded
    assert recorded["manifestCount"] == 1


def test_bundle_script_marks_local_archive_as_commit_unknown(bundledWorkspace):
    """Test that an archive build is honest about not knowing the commit.

    GIVEN a bundle built from a local archive that has no git metadata
    WHEN SOURCE.json is read
    THEN the commit is 'local-archive' rather than a made-up hash.
    """
    recorded = json.loads((bundledWorkspace / "python/src/mas/cli/rbac/preinstall/SOURCE.json").read_text())

    assert recorded["commit"] == "local-archive"


@pytest.fixture(scope="module")
def builtPackages(tmp_path_factory):
    """Build a real wheel and sdist from a throwaway copy of the project that has been through the bundle script.

    Returns:
        tuple[Path, Path]: The built wheel and sdist.
    """
    workspace = tmp_path_factory.mktemp("package-build")
    shutil.copy(PYPROJECT_PATH, workspace / "pyproject.toml")
    (workspace / "python").mkdir()
    shutil.copy(REPO_DIR / "python" / "README.md", workspace / "python" / "README.md")
    shutil.copytree(SRC_DIR.parents[1], workspace / "python" / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    source = workspace / "archive" / "pre-install" / "catalogs" / "maximo-operator-catalog" / "operators" / "ibm-mas" / "rbac" / "9.2"
    source.mkdir(parents=True)
    (source / "cluster-role-core-coreapi.yml").write_text("kind: ClusterRole\n")
    (workspace / "archive" / "pre-install" / "openshift-platform" / "operators" / "ibm-mas-op" / "rbac" / "9.2").mkdir(parents=True)
    (workspace / "archive" / "pre-install" / "openshift-platform" / "operators" / "ibm-mas-op" / "rbac" / "9.2" / "cluster-role-op.yaml").write_text(
        "kind: ClusterRole\n"
    )
    (workspace / "image" / "cli" / "install").mkdir(parents=True)
    with tarfile.open(workspace / "image" / "cli" / "install" / "pre-install.tar.gz", "w:gz") as archive:
        archive.add(workspace / "archive" / "pre-install", arcname="pre-install")

    bundled = subprocess.run(["bash", str(BUNDLE_SCRIPT)], env={**os.environ, "GITHUB_WORKSPACE": str(workspace)}, capture_output=True, text=True)
    assert bundled.returncode == 0, bundled.stdout + bundled.stderr

    built = subprocess.run([sys.executable, "-m", "build", "--outdir", str(workspace / "dist")], cwd=workspace, capture_output=True, text=True)
    assert built.returncode == 0, built.stdout + built.stderr
    return next((workspace / "dist").glob("*.whl")), next((workspace / "dist").glob("*.tar.gz"))


def test_built_wheel_contains_the_bundled_rbac(builtPackages):
    """Test that the published wheel ships the manifests that uvx needs.

    GIVEN a wheel built from a project that has been through the bundle script
    WHEN the wheel contents are listed
    THEN the .yml and .yaml manifests and SOURCE.json are inside mas/cli/rbac/preinstall.
    """
    wheel, _ = builtPackages
    names = zipfile.ZipFile(wheel).namelist()
    base = "mas/cli/rbac/preinstall"

    assert f"{base}/maximo-operator-catalog/operators/ibm-mas/rbac/9.2/cluster-role-core-coreapi.yml" in names
    assert f"{base}/openshift-platform/operators/ibm-mas-op/rbac/9.2/cluster-role-op.yaml" in names
    assert f"{base}/SOURCE.json" in names


def test_built_sdist_contains_the_bundled_rbac(builtPackages):
    """Test that the sdist, which the container image installs, also ships the manifests.

    GIVEN an sdist built from a project that has been through the bundle script
    WHEN the sdist contents are listed
    THEN the manifests and SOURCE.json are inside mas/cli/rbac/preinstall.
    """
    _, sdist = builtPackages
    names = tarfile.open(sdist).getnames()

    assert any(name.endswith("mas/cli/rbac/preinstall/maximo-operator-catalog/operators/ibm-mas/rbac/9.2/cluster-role-core-coreapi.yml") for name in names)
    assert any(name.endswith("mas/cli/rbac/preinstall/openshift-platform/operators/ibm-mas-op/rbac/9.2/cluster-role-op.yaml") for name in names)
    assert any(name.endswith("mas/cli/rbac/preinstall/SOURCE.json") for name in names)


def test_installed_wheel_resolves_its_own_bundled_rbac(builtPackages, tmp_path):
    """Test that an installed wheel finds its manifests with no container path and no override.

    GIVEN the built wheel unpacked the way uvx would install it
    WHEN mas.cli.rbac_utils.getPreinstallRBACRootDir() runs from the unpacked copy
    THEN it returns the rbac/preinstall directory inside that copy.
    """
    wheel, _ = builtPackages
    zipfile.ZipFile(wheel).extractall(tmp_path)

    result = subprocess.run(
        [sys.executable, "-c", "import mas.cli.rbac_utils as r; r.LEGACY_PREINSTALL_RBAC_DIR = '/nonexistent'; print(r.getPreinstallRBACRootDir())"],
        env={**os.environ, "PYTHONPATH": str(tmp_path), "MAS_PREINSTALL_RBAC_DIR": ""},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().splitlines()[-1] == str(tmp_path / "mas" / "cli" / "rbac" / "preinstall")
