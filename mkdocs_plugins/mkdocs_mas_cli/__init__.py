"""MkDocs plugin for CLI documentation from argparse."""

import re
import sys
import importlib
from pathlib import Path
from mkdocs.plugins import BasePlugin

from .formatter import MarkdownFormatter

__version__ = "0.1.0"


class MASCLIPlugin(BasePlugin):
    """
    Plugin to generate CLI documentation from argparse configurations.

    Supported directive:
    :::mas-cli-usage
    module: mas.cli.install.argParser
    parser: installArgParser
    ignore_description: true
    ignore_epilog: true
    :::
    """

    def on_page_markdown(self, markdown, page, config, files):
        """Replace CLI directives with rendered content."""

        # Pattern to match the directive block
        pattern = r':::mas-cli-usage\s*\n((?:.*\n)*?):::'

        def replace_directive(match):
            """Parse and replace a single directive."""
            params_text = match.group(1)
            params = self._parse_params(params_text)

            if 'module' not in params or 'parser' not in params:
                raise ValueError(
                    "CLI documentation directive missing required parameters. "
                    "Must specify both 'module' and 'parser'. "
                    f"Found parameters: {list(params.keys())}"
                )

            return self._render_cli_usage(
                params['module'],
                params['parser'],
                ignore_description=self._parse_bool(params.get('ignore_description', 'false')),
                ignore_epilog=self._parse_bool(params.get('ignore_epilog', 'false'))
            )

        markdown = re.sub(pattern, replace_directive, markdown)
        return markdown

    def _parse_params(self, params_text):
        """Parse YAML-style parameters from directive."""
        params = {}
        for line in params_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                params[key.strip()] = value.strip()
        return params

    def _parse_bool(self, value):
        """Parse boolean value from string."""
        return value.lower() in ('true', 'yes', '1', 'on')

    def _render_cli_usage(self, module_path, parser_name, ignore_description=False, ignore_epilog=False):
        """Load parser and generate markdown documentation."""
        # Don't catch exceptions - let them propagate to fail the build
        parser = self._load_parser(module_path, parser_name)
        formatter = MarkdownFormatter()
        return formatter.format_parser(parser, ignore_description=ignore_description, ignore_epilog=ignore_epilog)

    def _load_parser(self, module_path, parser_name):
        """Dynamically import and return the ArgumentParser."""
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            # If import fails, try adding python/src to path (for development)
            # This handles cases where mkdocs runs in a subprocess
            python_src = Path(__file__).parent.parent.parent / "python" / "src"

            # Always try to add the path if it exists
            if python_src.exists():
                python_src_str = str(python_src.resolve())
                if python_src_str not in sys.path:
                    sys.path.insert(0, python_src_str)

                # Force reload of importlib to pick up new path
                importlib.invalidate_caches()

                try:
                    module = importlib.import_module(module_path)
                except ImportError as e2:
                    raise ImportError(
                        f"Could not import {module_path}. "
                        f"Tried adding {python_src_str} to sys.path. "
                        f"Original error: {e}. "
                        f"After path addition: {e2}"
                    )
            else:
                raise ImportError(
                    f"Could not import {module_path}. "
                    f"Python source path {python_src} does not exist. "
                    f"Error: {e}"
                )

        if not hasattr(module, parser_name):
            raise AttributeError(
                f"Module {module_path} does not have attribute '{parser_name}'"
            )

        parser = getattr(module, parser_name)

        # Verify it's an ArgumentParser
        if not hasattr(parser, '_action_groups'):
            raise TypeError(
                f"{parser_name} is not an ArgumentParser instance"
            )

        return parser


# Made with Bob
