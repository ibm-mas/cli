#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Tests for the supportedCatalogs data structure in install/catalogs.py.

Also validates the raw file format is compatible with the grep/sed pattern
used in image/cli/app-root/src/.bashrc to display supported catalog versions
at container startup.
"""

import importlib.util
import os
import re
import subprocess

import pytest

# Load the module directly by file path to avoid the full mas.cli package
# __init__ chain which requires optional runtime dependencies.
# Repo root is 4 levels up from python/tests/unit/install/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
_CATALOGS_PATH = os.path.join(_REPO_ROOT, "python", "src", "mas", "cli", "install", "catalogs.py")
_spec = importlib.util.spec_from_file_location("mas.cli.install.catalogs", _CATALOGS_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

supportedCatalogs = _mod.supportedCatalogs

SUPPORTED_ARCHES = ["amd64", "s390x", "ppc64le"]
CATALOG_VERSION_PATTERN = re.compile(r"^v\d+-\d{6}-(amd64|s390x|ppc64le)$")


class TestSupportedCatalogsStructure:
    """Test the overall structure of supportedCatalogs."""

    def test_supportedCatalogs_is_dict(self):
        """Test that supportedCatalogs is a dictionary.

        GIVEN the supportedCatalogs object
        WHEN its type is checked
        THEN it should be a dict.
        """
        assert isinstance(supportedCatalogs, dict)

    def test_supportedCatalogs_contains_all_architectures(self):
        """Test that all expected architectures are present.

        GIVEN the supportedCatalogs dict
        WHEN its keys are checked
        THEN it should contain amd64, s390x, and ppc64le.
        """
        for arch in SUPPORTED_ARCHES:
            assert arch in supportedCatalogs, f"Missing architecture: {arch}"

    def test_supportedCatalogs_has_no_unexpected_architectures(self):
        """Test that no unexpected architecture keys are present.

        GIVEN the supportedCatalogs dict
        WHEN its keys are inspected
        THEN it should only contain the known architectures.
        """
        assert set(supportedCatalogs.keys()) == set(SUPPORTED_ARCHES)

    def test_each_arch_has_at_least_one_catalog(self):
        """Test that each architecture has at least one catalog version.

        GIVEN the supportedCatalogs dict
        WHEN each architecture's version list is checked
        THEN each list should be non-empty.
        """
        for arch in SUPPORTED_ARCHES:
            assert len(supportedCatalogs[arch]) > 0, f"No catalogs for arch: {arch}"

    def test_each_arch_has_list_of_strings(self):
        """Test that each architecture maps to a list of strings.

        GIVEN the supportedCatalogs dict
        WHEN the values are inspected
        THEN each value should be a non-empty list of strings.
        """
        for arch in SUPPORTED_ARCHES:
            versions = supportedCatalogs[arch]
            assert isinstance(versions, list), f"Expected list for arch {arch}, got {type(versions)}"
            for v in versions:
                assert isinstance(v, str), f"Expected str version in {arch}, got {type(v)}"


class TestSupportedCatalogVersionFormat:
    """Test the format of individual catalog version strings."""

    @pytest.mark.parametrize("arch", SUPPORTED_ARCHES)
    def test_catalog_versions_match_expected_format(self, arch):
        """Test that all catalog versions match the expected naming format.

        GIVEN catalog versions for a given architecture
        WHEN each version string is checked against the pattern
        THEN each should match v<major>-<YYMMDD>-<arch>.
        """
        for version in supportedCatalogs[arch]:
            assert CATALOG_VERSION_PATTERN.match(version), f"Version '{version}' for arch '{arch}' does not match expected format"

    @pytest.mark.parametrize("arch", SUPPORTED_ARCHES)
    def test_catalog_versions_arch_suffix_matches_key(self, arch):
        """Test that each version's arch suffix matches its dictionary key.

        GIVEN catalog versions for a given architecture
        WHEN the arch suffix in each version string is checked
        THEN it should match the dictionary key.
        """
        for version in supportedCatalogs[arch]:
            assert version.endswith(f"-{arch}"), f"Version '{version}' does not end with '-{arch}'"

    @pytest.mark.parametrize("arch", SUPPORTED_ARCHES)
    def test_catalog_versions_are_unique_per_arch(self, arch):
        """Test that there are no duplicate catalog versions for an architecture.

        GIVEN catalog versions for a given architecture
        WHEN the list is checked for duplicates
        THEN all entries should be unique.
        """
        versions = supportedCatalogs[arch]
        assert len(versions) == len(set(versions)), f"Duplicate versions found for arch: {arch}"

    @pytest.mark.parametrize("arch", SUPPORTED_ARCHES)
    def test_all_arches_have_same_number_of_catalogs(self, arch):
        """Test that all architectures have the same number of supported catalogs.

        GIVEN the supportedCatalogs dict
        WHEN the catalog counts per architecture are compared
        THEN all architectures should have the same count.
        """
        counts = {a: len(supportedCatalogs[a]) for a in SUPPORTED_ARCHES}
        expected = counts["amd64"]
        assert counts[arch] == expected, f"Arch '{arch}' has {counts[arch]} catalogs, expected {expected} (same as amd64)"


class TestCatalogsFileFormatForBashrc:
    """Validate that catalogs.py raw file format is compatible with the grep/sed
    pattern used in .bashrc to display supported catalog versions at startup.

    The .bashrc line reads:
      grep "\"v[0-9]*-[0-9]*-${arch}\"" /mascli/site-packages/mas/cli/install/catalogs.py
        | sed 's/.*"\\(v[^"]*\\)".*/  - \\1/'

    This requires each version string to appear as a double-quoted literal on
    its own line in the source file.
    """

    @pytest.mark.parametrize("arch", SUPPORTED_ARCHES)
    def test_bashrc_grep_pattern_matches_all_versions(self, arch):
        """Test that the .bashrc grep pattern extracts all expected versions.

        GIVEN the catalogs.py source file and a target architecture
        WHEN the same grep/sed pattern used in .bashrc is run via subprocess
        THEN it should return exactly the versions in supportedCatalogs for that arch.
        """
        result = subprocess.run(
            ["bash", "-c", f"grep '\"v[0-9]*-[0-9]*-{arch}\"' {_CATALOGS_PATH} | sed 's/.*\"\\(v[^\"]*\\)\".*/\\1/' | sort -t'-' -k2 -r"],
            capture_output=True,
            text=True,
        )
        extracted = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        expected = sorted(supportedCatalogs[arch], key=lambda v: v.split("-")[1], reverse=True)
        assert extracted == expected, f"grep/sed/sort extracted {extracted} for arch '{arch}', expected {expected}"

    def test_versions_use_double_quotes_in_source(self):
        """Test that all version strings appear as double-quoted literals in the source file.

        GIVEN the raw text of catalogs.py
        WHEN each version string from supportedCatalogs is searched
        THEN each should appear as a double-quoted string (e.g. "v9-261007-amd64")
        so the .bashrc grep pattern can find it.
        """
        with open(_CATALOGS_PATH) as f:
            content = f.read()

        for arch, versions in supportedCatalogs.items():
            for version in versions:
                assert f'"{version}"' in content, (
                    f"Version '{version}' not found as a double-quoted literal in catalogs.py. " f"The .bashrc grep pattern requires double-quoted strings."
                )
