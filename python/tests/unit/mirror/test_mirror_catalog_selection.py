# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Unit tests for catalog-aware package selection in MirrorApp."""

from unittest.mock import patch

from mas.cli.mirror.app import MirrorApp, MirrorResult


def _make_mock_catalog_9_1():
    """Create mock catalog data with MAS 9.1.x content including Assist."""
    return {
        "catalog_digest": "sha256:12345",
        "sls_version": "3.10.0",
        "tsm_version": "1.5.0",
        "amlen_extras_version": "1.0.0",
        "aiservice_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "aiservice_tenant_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "odh_version": "2.32.0",
        "minio_version": "RELEASE.2025-06-13T11-33-47Z",
        "dd_version": "1.0.0",
        "db2u_version": "11.5.9.0",
        "mongo_extras_version_default": "6.0.0",
        "mas_core_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_assist_version": {"9.1.x": "9.1.0"},
        "couchdb_version": "1.0.13",
        "mas_iot_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_facilities_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_manage_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_monitor_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_predict_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_optimizer_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_visualinspection_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "common_svcs_version": "4.13.0",
        "ibm_zen_version": "6.2.0",
        "cp4d_platform_version": "5.2.0",
        "swhub_version": "5.10.0",
        "ibm_licensing_version": "4.2.17",
        "ccs_build": "11.0.0",
        "postgress_version": "5.16.0",
        "pg_operator_version": "1.21.1",
        "datarefinery_version": "11.0.0",
        "elasticsearch_version": "1.1.2667",
        "opensearch_version": "1.1.2494",
        "wsl_version": "11.0.0",
        "wsl_runtimes_version": "11.0.0",
        "wml_version": "11.0.0",
        "redis_version": "1.3.1",
        "spark_version": "11.0.0",
        "cognos_version": "28.0.0",
        "cpd_product_version_default": "5.1.0",
    }


def _make_mock_catalog_9_2():
    """Create mock catalog data with MAS 9.2.x content where Assist is removed."""
    return {
        "catalog_digest": "sha256:67890",
        "sls_version": "3.10.0",
        "tsm_version": "1.5.0",
        "amlen_extras_version": "1.0.0",
        "aiservice_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "aiservice_tenant_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "odh_version": "2.32.0",
        "minio_version": "RELEASE.2025-06-13T11-33-47Z",
        "dd_version": "1.0.0",
        "db2u_version": "11.5.9.0",
        "mongo_extras_version_default": "6.0.0",
        "mas_core_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_assist_version": {"9.1.x": "9.1.0"},  # Assist only in 9.1.x, not in 9.2.x
        "couchdb_version": "1.0.13",
        "mas_iot_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_facilities_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_manage_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_monitor_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_predict_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_optimizer_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "mas_visualinspection_version": {"9.1.x": "9.1.0", "9.2.x": "9.2.0"},
        "common_svcs_version": "4.13.0",
        "ibm_zen_version": "6.2.0",
        "cp4d_platform_version": "5.2.0",
        "swhub_version": "5.10.0",
        "ibm_licensing_version": "4.2.17",
        "ccs_build": "11.0.0",
        "postgress_version": "5.16.0",
        "pg_operator_version": "1.21.1",
        "datarefinery_version": "11.0.0",
        "elasticsearch_version": "1.1.2667",
        "opensearch_version": "1.1.2494",
        "wsl_version": "11.0.0",
        "wsl_runtimes_version": "11.0.0",
        "wml_version": "11.0.0",
        "redis_version": "1.3.1",
        "spark_version": "11.0.0",
        "cognos_version": "28.0.0",
        "cpd_product_version_default": "5.1.0",
    }


@patch("mas.cli.mirror.app.shutil.which", return_value="/usr/local/bin/oc-mirror")
@patch("mas.cli.mirror.app.generateAuthFile", return_value="/tmp/auth.json")
@patch("mas.cli.mirror.app.mirrorCatalog", return_value=MirrorResult(images=1, mirrored=1, name="catalog"))
@patch("mas.cli.mirror.app.mirrorPackage", return_value=MirrorResult(images=5, mirrored=5, name="package"))
@patch("mas.cli.mirror.app.getCatalog")
def test_mirror_all_includes_assist_on_9_1(mock_get_catalog, mock_mirror_package, mock_mirror_catalog, mock_gen_auth, mock_which):
    """Test that --all mirrors Assist and CouchDB when release is 9.1.x.

    GIVEN a catalog containing MAS 9.1.x with Assist support
    WHEN MirrorApp.mirror is invoked with --all and --release 9.1.x
    THEN mirrorPackage is called for both ibm-mas-assist and ibm-couchdb with flag=True.
    """
    mock_get_catalog.return_value = _make_mock_catalog_9_1()
    app = MirrorApp()
    argv = [
        "--catalog",
        "v9-260129-amd64",
        "--release",
        "9.1.x",
        "--mode",
        "m2m",
        "--dir",
        "/tmp/mirror",
        "--target-registry",
        "registry.example.com/mas",
        "--all",
    ]

    app.mirror(argv=argv)

    mirrored_packages = [call.kwargs.get("package") for call in mock_mirror_package.call_args_list if call.kwargs.get("flag") is True]

    assert "ibm-mas-assist" in mirrored_packages
    assert "ibm-couchdb" in mirrored_packages
    assert "ibm-mas" in mirrored_packages


