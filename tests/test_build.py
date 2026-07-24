import json
import re
from pathlib import Path

import pytest

from sharepack.build import PYODIDE_VERSION, build
from sharepack.errors import ProjectError

FIXTURE = Path(__file__).parent / "fixtures_tasktrack"

# The exact extraction regexes tests/e2e/replay.mjs uses. If a template
# change breaks one of these, the e2e harness breaks with it.
REPLAY_PATTERNS = (
    r"const FILES = (\{.*?\});\n",
    r"const APP_GLOBALS = (\{.*?\});\n",
    r"const PYODIDE_PACKAGES = (\[.*?\]);\n",
    r'const PIP_INSTALL = (".*?");\n',
    r"const BOOT_PY = `\n([\s\S]*?)`;",
)


def test_build_produces_selfcontained_html(tmp_path):
    out = tmp_path / "demo.html"
    result = build(FIXTURE, out)
    html = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    for placeholder in (
        "__FILES_JSON__",
        "__BOOT_PY__",
        "__TITLE__",
        "__PYODIDE_PACKAGES__",
        "__PIP_INSTALL__",
        "__PYODIDE_VERSION__",
    ):
        assert placeholder not in html, f"unreplaced: {placeholder}"
    assert result.out == out
    assert result.adapter_name == "django"
    assert result.n_files > 0
    assert result.size_bytes == out.stat().st_size
    assert result.db_files == ["db.sqlite3"]
    assert result.db_bytes > 0


def test_build_payload_contains_database(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out)
    html = out.read_text(encoding="utf-8")
    m = re.search(r"const FILES = (\{.*?\});\n", html, re.S)
    assert m is not None
    payload = json.loads(m.group(1))
    assert "db.sqlite3" in payload
    assert "DJANGO_ALLOW_ASYNC_UNSAFE" in html


def test_replay_contract(tmp_path):
    """The e2e harness regex-extracts these exact shapes from the HTML."""
    out = tmp_path / "demo.html"
    build(FIXTURE, out)
    html = out.read_text(encoding="utf-8")
    for pattern in REPLAY_PATTERNS:
        assert re.search(pattern, html, re.S), f"replay.mjs contract broken: {pattern}"


def test_boot_py_safe_inside_js_template_literal(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out)
    html = out.read_text(encoding="utf-8")
    boot = re.search(r"const BOOT_PY = `\n([\s\S]*?)`;", html).group(1)
    assert "`" not in boot
    assert "${" not in boot


def test_pyodide_version_override(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out, pyodide_version="0.27.0")
    html = out.read_text(encoding="utf-8")
    assert "pyodide/v0.27.0/full/pyodide.js" in html
    assert f"pyodide/v{PYODIDE_VERSION}" not in html


def test_pip_pin_override(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out, pip_pin="django==5.0.6")
    html = out.read_text(encoding="utf-8")
    assert '"django==5.0.6"' in html


def test_static_url_in_app_globals(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out)
    html = out.read_text(encoding="utf-8")
    m = re.search(r"const APP_GLOBALS = (\{.*?\});\n", html, re.S)
    globals_ = json.loads(m.group(1))
    assert globals_["STATIC_URL"] == "/static/"
    assert globals_["SETTINGS_MODULE"] == "tasktrack.settings"


def test_missing_project_raises_project_error(tmp_path):
    with pytest.raises(ProjectError, match="not a directory"):
        build(tmp_path / "nope", tmp_path / "demo.html")


def test_e2e_pyodide_version_matches():
    """tests/e2e/package.json must pin the same Pyodide as the build."""
    pkg = json.loads(
        (Path(__file__).parent / "e2e" / "package.json").read_text(encoding="utf-8")
    )
    assert pkg["dependencies"]["pyodide"] == PYODIDE_VERSION
