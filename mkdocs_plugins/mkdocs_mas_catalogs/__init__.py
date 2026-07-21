"""MkDocs plugin for MAS catalog details."""

import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from mkdocs.plugins import BasePlugin

__version__ = "0.1.0"

log = logging.getLogger("mkdocs.plugins.mas_catalogs")

# Try to import from installed package first
try:
    from mas.devops.data import getCatalog, getOCPLifecycleData, getCatalogEditorial, NoSuchCatalogError
except ImportError:
    # Development fallback: add python-devops to path
    PYTHON_DEVOPS_PATH = Path(__file__).parent.parent.parent.parent / "python-devops" / "src"
    if PYTHON_DEVOPS_PATH.exists():
        sys.path.insert(0, str(PYTHON_DEVOPS_PATH))
        from mas.devops.data import getCatalog, getOCPLifecycleData, getCatalogEditorial, NoSuchCatalogError
    else:
        raise ImportError("Could not import mas.devops.data. " "Please install python-devops package or ensure it's available at ../python-devops/")


# ---------------------------------------------------------------------------
# Disk cache helpers
# ---------------------------------------------------------------------------

_CACHE_DIR = Path(os.environ.get("MAS_DOCS_CACHE_DIR", ".mkdocs_cache")) / "catalogs"
_NO_CACHE = os.environ.get("MAS_DOCS_NO_CACHE", "").lower() in ("1", "true", "yes")


def _data_dir_fingerprint() -> str:
    """Return a single fingerprint for the entire python-devops catalog data directory.

    Uses the maximum mtime across all YAML files in the two data subdirectories.
    This is computed **once** at plugin startup so no per-page stat() calls are needed.
    If the directory cannot be located the fingerprint is the string 'unknown'.
    """
    plugin_dir = Path(__file__).parent
    devops_data = plugin_dir.parent.parent.parent / "python-devops" / "src" / "mas" / "devops" / "data"
    search_dirs = [devops_data / "catalogs", devops_data / "editorial"]

    mtimes = []
    for d in search_dirs:
        if d.exists():
            for f in d.glob("*.yaml"):
                mtimes.append(f.stat().st_mtime)

    if not mtimes:
        return "unknown"
    return hashlib.md5(str(max(mtimes)).encode()).hexdigest()


def _disk_get(key: str):
    """Return a cached string from disk, or None."""
    if _NO_CACHE:
        return None
    cache_file = _CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _disk_set(key: str, value: str) -> None:
    """Persist a string value to the disk cache."""
    if _NO_CACHE:
        return
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (_CACHE_DIR / f"{key}.json").write_text(json.dumps(value), encoding="utf-8")
    except Exception:
        pass


def _section_cache_key(catalog_tag: str, section: str, fingerprint: str) -> str:
    """Return a stable MD5 cache key for one rendered section."""
    return hashlib.md5(f"{catalog_tag}:{section}:{fingerprint}".encode()).hexdigest()


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

SECTION_PATTERN = re.compile(r":::mas-catalog-(details|install|source|ocp-compatibility-matrix|whats-new|known-issues)")


