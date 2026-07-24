"""Flask adapter: detection, compatibility warnings, and boot script."""

import json
import re
from pathlib import Path
from typing import ClassVar

from ._shared import ENVELOPE_PY, UNPACK_PY, find_db_files, requirements_warnings

FLASK_PIN = "flask>=3,<4"
ENTRY_MODULES = ("app.py", "main.py", "wsgi.py", "application.py", "run.py")

FLASK_MARKER_RE = re.compile(r"\bFlask\s*\(")
APP_VAR_RE = re.compile(r"^(\w+)\s*=\s*Flask\s*\(", re.M)

FLASK_PY = r"""
import importlib
from flask import Flask


def _load_app(spec):
    mod_name, _, var = spec.partition(":")
    mod = importlib.import_module(mod_name)
    if var:
        obj = getattr(mod, var)
        return obj if isinstance(obj, Flask) else obj()
    for val in vars(mod).values():
        if isinstance(val, Flask):
            return val
    for name in ("create_app", "make_app"):
        factory = getattr(mod, name, None)
        if callable(factory):
            return factory()
    raise RuntimeError("no Flask app found in module " + mod_name)


app = _load_app(APP_SPEC)
app.config["TESTING"] = True
client = app.test_client()


def handle(method, path, form_json):
    try:
        form = json.loads(form_json)
        if method == "POST":
            resp = client.post(path, data=form, follow_redirects=True)
        else:
            resp = client.get(path, query_string=form or None,
                              follow_redirects=True)
        final = resp.request.path
        ctype = resp.headers.get("Content-Type", "text/html")
        return _envelope(resp.status_code, final, ctype, resp.data)
    except Exception:
        return _error(path)
"""

BOOT_PY = UNPACK_PY + ENVELOPE_PY + FLASK_PY


class FlaskAdapter:
    """Detects a Flask project and supplies its Pyodide boot context."""

    name = "flask"
    pyodide_packages: ClassVar[list[str]] = ["micropip", "Jinja2", "sqlite3"]

    def __init__(
        self,
        app_spec: str,
        db_files: list[str],
        warnings: list[str],
    ) -> None:
        """Store detection results.

        Args:
            app_spec: ``module`` or ``module:variable`` locating the app.
            db_files: Relative paths of bundled SQLite database files.
            warnings: Human-readable compatibility warnings.
        """
        self.app_spec = app_spec
        self.db_files = db_files
        self.warnings = warnings
        self.static_url = "/static/"

    @property
    def describe(self) -> str:
        """One-line description of what boots this app."""
        return f"app: {self.app_spec}"

    @classmethod
    def detect(
        cls,
        project: Path,
        files: dict[str, bytes],
        settings_module: str | None = None,
        app_spec: str | None = None,
    ) -> "FlaskAdapter | None":
        """Recognize a Flask project from its collected files.

        Args:
            project: Project root directory.
            files: Collected project files keyed by relative path.
            settings_module: Ignored; accepted for adapter interface parity.
            app_spec: Explicit ``module:variable`` override; when given,
                the module only needs to exist and instantiate Flask.

        Returns:
            An adapter instance, or None if this is not a Flask project.
        """
        if "manage.py" in files:
            return None
        marker = FLASK_MARKER_RE
        if app_spec is not None:
            mod_name = app_spec.partition(":")[0]
            src = files.get(mod_name.replace(".", "/") + ".py", b"")
            if not marker.search(src.decode("utf-8", "replace")):
                return None
            return cls(app_spec, find_db_files(files), requirements_warnings(files))
        for entry in ENTRY_MODULES:
            if entry not in files:
                continue
            src = files[entry].decode("utf-8", "replace")
            if not marker.search(src):
                continue
            module = entry.removesuffix(".py")
            m = APP_VAR_RE.search(src)
            spec = f"{module}:{m.group(1)}" if m else module
            return cls(spec, find_db_files(files), requirements_warnings(files))
        return None

    def template_context(self, pip_pin: str | None = None) -> dict[str, str]:
        """Return template placeholder values for the boot harness.

        Args:
            pip_pin: Override for the framework's pip requirement string
                (default: the built-in Flask pin).

        Returns:
            Mapping of ``__PLACEHOLDER__`` names to replacement strings.
        """
        return {
            "__PIP_INSTALL__": json.dumps([pip_pin or FLASK_PIN]),
            "__PYODIDE_PACKAGES__": json.dumps(self.pyodide_packages),
            "__APP_GLOBALS__": json.dumps(
                {"APP_SPEC": self.app_spec, "STATIC_URL": self.static_url}
            ),
            "__BOOT_PY__": BOOT_PY,
        }
