"""Command-line entry point: sharepack <project_dir> [-o demo.html]"""
import argparse
from pathlib import Path

from .build import build


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sharepack",
        description="Bundle a local Python web app into one demo.html "
                    "that runs entirely in the recipient's browser.")
    ap.add_argument("project", type=Path,
                    help="project root (for Django: contains manage.py)")
    ap.add_argument("-o", "--out", type=Path, default=Path("demo.html"),
                    help="output HTML file (default: demo.html)")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args(argv)
    build(args.project, args.out, quiet=args.quiet)


if __name__ == "__main__":
    main()
