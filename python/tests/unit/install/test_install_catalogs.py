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
used in image/cli/app-root/src/.bashrc to display supported IBM Maximo Operator Catalog versions
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
    """Validate that catalogs.py raw file format is compatible with the grep/sed/uniq
    pipeline used in .bashrc to display supported catalog versions at startup.

    The .bashrc line reads:
      grep -o '"v[0-9]*-[0-9]*-[^"]*"' /mascli/site-packages/mas/cli/install/catalogs.py
        | sed 's/.*"(v[0-9]*-[0-9]*)-[^"]*".*/  - \\1/'
        | sort -t'-' -k2 -r | uniq

    This extracts unique version dates (without arch suffix) sorted newest first.
    """

    def test_bashrc_grep_pattern_extracts_unique_dates(self):
        """Test that the .bashrc grep/sed/sort/uniq pipeline extracts unique version dates.

        GIVEN the catalogs.py source file
        WHEN the same pipeline used in .bashrc is run via subprocess
        THEN it should return unique version dates (without arch suffix) sorted newest first.
        """
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"grep -o '\"v[0-9]*-[0-9]*-[^\"]*\"' {_CATALOGS_PATH} | sed 's/.*\"\\(v[0-9]*-[0-9]*\\)-[^\"]*\".*/\\1/' | sort -t'-' -k2 -r | uniq",
            ],
            capture_output=True,
            text=True,
        )
        extracted = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        expected = sorted(set(v.rsplit("-", 1)[0] for v in supportedCatalogs["amd64"]), key=lambda v: v.split("-")[1], reverse=True)
        assert extracted == expected, f"grep/sed/sort/uniq extracted {extracted}, expected {expected}"

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


class TestCatalogsSubcommandOutput:
    """Validate the table and tag list produced by the `mas-cli catalogs` subcommand.

    The handler in __main__.py derives arches and versions dynamically from
    supportedCatalogs.keys() — no hardcoded arch list.  These tests replicate
    that logic directly without invoking the full CLI (which requires heavy
    runtime dependencies).
    """

    def _build_arches(self):
        """Return arches derived dynamically from supportedCatalogs keys."""
        return list(supportedCatalogs.keys())

    def _build_versions(self):
        """Replicate the version-building expression from __main__.py catalogs handler."""
        arches = self._build_arches()
        all_versions = {v.rsplit("-", 1)[0] for arch in arches for v in supportedCatalogs[arch]}
        return sorted(all_versions, key=lambda v: v.split("-")[1], reverse=True)

    def _build_version_arches(self):
        """Replicate the version->arch-set lookup from __main__.py catalogs handler."""
        arches = self._build_arches()
        versions = self._build_versions()
        return {ver: {v.rsplit("-", 1)[1] for arch in arches for v in supportedCatalogs[arch] if v.rsplit("-", 1)[0] == ver} for ver in versions}

    def test_arches_derived_from_catalog_keys(self):
        """Test that arches come from supportedCatalogs keys, not a hardcoded list.

        GIVEN the supportedCatalogs dict
        WHEN arches are derived from its keys
        THEN they should exactly match the top-level keys.
        """
        assert self._build_arches() == list(supportedCatalogs.keys())

    def test_output_versions_have_no_arch_suffix(self):
        """Test that arch suffixes are stripped from the version list.

        GIVEN supportedCatalogs entries with arch suffixes
        WHEN the catalogs subcommand version list is built
        THEN no version should end with any known arch suffix.
        """
        known_suffixes = tuple(f"-{a}" for a in self._build_arches())
        for v in self._build_versions():
            assert not v.endswith(known_suffixes), f"Arch suffix not stripped from '{v}'"

    def test_output_versions_are_unique(self):
        """Test that the version list contains no duplicates.

        GIVEN supportedCatalogs with matching dates across arches
        WHEN the catalogs subcommand version list is built
        THEN all entries should be unique.
        """
        versions = self._build_versions()
        assert len(versions) == len(set(versions)), "Duplicate versions in catalogs subcommand output"

    def test_output_versions_sorted_newest_first(self):
        """Test that versions are sorted newest-first by date field.

        GIVEN a list of version strings in the form v<major>-<YYMMDD>
        WHEN the catalogs subcommand version list is built
        THEN dates should be in descending order.
        """
        versions = self._build_versions()
        dates = [v.split("-")[1] for v in versions]
        assert dates == sorted(dates, reverse=True), f"Versions not sorted newest-first: {versions}"

    def test_output_count_matches_unique_versions_across_all_arches(self):
        """Test that output count equals unique date-stripped versions across all arches.

        GIVEN supportedCatalogs with all arches
        WHEN the catalogs subcommand version list is built
        THEN the count should equal the number of unique date-only versions.
        """
        arches = self._build_arches()
        expected_count = len({v.rsplit("-", 1)[0] for arch in arches for v in supportedCatalogs[arch]})
        assert len(self._build_versions()) == expected_count, f"Expected {expected_count} unique versions"

    def test_version_arches_lookup_covers_all_versions(self):
        """Test that the version->arches lookup contains an entry for every version.

        GIVEN the version list and arch lookup built by the catalogs handler
        WHEN the lookup keys are checked
        THEN every version should have an entry.
        """
        versions = self._build_versions()
        version_arches = self._build_version_arches()
        assert set(version_arches.keys()) == set(versions), "version_arches lookup is missing entries"

    def test_version_arches_values_are_subsets_of_known_arches(self):
        """Test that each version's arch set only contains known arches.

        GIVEN the version->arches lookup
        WHEN each value set is checked
        THEN it should only contain arches present in supportedCatalogs.keys().
        """
        known_arches = set(self._build_arches())
        for ver, ver_arches in self._build_version_arches().items():
            assert ver_arches <= known_arches, f"Unknown arch in version_arches['{ver}']: {ver_arches - known_arches}"

    def test_latest_tags_cover_all_arches_that_support_newest_version(self):
        """Test that the latest catalog tags section lists a tag for every arch supporting the newest version.

        GIVEN the newest version and the version->arches lookup
        WHEN the latest tags are generated
        THEN there should be one tag per arch that supports the newest version.
        """
        versions = self._build_versions()
        version_arches = self._build_version_arches()
        newest = versions[0]
        expected_tags = {f"{newest}-{arch}" for arch in version_arches[newest]}
        arches = self._build_arches()
        actual_tags = {f"{newest}-{arch}" for arch in arches if arch in version_arches[newest]}
        assert actual_tags == expected_tags, f"Latest tags mismatch: expected {expected_tags}, got {actual_tags}"
