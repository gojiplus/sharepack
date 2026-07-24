"""Pieces shared by all framework adapters.

Boot scripts run inside Pyodide and are spliced into a JS template
literal, so they must never contain a backtick or "${". Every adapter
composes its BOOT_PY as ``UNPACK_PY + ENVELOPE_PY + <framework part>``;
UNPACK_PY's leading newline is part of the e2e extraction contract.
"""

from pathlib import Path

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

UNPACK_PY = r"""
import base64, json, mimetypes, os, sys
files = json.loads(FILES_JSON)
for rel, b64 in files.items():
    path = "/app/" + rel
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
sys.path.insert(0, "/app")
os.chdir("/app")
"""

ENVELOPE_PY = r"""
TEXT_CTYPES = ("application/json", "application/xml", "application/javascript",
               "application/xhtml+xml")


def _envelope(status, path, ctype, raw):
    main = ctype.split(";")[0].strip().lower()
    textual = (main.startswith("text/") or main in TEXT_CTYPES
               or main.endswith("+json") or main.endswith("+xml"))
    if textual:
        body, b64 = raw.decode("utf-8", "replace"), False
    else:
        body, b64 = base64.b64encode(raw).decode(), True
    return json.dumps({"status": status, "path": path,
                       "ctype": ctype, "b64": b64, "body": body})


def _error(path):
    import traceback
    return json.dumps({"status": 500, "path": path, "ctype": "text/plain",
                       "b64": False, "body": traceback.format_exc()})
"""


def find_db_files(files: dict[str, bytes]) -> list[str]:
    """Return relative paths of bundled database files.

    Args:
        files: Collected project files keyed by relative path.

    Returns:
        Paths whose extension marks them as SQLite databases.
    """
    return [f for f in files if Path(f).suffix.lower() in DATA_EXT]


def requirements_warnings(files: dict[str, bytes]) -> list[str]:
    """Warn about requirements that will not survive the trip to WASM.

    Args:
        files: Collected project files keyed by relative path.

    Returns:
        Human-readable warnings for known-incompatible dependencies.
    """
    reqs = files.get("requirements.txt", b"").decode("utf-8", "replace").lower()
    return [
        f"requirements.txt mentions '{bad}'; compiled deps may not load in WASM"
        for bad in INCOMPATIBLE_DEPS
        if bad in reqs
    ]
