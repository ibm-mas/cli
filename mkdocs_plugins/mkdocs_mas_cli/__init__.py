"""MkDocs plugin for CLI documentation from argparse."""

import hashlib
import importlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from mkdocs.plugins import BasePlugin

from .formatter import MarkdownFormatter

__version__ = "0.1.0"

log = logging.getLogger("mkdocs.plugins.mas_cli")


# ---------------------------------------------------------------------------
# Disk cache helpers
# ---------------------------------------------------------------------------

_CACHE_DIR = Path(os.environ.get("MAS_DOCS_CACHE_DIR", ".mkdocs_cache")) / "cli"
_NO_CACHE = os.environ.get("MAS_DOCS_NO_CACHE", "").lower() in ("1", "true", "yes")


def _module_fingerprint(module_path: str) -> str:
    """Return a mtime-based fingerprint for the argparser source file.

    Computed once per (module_path) value; the result is stable for the lifetime
    of the process.  Uses the source file mtime when the module lives under
    python/src, otherwise tries importlib.util.find_spec.
    """
    python_src = Path(__file__).parent.parent.parent / "python" / "src"
    source_file = python_src / (module_path.replace(".", os.sep) + ".py")

    if source_file.exists():
        return str(source_file.stat().st_mtime)

    try:
        spec = importlib.util.find_spec(module_path)
        if spec and spec.origin:
            return str(Path(spec.origin).stat().st_mtime)
    except Exception:
        pass

    return module_path  # stable fallback — won't bust the cache but won't produce stale data


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


