"""FastAPI adapter: detection, compatibility warnings, and boot script."""

import json
import re
from pathlib import Path
from typing import ClassVar

from ._shared import ENVELOPE_PY, UNPACK_PY, find_db_files, requirements_warnings

# The ceiling exists because Pyodide 0.26.4 ships pydantic 2.7.0 as a
# built package and fastapi >= 0.116 requires pydantic >= 2.9. Raising
# PYODIDE_VERSION is what relaxes this pin.
FASTAPI_PIN = "fastapi>=0.110,<0.116"
MULTIPART_PIN = "python-multipart>=0.0.9"
ENTRY_MODULES = ("main.py", "app.py", "api.py", "application.py", "run.py")

FASTAPI_MARKER_RE = re.compile(r"\bFastAPI\s*\(")
APP_VAR_RE = re.compile(r"^(\w+)\s*=\s*FastAPI\s*\(", re.M)

FASTAPI_PY = r"""
import glob, importlib
from urllib.parse import urlencode, urljoin, urlsplit
from http.cookies import SimpleCookie

import anyio.to_thread


async def _run_sync_inline(func, *args, **kwargs):
    return func(*args)

# Pyodide cannot start threads; run would-be threadpool work inline.
anyio.to_thread.run_sync = _run_sync_inline

from fastapi import FastAPI


def _load_app(spec):
    mod_name, _, var = spec.partition(":")
    mod = importlib.import_module(mod_name)
    if var:
        return getattr(mod, var)
    for val in vars(mod).values():
        if isinstance(val, FastAPI):
            return val
    raise RuntimeError("no FastAPI app found in module " + mod_name)


app = _load_app(APP_SPEC)
COOKIES = {}


def _find_static(rel):
    hits = sorted(glob.glob("/app/**/static/" + rel, recursive=True))
    return hits[0] if hits else None


def _serve_static(path):
    rel = path[len(STATIC_URL):].split("?")[0]
    hit = _find_static(rel)
    if not hit:
        return json.dumps({"status": 404, "path": path, "ctype": "text/plain",
                           "b64": False, "body": "static file not found: " + rel})
    ctype = mimetypes.guess_type(hit)[0] or "application/octet-stream"
    with open(hit, "rb") as f:
        raw = f.read()
    return _envelope(200, path, ctype, raw)


async def _asgi(method, path, body, ctype):
    parts = urlsplit(path)
    headers = [(b"host", b"sharepack.local")]
    if ctype:
        headers.append((b"content-type", ctype.encode()))
    if body:
        headers.append((b"content-length", str(len(body)).encode()))
    if COOKIES:
        raw = "; ".join(k + "=" + v for k, v in COOKIES.items())
        headers.append((b"cookie", raw.encode()))
    scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
             "http_version": "1.1", "method": method, "scheme": "http",
             "path": parts.path, "raw_path": parts.path.encode(),
             "query_string": parts.query.encode(), "root_path": "",
             "headers": headers, "client": ("127.0.0.1", 1234),
             "server": ("sharepack.local", 80)}
    state = {"sent": False}
    out = {"status": 500, "headers": [], "body": b""}

    async def receive():
        if state["sent"]:
            return {"type": "http.disconnect"}
        state["sent"] = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            out["status"] = msg["status"]
            out["headers"] = list(msg.get("headers", []))
        elif msg["type"] == "http.response.body":
            out["body"] += msg.get("body", b"")

    await app(scope, receive, send)
    return out


def _header(headers, name):
    for key, val in headers:
        if key.decode("latin-1").lower() == name:
            return val.decode("latin-1")
    return None


def _store_cookies(headers):
    # Minimal jar: no path/domain/expiry scoping. Enough for sessions
    # inside a single-page demo.
    for key, val in headers:
        if key.decode("latin-1").lower() == "set-cookie":
            jar = SimpleCookie()
            jar.load(val.decode("latin-1"))
            for ck, morsel in jar.items():
                if morsel.value == "" or morsel["max-age"] == "0":
                    COOKIES.pop(ck, None)
                else:
                    COOKIES[ck] = morsel.value


async def handle(method, path, form_json):
    try:
        if path.startswith(STATIC_URL):
            return _serve_static(path)
        form = json.loads(form_json)
        body, ctype = b"", None
        if method == "POST":
            body = urlencode(form, doseq=True).encode()
            ctype = "application/x-www-form-urlencoded"
        elif form:
            sep = "&" if "?" in path else "?"
            path = path + sep + urlencode(form, doseq=True)
        for _ in range(5):
            out = await _asgi(method, path, body, ctype)
            _store_cookies(out["headers"])
            loc = _header(out["headers"], "location")
            if out["status"] in (301, 302, 303, 307, 308) and loc:
                path = urljoin(path, loc)
                if out["status"] not in (307, 308):
                    method, body, ctype = "GET", b"", None
                continue
            break
        rtype = _header(out["headers"], "content-type") or "text/html"
        return _envelope(out["status"], path.split("?")[0], rtype, out["body"])
    except Exception:
        return _error(path)
"""

BOOT_PY = UNPACK_PY + ENVELOPE_PY + FASTAPI_PY


class FastAPIAdapter:
    """Detects a FastAPI project and supplies its Pyodide boot context."""

    name = "fastapi"
    pyodide_packages: ClassVar[list[str]] = [
        "micropip",
        "pydantic",
        "Jinja2",
        "sqlite3",
    ]

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
    ) -> "FastAPIAdapter | None":
        """Recognize a FastAPI project from its collected files.

        Args:
            project: Project root directory.
            files: Collected project files keyed by relative path.
            settings_module: Ignored; accepted for adapter interface parity.
            app_spec: Explicit ``module:variable`` override; when given,
                the module only needs to exist and instantiate FastAPI.

        Returns:
            An adapter instance, or None if this is not a FastAPI project.
        """
        if "manage.py" in files:
            return None
        warnings = [
            "sync (def) endpoints run inline via a patched threadpool; "
            "prefer async def"
        ]
        if app_spec is not None:
            mod_name = app_spec.partition(":")[0]
            src = files.get(mod_name.replace(".", "/") + ".py", b"")
            if not FASTAPI_MARKER_RE.search(src.decode("utf-8", "replace")):
                return None
            return cls(
                app_spec,
                find_db_files(files),
                warnings + requirements_warnings(files),
            )
        for entry in ENTRY_MODULES:
            if entry not in files:
                continue
            src = files[entry].decode("utf-8", "replace")
            if not FASTAPI_MARKER_RE.search(src):
                continue
            module = entry.removesuffix(".py")
            m = APP_VAR_RE.search(src)
            spec = f"{module}:{m.group(1)}" if m else module
            return cls(
                spec,
                find_db_files(files),
                warnings + requirements_warnings(files),
            )
        return None

    def template_context(self, pip_pin: str | None = None) -> dict[str, str]:
        """Return template placeholder values for the boot harness.

        Args:
            pip_pin: Override for the framework's pip requirement string
                (default: the built-in FastAPI pin).

        Returns:
            Mapping of ``__PLACEHOLDER__`` names to replacement strings.
        """
        return {
            "__PIP_INSTALL__": json.dumps([pip_pin or FASTAPI_PIN, MULTIPART_PIN]),
            "__PYODIDE_PACKAGES__": json.dumps(self.pyodide_packages),
            "__APP_GLOBALS__": json.dumps(
                {"APP_SPEC": self.app_spec, "STATIC_URL": self.static_url}
            ),
            "__BOOT_PY__": BOOT_PY,
        }
