"""Assemble the single-file HTML artifact."""
import base64
import json
from importlib import resources
from pathlib import Path

from .adapters import detect
from .collect import collect

PYODIDE_VERSION = "0.26.4"


def build(project: Path, out: Path, quiet: bool = False):
    project = Path(project)
    out = Path(out)
    files, scrubbed = collect(project)
    adapter = detect(project, files)

    payload = {rel: base64.b64encode(data).decode() for rel, data in files.items()}
    template = (resources.files("sharepack") / "template.html").read_text()

    html = template.replace("__TITLE__", project.resolve().name)
    html = html.replace("__PYODIDE_VERSION__", PYODIDE_VERSION)
    html = html.replace("__FILES_JSON__", json.dumps(payload))
    for key, value in adapter.template_context().items():
        html = html.replace(key, value)
    out.write_text(html)

    if not quiet:
        size_mb = out.stat().st_size / 1e6
        n_db = len(adapter.db_files)
        print(f"sharepack: {len(files)} files bundled "
              f"({n_db} database file{'s' if n_db != 1 else ''}) "
              f"-> {out} ({size_mb:.1f} MB)")
        print(f"  framework       : {adapter.name}")
        for s in scrubbed:
            print(f"  scrubbed        : {s}")
        for w in adapter.warnings:
            print(f"  WARNING         : {w}")
        print("  viewer needs    : a browser + internet on first load (CDN runtime)")
        print("  does not travel : outbound API calls, file uploads, compiled deps")
    return out


