"""Assemble the single-file HTML artifact."""

import base64
import json
from importlib import resources
from pathlib import Path

from .adapters import detect
from .collect import collect

PYODIDE_VERSION = "0.26.4"


def build(project: Path, out: Path, quiet: bool = False) -> Path:
    """Bundle a project into a single self-contained HTML file.

    Args:
        project: Project root directory (for Django: contains manage.py).
        out: Path of the HTML file to write.
        quiet: Suppress the human-readable build report.

    Returns:
        The path of the written HTML file.
    """
    project = Path(project)
    out = Path(out)
    files, scrubbed = collect(project)
    adapter = detect(project, files)

    payload = {rel: base64.b64encode(data).decode() for rel, data in files.items()}
    template = (resources.files("sharepack") / "template.html").read_text(
        encoding="utf-8"
    )

    html = template.replace("__TITLE__", project.resolve().name)
    html = html.replace("__PYODIDE_VERSION__", PYODIDE_VERSION)
    html = html.replace("__FILES_JSON__", json.dumps(payload))
    for key, value in adapter.template_context().items():
        html = html.replace(key, value)
    out.write_text(html, encoding="utf-8")

    if not quiet:
        size_mb = out.stat().st_size / 1e6
        n_db = len(adapter.db_files)
        print(  # noqa: T201
            f"sharepack: {len(files)} files bundled "
            f"({n_db} database file{'s' if n_db != 1 else ''}) "
            f"-> {out} ({size_mb:.1f} MB)"
        )
        print(f"  framework       : {adapter.name}")  # noqa: T201
        for s in scrubbed:
            print(f"  scrubbed        : {s}")  # noqa: T201
        for w in adapter.warnings:
            print(f"  WARNING         : {w}")  # noqa: T201
        print(  # noqa: T201
            "  viewer needs    : a browser + internet on first load (CDN runtime)"
        )
        print(  # noqa: T201
            "  does not travel : outbound API calls, file uploads, compiled deps"
        )
    return out
