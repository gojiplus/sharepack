"""Command-line entry point: sharepack <project_dir> [-o demo.html]."""

import argparse
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .adapters import detect
from .build import PYODIDE_VERSION, BuildResult, build
from .collect import collect
from .errors import ProjectError, SharepackError


def _parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    ap = argparse.ArgumentParser(
        prog="sharepack",
        description="Bundle a local Python web app into one demo.html "
        "that runs entirely in the recipient's browser.",
    )
    ap.add_argument(
        "project",
        type=Path,
        help="project root (for Django: contains manage.py)",
    )
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("demo.html"),
        help="output HTML file (default: demo.html)",
    )
    ap.add_argument(
        "-q", "--quiet", action="store_true", help="suppress the build report"
    )
    ap.add_argument(
        "-V", "--version", action="version", version=f"sharepack {__version__}"
    )
    ap.add_argument(
        "--open",
        action="store_true",
        help="open the built file in your browser",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would be bundled, scrubbed, and skipped; write nothing",
    )
    ap.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="GLOB",
        help="bundle files matching this glob even if their extension is "
        "not bundled by default (repeatable)",
    )
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="keep files matching this glob out of the bundle (repeatable)",
    )
    ap.add_argument(
        "--settings-module",
        metavar="DOTTED.PATH",
        help="Django settings module, if detection from manage.py fails",
    )
    ap.add_argument(
        "--pyodide-version",
        default=PYODIDE_VERSION,
        metavar="X.Y.Z",
        help=f"Pyodide release loaded from the CDN (default: {PYODIDE_VERSION})",
    )
    ap.add_argument(
        "--django-pin",
        metavar="SPEC",
        help='pip requirement for the framework (default: "django>=4.2,<5.2")',
    )
    return ap


def _dry_run(args: argparse.Namespace) -> None:
    """Print what a build would bundle, without writing anything."""
    if not args.project.is_dir():
        raise ProjectError(f"project path is not a directory: {args.project}")
    collection = collect(args.project, include=args.include, exclude=args.exclude)
    adapter = detect(
        args.project, collection.files, settings_module=args.settings_module
    )
    print(f"sharepack --dry-run: {args.project}")
    print(f"  framework: {adapter.name} (settings: {adapter.settings_module})")
    print(
        f"  would bundle {len(collection.files)} files "
        f"({collection.total_bytes / 1e6:.1f} MB before base64):"
    )
    for rel, data in collection.files.items():
        print(f"    {rel} ({len(data):,} bytes)")
    for s in collection.scrubbed:
        print(f"  scrubbed: {s}")
    for sk in collection.skipped:
        print(f"  skipped: {sk.path} — {sk.reason}")
    for w in adapter.warnings:
        print(f"  WARNING: {w}")


def _report(result: BuildResult) -> None:
    """Print the human-readable build report."""
    size_mb = result.size_bytes / 1e6
    n_db = len(result.db_files)
    print(
        f"sharepack: {result.n_files} files bundled "
        f"({n_db} database file{'s' if n_db != 1 else ''}) "
        f"-> {result.out} ({size_mb:.1f} MB)"
    )
    print(f"  framework       : {result.adapter_name}")
    for s in result.scrubbed:
        print(f"  scrubbed        : {s}")
    if result.skipped:
        print(
            f"  skipped         : {len(result.skipped)} file"
            f"{'s' if len(result.skipped) != 1 else ''} not bundled "
            "(--dry-run lists them)"
        )
    for w in result.warnings:
        print(f"  WARNING         : {w}")
    print("  viewer needs    : a browser + internet on first load (CDN runtime)")
    print("  does not travel : outbound API calls, file uploads, compiled deps")


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and build the single-file demo.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.
    """
    args = _parser().parse_args(argv)
    try:
        if args.dry_run:
            _dry_run(args)
            return
        result = build(
            args.project,
            args.out,
            include=args.include,
            exclude=args.exclude,
            settings_module=args.settings_module,
            pyodide_version=args.pyodide_version,
            pip_pin=args.django_pin,
        )
    except SharepackError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    if not args.quiet:
        _report(result)
    if args.open:
        webbrowser.open(result.out.resolve().as_uri())


if __name__ == "__main__":
    main()