@patch("mas.cli.mirror.app.shutil.which", return_value="/usr/local/bin/oc-mirror")
@patch("mas.cli.mirror.app.generateAuthFile", return_value="/tmp/auth.json")
@patch("mas.cli.mirror.app.mirrorCatalog", return_value=MirrorResult(images=1, mirrored=1, name="catalog"))
@patch("mas.cli.mirror.app.mirrorPackage", return_value=MirrorResult(images=5, mirrored=5, name="package"))
@patch("mas.cli.mirror.app.getCatalog")
def test_mirror_all_excludes_assist_on_9_2(mock_get_catalog, mock_mirror_package, mock_mirror_catalog, mock_gen_auth, mock_which, capsys):
    """Test that --all excludes Assist and CouchDB when release is 9.2.x.

    GIVEN a catalog where Assist is not supported for MAS 9.2.x
    WHEN MirrorApp.mirror is invoked with --all and --release 9.2.x
    THEN mirrorPackage is NOT called with flag=True for ibm-mas-assist or ibm-couchdb
    AND the "No content to mirror for MAS release 9.2.x" message is printed for both packages.
    """
    mock_get_catalog.return_value = _make_mock_catalog_9_2()
    app = MirrorApp()
    argv = [
        "--catalog",
        "v9-260129-amd64",
        "--release",
        "9.2.x",
        "--mode",
        "m2m",
        "--dir",
        "/tmp/mirror",
        "--target-registry",
        "registry.example.com/mas",
        "--all",
    ]

    app.mirror(argv=argv)

    mirrored_packages = [call.kwargs.get("package") for call in mock_mirror_package.call_args_list if call.kwargs.get("flag") is True]
    output = capsys.readouterr().out

    assert "ibm-mas-assist" not in mirrored_packages
    assert "ibm-couchdb" not in mirrored_packages
    assert "ibm-mas" in mirrored_packages
    assert "ibm-mas-assist (" in output and "No content to mirror for MAS release 9.2.x" in output
    assert "ibm-couchdb (" in output and "No content to mirror for MAS release 9.2.x" in output


@patch("mas.cli.mirror.app.shutil.which", return_value="/usr/local/bin/oc-mirror")
@patch("mas.cli.mirror.app.generateAuthFile", return_value="/tmp/auth.json")
@patch("mas.cli.mirror.app.mirrorCatalog", return_value=MirrorResult(images=1, mirrored=1, name="catalog"))
@patch("mas.cli.mirror.app.mirrorPackage", return_value=MirrorResult(images=5, mirrored=5, name="package"))
@patch("mas.cli.mirror.app.getCatalog")
def test_mirror_assist_flag_on_unsupported_release(mock_get_catalog, mock_mirror_package, mock_mirror_catalog, mock_gen_auth, mock_which, capsys):
    """Test that --assist flag does not mirror CouchDB when Assist is not in 9.2.x.

    GIVEN a catalog where Assist is removed in MAS 9.2.x
    WHEN MirrorApp.mirror is invoked with --assist and --release 9.2.x
    THEN mirrorPackage is NOT called with flag=True for ibm-couchdb or ibm-mas-assist
    AND the Assist entry is reached in the package loop and reports "No content to mirror for MAS release 9.2.x".
    """
    mock_get_catalog.return_value = _make_mock_catalog_9_2()
    app = MirrorApp()
    argv = [
        "--catalog",
        "v9-260129-amd64",
        "--release",
        "9.2.x",
        "--mode",
        "m2m",
        "--dir",
        "/tmp/mirror",
        "--target-registry",
        "registry.example.com/mas",
        "--assist",
    ]

    app.mirror(argv=argv)

    mirrored_packages = [call.kwargs.get("package") for call in mock_mirror_package.call_args_list if call.kwargs.get("flag") is True]
    output = capsys.readouterr().out

    assert "ibm-mas-assist" not in mirrored_packages
    assert "ibm-couchdb" not in mirrored_packages
    # Positive control: the Assist entry was reached and skipped via the release check, not silently dropped
    assert "ibm-mas-assist (" in output and "No content to mirror for MAS release 9.2.x" in output


@patch("mas.cli.mirror.app.shutil.which", return_value="/usr/local/bin/oc-mirror")
@patch("mas.cli.mirror.app.generateAuthFile", return_value="/tmp/auth.json")
@patch("mas.cli.mirror.app.mirrorCatalog", return_value=MirrorResult(images=1, mirrored=1, name="catalog"))
@patch("mas.cli.mirror.app.mirrorPackage", return_value=MirrorResult(images=5, mirrored=5, name="package"))
@patch("mas.cli.mirror.app.getCatalog")
def test_mirror_missing_catalog_key_handled_safely(mock_get_catalog, mock_mirror_package, mock_mirror_catalog, mock_gen_auth, mock_which):
    """Test that missing catalog keys do not cause KeyError when --all is used.

    GIVEN a sparse catalog missing multiple optional dependency keys
    WHEN MirrorApp.mirror is invoked with --all
    THEN mirroring completes without raising KeyError.
    """
    # Sparse catalog missing optional keys like amlen_extras_version, dd_version, couchdb_version
    sparse_catalog = {
        "catalog_digest": "sha256:11111",
        "sls_version": "3.10.0",
        "tsm_version": "1.5.0",
        "mas_core_version": {"9.2.x": "9.2.0"},
        "cpd_product_version_default": "5.1.0",
    }
    mock_get_catalog.return_value = sparse_catalog
    app = MirrorApp()
    argv = [
        "--catalog",
        "v9-260129-amd64",
        "--release",
        "9.2.x",
        "--mode",
        "m2m",
        "--dir",
        "/tmp/mirror",
        "--target-registry",
        "registry.example.com/mas",
        "--all",
    ]

    # Should not raise KeyError
    app.mirror(argv=argv)

    mirrored_packages = [call.kwargs.get("package") for call in mock_mirror_package.call_args_list if call.kwargs.get("flag") is True]

    assert "ibm-mas" in mirrored_packages
    assert "ibm-sls" in mirrored_packages
