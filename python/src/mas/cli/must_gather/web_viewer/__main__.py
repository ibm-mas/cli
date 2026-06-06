"""Command-line interface for generating and serving web viewer for must-gather output.

This module provides commands to generate the web viewer and optionally
serve it via HTTP for easy viewing in a browser.
"""

import argparse
import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path

from mas.cli.must_gather import web_viewer


def main():
    """Generate and optionally serve web viewer for must-gather output."""
    parser = argparse.ArgumentParser(
        prog="python -m mas.cli.must_gather.web_viewer",
        description="Generate and serve web viewer for must-gather output",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate web viewer files (index.html and manifest.json)")
    generate_parser.add_argument(
        "directory",
        type=str,
        help="Path to must-gather output directory",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Generate viewer and start HTTP server")
    serve_parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Path to must-gather output directory",
    )
    serve_parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server (default: 8000)")
    serve_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser",
    )

    args = parser.parse_args()

    # Default to serve if no command specified but directory given
    if not args.command:
        if len(sys.argv) > 1:
            # Assume it's a directory for backward compatibility
            args.command = "generate"
            args.directory = sys.argv[1]
        else:
            parser.print_help()
            return 1

    if args.command == "generate":
        return generate_viewer(args.directory)
    elif args.command == "serve":
        return serve_viewer(args.dir, args.port, not args.no_browser)
    else:
        parser.print_help()
        return 1


def generate_viewer(directory: str) -> int:
    """Generate web viewer for a must-gather directory.

    Args:
        directory (str): Path to must-gather output directory

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Validate directory exists
    outputDir = Path(directory)
    if not outputDir.exists():
        print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
        return 1

    if not outputDir.is_dir():
        print(f"Error: Path is not a directory: {directory}", file=sys.stderr)
        return 1

    # Generate web viewer
    print(f"Generating web viewer for: {directory}")
    if web_viewer.generateWebViewer(str(outputDir)):
        print("\n✅ Web viewer generated successfully!")
        print("\nTo view the must-gather, run:")
        print(f"  python -m mas.cli.must_gather.web_viewer serve --dir {directory}\n")
        return 0
    else:
        print("\n❌ Failed to generate web viewer", file=sys.stderr)
        print("   Check the logs for details", file=sys.stderr)
        return 1


def serve_viewer(directory: str, port: int, open_browser: bool) -> int:
    """Generate viewer and start HTTP server.

    Args:
        directory (str): Path to must-gather output directory
        port (int): Port number for HTTP server
        open_browser (bool): Whether to automatically open browser

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Validate directory
    outputDir = Path(directory)
    if not outputDir.exists():
        print(f"Error: Directory does not exist: {directory}", file=sys.stderr)
        return 1

    if not outputDir.is_dir():
        print(f"Error: Path is not a directory: {directory}", file=sys.stderr)
        return 1

    # Generate viewer if needed
    indexPath = outputDir / "index.html"
    if not indexPath.exists():
        print(f"Generating web viewer for: {directory}")
        if not web_viewer.generateWebViewer(str(outputDir)):
            print("\n❌ Failed to generate web viewer", file=sys.stderr)
            return 1
        print("✅ Web viewer generated\n")
    else:
        print(f"Using existing web viewer in: {directory}\n")

    # Start HTTP server
    print(f"Starting HTTP server on port {port}...")
    print(f"View must-gather at: http://localhost:{port}/")
    print("Press Ctrl+C to stop the server\n")

    # Change to the output directory
    import os

    os.chdir(str(outputDir))

    # Open browser if requested
    if open_browser:
        webbrowser.open(f"http://localhost:{port}/")

    # Start server
    Handler = http.server.SimpleHTTPRequestHandler
    Handler.extensions_map.update({".yaml": "text/plain", ".yml": "text/plain", ".log": "text/plain"})

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
            return 0  # This line is never reached but satisfies type checker
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        return 0
    except OSError as e:
        print(f"\n❌ Failed to start server: {e}", file=sys.stderr)
        print(f"   Port {port} may already be in use", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
