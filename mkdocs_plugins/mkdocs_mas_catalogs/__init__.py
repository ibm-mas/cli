"""MkDocs plugin for MAS catalog details."""

import sys
from pathlib import Path
import re
from mkdocs.plugins import BasePlugin

__version__ = "0.1.0"

# Try to import from installed package first
try:
    from mas.devops.data import getCatalog
except ImportError:
    # Development fallback: add python-devops to path
    PYTHON_DEVOPS_PATH = (
        Path(__file__).parent.parent.parent.parent / "python-devops" / "src"
    )
    if PYTHON_DEVOPS_PATH.exists():
        sys.path.insert(0, str(PYTHON_DEVOPS_PATH))
        from mas.devops.data import getCatalog
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

        return markdown

    def _get_catalog_data(self, catalog_tag):
        """Get catalog data and handle errors."""
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


# Made with Bob
