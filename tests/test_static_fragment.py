"""STATIC_PY, the static-file handler the Django and FastAPI boot scripts share.

The fragment runs inside Pyodide in production; here it runs under CPython
with the same preamble the boot scripts give it.
"""

import base64
import json
import mimetypes
from pathlib import Path
from types import SimpleNamespace

from sharepack.adapters._shared import ENVELOPE_PY, STATIC_PY


def _boot(find_static=None) -> dict:
    ns = {
        "base64": base64,
        "json": json,
        "mimetypes": mimetypes,
        "STATIC_URL": "/static/",
    }
    exec(ENVELOPE_PY + STATIC_PY, ns)  # noqa: S102 - the package's own boot source
    ns["_find_static"] = find_static or ns["_glob_static"]
    return ns


def test_a_found_file_is_returned_in_an_envelope(tmp_path: Path) -> None:
    css = tmp_path / "site.css"
    css.write_text("p { color: red }")
    ns = _boot(lambda rel: str(css) if rel == "site.css" else None)

    out = json.loads(ns["_serve_static"]("/static/site.css?v=3"))

    assert out == {
        "status": 200,
        "path": "/static/site.css?v=3",
        "ctype": "text/css",
        "b64": False,
        "body": "p { color: red }",
    }


def test_a_missing_file_is_a_404(tmp_path: Path) -> None:
    ns = _boot(lambda rel: None)

    out = json.loads(ns["_serve_static"]("/static/gone.js"))

    assert out["status"] == 404
    assert out["body"] == "static file not found: gone.js"


def test_the_fallback_searches_every_static_directory_under_app() -> None:
    ns = _boot()
    seen = []
    ns["glob"] = SimpleNamespace(
        glob=lambda pattern, recursive: (
            seen.append((pattern, recursive))
            or ["/app/b/static/x.css", "/app/a/static/x.css"]
        )
    )

    assert ns["_glob_static"]("x.css") == "/app/a/static/x.css"
    assert seen == [("/app/**/static/x.css", True)]
