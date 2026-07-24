"""Django adapter: detection, compatibility warnings, and boot script."""

import json
import re
from pathlib import Path
from typing import ClassVar

from ._shared import ENVELOPE_PY, UNPACK_PY, find_db_files, requirements_warnings

DJANGO_PIN = "django>=4.2,<5.2"

SETTINGS_MODULE_RE = re.compile(r"""['"]([\w.]+\.settings[\w.]*)['"]""")
STATIC_URL_RE = re.compile(r"""^\s*STATIC_URL\s*=\s*['"]([^'"]+)['"]""", re.M)

DJANGO_PY = r"""
os.environ["DJANGO_SETTINGS_MODULE"] = SETTINGS_MODULE
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
from django.conf import settings
django.setup()
settings.ALLOWED_HOSTS = ["*"]
settings.DEBUG = True
if not getattr(settings, "SECRET_KEY", None):
    settings.SECRET_KEY = "sharepack-throwaway"

from django.test import Client
client = Client(enforce_csrf_checks=False)


def _find_static(rel):
    try:
        from django.contrib.staticfiles import finders
        hit = finders.find(rel)
        if hit:
            return hit
    except Exception:
        pass
    import glob
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


def handle(method, path, form_json):
    try:
        if path.startswith(STATIC_URL):
            return _serve_static(path)
        form = json.loads(form_json)
        if method == "POST":
            resp = client.post(path, form, follow=True)
        else:
            resp = client.get(path, form or None, follow=True)
        final = resp.redirect_chain[-1][0] if resp.redirect_chain else path
        ctype = resp.headers.get("Content-Type", "text/html")
        return _envelope(resp.status_code, final, ctype, resp.content)
    except Exception:
        return _error(path)
"""

BOOT_PY = UNPACK_PY + ENVELOPE_PY + DJANGO_PY


class DjangoAdapter:
    """Detects a Django project and supplies its Pyodide boot context."""

    name = "django"
    pyodide_packages: ClassVar[list[str]] = ["micropip", "sqlite3", "tzdata"]

    def __init__(
        self,
        settings_module: str,
        db_files: list[str],
        warnings: list[str],
        static_url: str = "/static/",
    ) -> None:
        """Store detection results.

        Args:
            settings_module: Dotted path of the Django settings module.
            db_files: Relative paths of bundled SQLite database files.
            warnings: Human-readable compatibility warnings.
            static_url: The project's STATIC_URL, normalized to have
                leading and trailing slashes.
        """
        self.settings_module = settings_module
        self.db_files = db_files
        self.warnings = warnings
        self.static_url = static_url

    @property
    def describe(self) -> str:
        """One-line description of what boots this app."""
        return f"settings: {self.settings_module}"

    @classmethod
    def detect(
        cls,
        project: Path,
        files: dict[str, bytes],
        settings_module: str | None = None,
        app_spec: str | None = None,
    ) -> "DjangoAdapter | None":
        """Recognize a Django project from its collected files.

        Args:
            project: Project root directory.
            files: Collected project files keyed by relative path.
            settings_module: Explicit settings module; when given,
                detection from manage.py is skipped.
            app_spec: Ignored; accepted for adapter interface parity.

        Returns:
            An adapter instance, or None if this is not a Django project.
        """
        if settings_module is None:
            if "manage.py" not in files:
                return None
            m = SETTINGS_MODULE_RE.search(files["manage.py"].decode("utf-8", "replace"))
            if not m:
                return None
            settings_module = str(m.group(1))
        settings_rel = settings_module.replace(".", "/") + ".py"
        settings_src = files.get(settings_rel, b"").decode("utf-8", "replace")

        static_url = "/static/"
        sm = STATIC_URL_RE.search(settings_src)
        if sm:
            static_url = sm.group(1)
            if not static_url.startswith("/"):
                static_url = "/" + static_url
            if not static_url.endswith("/"):
                static_url += "/"

        warnings = []
        if re.search(r"postgresql|mysql|oracle", settings_src):
            warnings.append(
                "non-SQLite database backend in settings; sharepack only ships SQLite"
            )
        warnings += requirements_warnings(files)
        db = find_db_files(files)
        if not db:
            warnings.append(
                "no SQLite file found; app must work with an empty/no database"
            )
        return cls(settings_module, db, warnings, static_url)

    def template_context(self, pip_pin: str | None = None) -> dict[str, str]:
        """Return template placeholder values for the boot harness.

        Args:
            pip_pin: Override for the framework's pip requirement string
                (default: the built-in Django pin).

        Returns:
            Mapping of ``__PLACEHOLDER__`` names to replacement strings.
        """
        return {
            "__PIP_INSTALL__": json.dumps([pip_pin or DJANGO_PIN]),
            "__PYODIDE_PACKAGES__": json.dumps(self.pyodide_packages),
            "__APP_GLOBALS__": json.dumps(
                {
                    "SETTINGS_MODULE": self.settings_module,
                    "STATIC_URL": self.static_url,
                }
            ),
            "__BOOT_PY__": BOOT_PY,
        }
