"""MkDocs plugin for MAS catalog details."""

import sys
from pathlib import Path
import re
from mkdocs.plugins import BasePlugin

__version__ = "0.1.0"

# Try to import from installed package first
try:
    from mas.devops.data import getCatalog, getOCPLifecycleData, getCatalogEditorial
except ImportError:
    # Development fallback: add python-devops to path
    PYTHON_DEVOPS_PATH = (
        Path(__file__).parent.parent.parent.parent / "python-devops" / "src"
    )
    if PYTHON_DEVOPS_PATH.exists():
        sys.path.insert(0, str(PYTHON_DEVOPS_PATH))
        from mas.devops.data import getCatalog, getOCPLifecycleData, getCatalogEditorial
    else:
        raise ImportError(
            "Could not import mas.devops.data. "
            "Please install python-devops package or ensure it's available at ../python-devops/"
        )


class MASCatalogsPlugin(BasePlugin):
    """
    Plugin to inject catalog metadata dynamically.

    Supported directives:
    - :::mas-catalog-details - Renders the Details table
    - :::mas-catalog-install - Renders the Manual Installation command
    - :::mas-catalog-source - Renders the CatalogSource YAML
    - :::mas-catalog-ocp-compatibility-matrix - Renders the OCP compatibility matrix
    - :::mas-catalog-whats-new - Renders the What's New section
    - :::mas-catalog-known-issues - Renders the Known Issues section

    The catalog tag is automatically detected from the page filename.
    For example, in v9-251127-amd64.md, the tag is v9-251127-amd64
    """

    def on_page_markdown(self, markdown, page, config, files):
        """Replace catalog directives with rendered content."""

        # Extract catalog tag from page filename
        # e.g., "catalogs/v9-251127-amd64.md" -> "v9-251127-amd64"
        page_name = Path(page.file.src_path).stem
        catalog_tag = page_name

        # Replace all directives
        markdown = re.sub(
            r":::mas-catalog-details",
            lambda m: self._render_details(catalog_tag),
            markdown,
        )
        markdown = re.sub(
            r":::mas-catalog-install",
            lambda m: self._render_install(catalog_tag),
            markdown,
        )
        markdown = re.sub(
            r":::mas-catalog-source",
            lambda m: self._render_source(catalog_tag),
            markdown,
        )
        markdown = re.sub(
            r":::mas-catalog-ocp-compatibility-matrix",
            lambda m: self._render_ocp_matrix(catalog_tag),
            markdown,
        )
        markdown = re.sub(
            r":::mas-catalog-whats-new",
            lambda m: self._render_whats_new(catalog_tag),
            markdown,
        )
        markdown = re.sub(
            r":::mas-catalog-known-issues",
            lambda m: self._render_known_issues(catalog_tag),
            markdown,
        )

        return markdown

    def _get_catalog_data(self, catalog_tag):
        """Get catalog data and handle errors."""
        try:
            catalog = getCatalog(catalog_tag)

            if not catalog:
                return (
                    None,
                    f"""!!! error
    Catalog {catalog_tag} not found in python-devops.

    Make sure the catalog metadata exists at:
    `python-devops/src/mas/devops/data/catalogs/{catalog_tag}.yaml`
""",
                )

            return catalog, None
        except Exception as e:
            # Handle NoSuchCatalogError and other exceptions gracefully
            return (
                None,
                f"""!!! warning
    Catalog {catalog_tag} metadata not available in python-devops.

    This is an older catalog version. The metadata file does not exist at:
    `python-devops/src/mas/devops/data/catalogs/{catalog_tag}.yaml`

    Error: {str(e)}
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

        # Get OCP compatibility list from catalog
        ocp_versions = catalog.get("ocp_compatibility", [])

        if not ocp_versions:
            return """!!! warning
    No OCP compatibility data available for this catalog.
"""

        # Get OCP lifecycle data using the API
        ocp_lifecycle_data = getOCPLifecycleData()
        if not ocp_lifecycle_data:
            return """!!! error
    OCP lifecycle data not found. Please ensure ocp.yaml exists in python-devops.
"""

        # Build the table header
        table_html = """<table class="compatabilityMatrix">
  <tr>
    <th>OCP</th><td rowspan="{}" class="spacer"></td>
    <th>General Availability</th>
    <th>Standard Support</th>
    <th>Extended Support</th>
  </tr>
""".format(
            len(ocp_versions) + 1
        )

        # Add rows for each OCP version
        ocp_data = ocp_lifecycle_data.get("ocp_versions", {})
        for version in ocp_versions:
            version_str = str(version)
            version_info = ocp_data.get(version_str, {})

            ga_date = version_info.get("ga_date", "N/A")
            standard_support = version_info.get("standard_support", "N/A")
            extended_support = version_info.get("extended_support", "N/A")

            # Format extended support - use "N/A" if it's literally "N/A"
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
        editorial = getCatalogEditorial(catalog_tag)

        if not editorial:
            return ""  # No editorial content, return empty string

        whats_new = editorial.get("whats_new", [])

        if not whats_new:
            return ""  # No What's New content

        # Handle both old string format and new structured format
        if isinstance(whats_new, str):
            # Old format: plain text
            whats_new_text = whats_new.strip()
        else:
            # New format: list of items with title and details
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
        editorial = getCatalogEditorial(catalog_tag)

        # If no editorial data exists, show "no known issues"
        if not editorial:
            return """Known Issues
-------------------------------------------------------------------------------
There are no known issues for this catalog release.
"""

        known_issues = editorial.get("known_issues", [])

        # If known_issues field exists but is empty, show "no known issues"
        if not known_issues:
            return """Known Issues
-------------------------------------------------------------------------------
There are no known issues for this catalog release.
"""

        # Handle both old string format and new structured format
        if isinstance(known_issues, str):
            # Old format: plain text
            known_issues_text = known_issues.strip()
        else:
            # New format: list of items with title
            lines = []
            for item in known_issues:
                title = item.get("title", "")
                if title:
                    lines.append(f"- {title}")

            known_issues_text = "\n".join(lines)

        if not known_issues_text:
            return """Known Issues
-------------------------------------------------------------------------------
There are no known issues for this catalog release.
"""

        return f"""Known Issues
-------------------------------------------------------------------------------
{known_issues_text}
"""


# Made with Bob