class MASCatalogsPlugin(BasePlugin):
    """
    Plugin to inject catalog metadata dynamically.

    Supported directives:
    - :::mas-catalog-details
    - :::mas-catalog-install
    - :::mas-catalog-source
    - :::mas-catalog-ocp-compatibility-matrix
    - :::mas-catalog-whats-new
    - :::mas-catalog-known-issues

    The catalog tag is automatically detected from the page filename.
    For example, in v9-251127-amd64.md, the tag is v9-251127-amd64

    All catalog pages are pre-rendered once per build in `on_env` and stored in
    an in-process dict keyed by (catalog_tag, section).  `on_page_markdown` then
    only performs a dict lookup — zero I/O, zero data loading.

    Rendered sections are also persisted to .mkdocs_cache/ so that the very
    first page of a fresh `mkdocs serve` run is also fast once the cache is warm.
    Set MAS_DOCS_NO_CACHE=1 to disable the disk cache entirely.
    """

    def on_files(self, files, config):
        """Pre-render all catalog sections for every catalog page, once per build.

        Uses on_files (fires on every build including dirty/incremental) rather
        than on_env so that self._rendered is always populated before
        on_page_markdown is called.

        On subsequent calls (dirty/watch reloads) the fingerprint is compared
        against the previous run; if nothing in python-devops has changed the
        already-populated self._rendered dict is reused without any I/O.
        """
        fingerprint = _data_dir_fingerprint()

        # Fast path: data unchanged and we already have rendered content
        if getattr(self, "_rendered", None) and getattr(self, "_fingerprint", None) == fingerprint:
            log.debug("mas_catalogs: data unchanged, reusing %d pre-rendered sections", len(self._rendered))
            return files

        self._rendered: dict = {}
        self._fingerprint = fingerprint

        catalog_pages = [f for f in files if re.match(r"catalogs/(v8|v9)-\d{6}-.+\.md$", f.src_path)]

        sections = ["details", "install", "source", "ocp_matrix", "whats_new", "known_issues"]
        hits = 0
        misses = 0

        for page_file in catalog_pages:
            tag = Path(page_file.src_path).stem
            for section in sections:
                key = _section_cache_key(tag, section, fingerprint)
                cached = _disk_get(key)
                if cached is not None:
                    self._rendered[(tag, section)] = cached
                    hits += 1
                else:
                    rendered = self._render_section(tag, section)
                    self._rendered[(tag, section)] = rendered
                    _disk_set(key, rendered)
                    misses += 1

        log.info(
            "mas_catalogs: pre-rendered %d catalog sections (%d disk hits, %d rendered)",
            len(self._rendered),
            hits,
            misses,
        )
        return files

    def on_page_markdown(self, markdown, page, config, files):
        """Replace catalog directives with pre-rendered content — O(1) dict lookup."""
        page_name = Path(page.file.src_path).stem

        # Only process pages that look like catalog pages
        if not re.match(r"(v8|v9)-\d{6}-.+", page_name):
            return markdown

        tag = page_name

        def _replace(m):
            # Normalise directive slug to section key
            slug = m.group(1)  # e.g. "ocp-compatibility-matrix"
            section = slug.replace("-", "_")  # e.g. "ocp_matrix"
            # Map the directive slug variants to section keys
            section = {
                "ocp_compatibility_matrix": "ocp_matrix",
                "whats_new": "whats_new",
                "known_issues": "known_issues",
            }.get(section, section)
            return self._rendered.get((tag, section), "")

        return SECTION_PATTERN.sub(_replace, markdown)

    def _render_section(self, catalog_tag: str, section: str) -> str:
        """Dispatch to the correct renderer for section, skipping unknown catalogs."""
        dispatch = {
            "details": self._render_details,
            "install": self._render_install,
            "source": self._render_source,
            "ocp_matrix": self._render_ocp_matrix,
            "whats_new": self._render_whats_new,
            "known_issues": self._render_known_issues,
        }
        fn = dispatch.get(section)
        if fn is None:
            return ""
        try:
            return fn(catalog_tag)
        except NoSuchCatalogError:
            return ""

    def _get_catalog_data(self, catalog_tag):
        """Get catalog data and handle errors."""
        try:
            catalog = getCatalog(catalog_tag)
            return catalog, None
        except NoSuchCatalogError:
            return (
                None,
                f"""!!! error
    Catalog {catalog_tag} not found in python-devops.

    Make sure the catalog metadata exists at:
    `python-devops/src/mas/devops/data/catalogs/{catalog_tag}.yaml`
""",
            )

    def _render_details(self, catalog_tag):
        """Render the Details section."""
        catalog, error = self._get_catalog_data(catalog_tag)
        if error:
            return error

        digest = catalog.get("catalog_digest", "N/A")

        return f"""Details
-------------------------------------------------------------------------------

<table>
  <tr><td>Image</td><td>icr.io/cpopen/ibm-maximo-operator-catalog</td></tr>
  <tr><td>Tag</td><td>{catalog_tag}</td></tr>
  <tr><td>Digest</td><td>{digest}</td></tr>
</table>
"""

    def _render_install(self, catalog_tag):
        """Render the Manual Installation section."""
        catalog, error = self._get_catalog_data(catalog_tag)
        if error:
            return error

        return f"""Manual Installation
-------------------------------------------------------------------------------
`oc apply -f https://raw.githubusercontent.com/ibm-mas/cli/master/catalogs/{catalog_tag}.yaml`
"""

    def _render_source(self, catalog_tag):
        """Render the Source section with CatalogSource YAML."""
        catalog, error = self._get_catalog_data(catalog_tag)
        if error:
            return error

        digest = catalog.get("catalog_digest", "N/A")

        return f"""Source
-------------------------------------------------------------------------------
```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: ibm-operator-catalog
  namespace: openshift-marketplace
spec:
  displayName: IBM Maximo Operators ({catalog_tag})
  publisher: IBM
  description: Static Catalog Source for IBM Maximo Application Suite
  sourceType: grpc
  image: icr.io/cpopen/ibm-maximo-operator-catalog@{digest}
  priority: 90
```
"""

    def _render_ocp_matrix(self, catalog_tag):
        """Render the OCP compatibility matrix table."""
        catalog, error = self._get_catalog_data(catalog_tag)
        if error:
            return error

        ocp_versions = catalog.get("ocp_compatibility", [])

        if not ocp_versions:
            return """!!! warning
    No OCP compatibility data available for this catalog.
"""

        ocp_lifecycle_data = getOCPLifecycleData()
        if not ocp_lifecycle_data:
            return """!!! error
    OCP lifecycle data not found. Please ensure ocp.yaml exists in python-devops.
"""

        table_html = """The Red Hat Extended Update Support Add-on Term 1 offering is included with the OCP subscription that comes with a MAS license. In the case of EUS denoted OCP releases, any support dates stated refer to the EUS1 end dates.

For more details refer to the [OCP lifecycle policy](https://access.redhat.com/support/policy/updates/openshift).  Also note that non-EUS release support expires before the extended support for the previous EUS release, for example extended support for OCP 4.18 expires on Feb 25, 2027, while standard support for OCP 4.17 expires on April 1, 2026.

<table class="compatabilityMatrix">
  <tr>
    <th>OCP</th><td rowspan="{}" class="spacer"></td>
    <th>General Availability</th>
    <th>Standard Support</th>
    <th>Extended Support</th>
  </tr>
""".format(
            len(ocp_versions) + 1
        )

        ocp_data = ocp_lifecycle_data.get("ocp_versions", {})
        for version in ocp_versions:
            version_str = str(version)
            version_info = ocp_data.get(version_str, {})

            ga_date = version_info.get("ga_date", "N/A")
            standard_support = version_info.get("standard_support", "N/A")
            extended_support = version_info.get("extended_support", "N/A")

            if extended_support == "N/A":
                extended_support = " N/A "

            table_html += f"""  <tr>
    <td class="firstColumn">{version_str}</td>
    <td>{ga_date}</td>
    <td>{standard_support}</td>
    <td>{extended_support}</td>
  </tr>
"""

        table_html += "</table>"
        return table_html

    def _render_whats_new(self, catalog_tag):
        """Render the What's New section."""
        try:
            editorial = getCatalogEditorial(catalog_tag)
        except NoSuchCatalogError:
            return ""

        if not editorial:
            return ""

        whats_new = editorial.get("whats_new", [])
        if not whats_new:
            return ""

        if isinstance(whats_new, str):
            whats_new_text = whats_new.strip()
        else:
            lines = []
            for item in whats_new:
                title = item.get("title", "")
                details = item.get("details", [])
                lines.append(f"- {title}")
                for detail in details:
                    lines.append(f"    - {detail}")
            whats_new_text = "\n".join(lines)

        if not whats_new_text:
            return ""

        return f"""What's New
-------------------------------------------------------------------------------
{whats_new_text}
"""

    def _render_known_issues(self, catalog_tag):
        """Render the Known Issues section."""
        try:
            editorial = getCatalogEditorial(catalog_tag)
        except NoSuchCatalogError:
            return ""

        no_issues = """Known Issues
-------------------------------------------------------------------------------
There are no known issues for this catalog release.
"""

        if not editorial:
            return no_issues

        known_issues = editorial.get("known_issues", [])
        if not known_issues:
            return no_issues

        if isinstance(known_issues, str):
            known_issues_text = known_issues.strip()
        else:
            lines = [f"- {item.get('title', '')}" for item in known_issues if item.get("title")]
            known_issues_text = "\n".join(lines)

        if not known_issues_text:
            return no_issues

        return f"""Known Issues
-------------------------------------------------------------------------------
{known_issues_text}
"""