def _cli_cache_key(module_path: str, parser_name: str, ignore_description: bool, ignore_epilog: bool) -> str:
    """Return a stable MD5 cache key for one rendered CLI usage block."""
    fingerprint = _module_fingerprint(module_path)
    raw = f"{module_path}:{parser_name}:{ignore_description}:{ignore_epilog}:{fingerprint}"
    return hashlib.md5(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

# Pattern to match the full directive block
_DIRECTIVE_PATTERN = re.compile(r":::mas-cli-usage\s*\n((?:.*\n)*?):::")


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

    All directives across all pages are discovered and rendered once in `on_env`.
    `on_page_markdown` then only performs a dict lookup keyed by the raw directive
    text — zero I/O, zero module imports on subsequent calls.

    Results are also persisted to .mkdocs_cache/ so subsequent `mkdocs serve`
    starts skip rendering entirely if the source module has not changed.
    Set MAS_DOCS_NO_CACHE=1 to disable the disk cache.
    """

    def on_files(self, files, config):
        """Discover all CLI directives across all source files and render them once.

        Uses on_files (fires on every build including dirty/incremental) rather
        than on_env so that self._rendered is always populated before
        on_page_markdown is called.

        On subsequent calls (dirty/watch reloads) the already-populated
        self._rendered dict is reused if no argparser source files have changed.
        """
        # Compute fingerprint across all argparser source files in one pass
        python_src = Path(__file__).parent.parent.parent / "python" / "src"
        fingerprint = "unknown"
        if python_src.exists():
            mtimes = [f.stat().st_mtime for f in python_src.rglob("argParser.py")]
            if mtimes:
                fingerprint = hashlib.md5(str(max(mtimes)).encode()).hexdigest()

        # Fast path: source unchanged and we already have rendered content
        if getattr(self, "_rendered", None) and getattr(self, "_cli_fingerprint", None) == fingerprint:
            log.debug("mas_cli: source unchanged, reusing %d pre-rendered CLI blocks", len(self._rendered))
            return files

        self._rendered: dict = {}  # raw_params_text -> rendered markdown
        self._cli_fingerprint = fingerprint
        hits = 0
        misses = 0

        for page_file in files:
            if not page_file.src_path.endswith(".md"):
                continue
            try:
                content = Path(page_file.abs_src_path).read_text(encoding="utf-8")
            except Exception:
                continue

            for m in _DIRECTIVE_PATTERN.finditer(content):
                params_text = m.group(1)
                if params_text in self._rendered:
                    continue  # already scheduled

                params = self._parse_params(params_text)
                if "module" not in params or "parser" not in params:
                    continue

                module_path = params["module"]
                parser_name = params["parser"]
                ignore_description = self._parse_bool(params.get("ignore_description", "false"))
                ignore_epilog = self._parse_bool(params.get("ignore_epilog", "false"))

                key = _cli_cache_key(module_path, parser_name, ignore_description, ignore_epilog)
                cached = _disk_get(key)
                if cached is not None:
                    self._rendered[params_text] = cached
                    hits += 1
                else:
                    rendered = self._render_cli_usage(
                        module_path,
                        parser_name,
                        ignore_description=ignore_description,
                        ignore_epilog=ignore_epilog,
                    )
                    self._rendered[params_text] = rendered
                    _disk_set(key, rendered)
                    misses += 1

        log.info(
            "mas_cli: pre-rendered %d CLI usage blocks (%d disk hits, %d rendered)",
            len(self._rendered),
            hits,
            misses,
        )
        return files

    def on_page_markdown(self, markdown, page, config, files):
        """Replace CLI directives with pre-rendered content — O(1) dict lookup."""

        def replace_directive(match):
            """Swap the raw directive for its pre-rendered output."""
            params_text = match.group(1)
            result = self._rendered.get(params_text)
            if result is not None:
                return result

            # Fallback: render on-demand (e.g. if on_env was skipped)
            params = self._parse_params(params_text)
            if "module" not in params or "parser" not in params:
                raise ValueError(
                    "CLI documentation directive missing required parameters. "
                    "Must specify both 'module' and 'parser'. "
                    f"Found parameters: {list(params.keys())}"
                )
            return self._render_cli_usage(
                params["module"],
                params["parser"],
                ignore_description=self._parse_bool(params.get("ignore_description", "false")),
                ignore_epilog=self._parse_bool(params.get("ignore_epilog", "false")),
            )

        return _DIRECTIVE_PATTERN.sub(replace_directive, markdown)

    def _parse_params(self, params_text):
        """Parse YAML-style parameters from directive."""
        params = {}
        for line in params_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                params[key.strip()] = value.strip()
        return params

    def _parse_bool(self, value):
        """Parse boolean value from string."""
        return value.lower() in ("true", "yes", "1", "on")

    def _render_cli_usage(self, module_path, parser_name, ignore_description=False, ignore_epilog=False):
        """Load parser and generate markdown documentation."""
        parser = self._load_parser(module_path, parser_name)
        formatter = MarkdownFormatter()
        return formatter.format_parser(parser, ignore_description=ignore_description, ignore_epilog=ignore_epilog)

    def _load_parser(self, module_path, parser_name):
        """Dynamically import and return the ArgumentParser."""
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            python_src = Path(__file__).parent.parent.parent / "python" / "src"

            if python_src.exists():
                python_src_str = str(python_src.resolve())
                if python_src_str not in sys.path:
                    sys.path.insert(0, python_src_str)

                importlib.invalidate_caches()

                try:
                    module = importlib.import_module(module_path)
                except ImportError as e2:
                    raise ImportError(
                        f"Could not import {module_path}. " f"Tried adding {python_src_str} to sys.path. " f"Original error: {e}. " f"After path addition: {e2}"
                    )
            else:
                raise ImportError(f"Could not import {module_path}. " f"Python source path {python_src} does not exist. " f"Error: {e}")

        if not hasattr(module, parser_name):
            raise AttributeError(f"Module {module_path} does not have attribute '{parser_name}'")

        parser = getattr(module, parser_name)

        if not hasattr(parser, "_action_groups"):
            raise TypeError(f"{parser_name} is not an ArgumentParser instance")

        return parser
