"""Django adapter: detection, compatibility warnings, and boot script."""

import json
import re
from pathlib import Path
from typing import ClassVar

DJANGO_PIN = "django>=4.2,<5.2"
DATA_EXT = {".sqlite3", ".db", ".sqlite"}
INCOMPATIBLE_DEPS = (
    "psycopg",
    "mysqlclient",
    "lxml",
    "cryptography",
    "uwsgi",
    "gunicorn-native",
    "grpcio",
)

BOOT_PY = r"""
import base64, json, os, sys
files = json.loads(FILES_JSON)
for rel, b64 in files.items():
    path = "/app/" + rel
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
sys.path.insert(0, "/app")
os.chdir("/app")
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

def handle(method, path, form_json):
    try:
        if method == "POST":
            resp = client.post(path, json.loads(form_json), follow=True)
        else:
            resp = client.get(path, follow=True)
        final = resp.redirect_chain[-1][0] if resp.redirect_chain else path
        ctype = resp.headers.get("Content-Type", "text/html")
        body = resp.content.decode("utf-8", "replace")
        return json.dumps({"status": resp.status_code, "path": final,
                           "ctype": ctype, "body": body})
    except Exception:
        import traceback
        return json.dumps({"status": 500, "path": path, "ctype": "text/plain",
                           "body": traceback.format_exc()})
"""


class DjangoAdapter:
    """Detects a Django project and supplies its Pyodide boot context."""

    name = "django"
    pyodide_packages: ClassVar[list[str]] = ["micropip", "sqlite3", "tzdata"]

    def __init__(
        self,
        settings_module: str,
        db_files: list[str],
        warnings: list[str],
    ) -> None:
        """Store detection results.

        Args:
            settings_module: Dotted path of the Django settings module.
            db_files: Relative paths of bundled SQLite database files.
            warnings: Human-readable compatibility warnings.
        """
        self.settings_module = settings_module
        self.db_files = db_files
        self.warnings = warnings

    @classmethod
    def detect(cls, project: Path, files: dict[str, bytes]) -> "DjangoAdapter | None":
        """Recognize a Django project from its collected files.

        Args:
            project: Project root directory.
            files: Collected project files keyed by relative path.

        Returns:
            An adapter instance, or None if this is not a Django project.
        """
        if "manage.py" not in files:
            return None
        m = re.search(
            r"""['"]([\w.]+\.settings[\w.]*)['"]""",
            files["manage.py"].decode("utf-8", "replace"),
        )
        if not m:
            return None
        settings_module = m.group(1)
        settings_rel = settings_module.replace(".", "/") + ".py"
        settings_src = files.get(settings_rel, b"").decode("utf-8", "replace")

        warnings = []
        if re.search(r"postgresql|mysql|oracle", settings_src):
            warnings.append(
                "non-SQLite database backend in settings; sharepack only ships SQLite"
            )
        reqs = files.get("requirements.txt", b"").decode("utf-8", "replace").lower()
        for bad in INCOMPATIBLE_DEPS:
            if bad in reqs:
                warnings.append(
                    f"requirements.txt mentions '{bad}'; "
                    "compiled deps may not load in WASM"
                )
        db = [f for f in files if Path(f).suffix.lower() in DATA_EXT]
        if not db:
            warnings.append(
                "no SQLite file found; app must work with an empty/no database"
            )
        return cls(settings_module, db, warnings)

    def template_context(self) -> dict[str, str]:
        """Return template placeholder values for the boot harness.

        Returns:
            Mapping of ``__PLACEHOLDER__`` names to replacement strings.
        """
        return {
            "__PIP_INSTALL__": json.dumps(DJANGO_PIN),
            "__PYODIDE_PACKAGES__": json.dumps(self.pyodide_packages),
            "__APP_GLOBALS__": json.dumps({"SETTINGS_MODULE": self.settings_module}),
            "__BOOT_PY__": BOOT_PY,
        }
