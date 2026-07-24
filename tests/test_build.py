import json
import re
from pathlib import Path

import pytest

from sharepack.build import build
from sharepack.collect import collect
from sharepack.adapters import detect

FIXTURE = Path(__file__).parent / "fixtures_tasktrack"


def test_collect_includes_code_and_db():
    files, _ = collect(FIXTURE)
    assert "manage.py" in files
    assert "db.sqlite3" in files
    assert any(f.endswith("list.html") for f in files)


def test_collect_scrubs_secret_key():
    files, scrubbed = collect(FIXTURE)
    settings = files["tasktrack/settings.py"].decode()
    assert "sharepack-throwaway-key-not-a-secret" in settings
    assert any("SECRET_KEY replaced" in s for s in scrubbed)


def test_collect_skips_pycache(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.py").write_text("cached")
    (tmp_path / "app.py").write_text("real")
    files, _ = collect(tmp_path)
    assert list(files) == ["app.py"]


def test_collect_excludes_env_and_credential_files(tmp_path):
    (tmp_path / ".env").write_text("SECRET=1")
    (tmp_path / "aws_credentials.json").write_text("{}")
    (tmp_path / "app.py").write_text("ok")
    files, scrubbed = collect(tmp_path)
    assert list(files) == ["app.py"]
    assert len(scrubbed) == 2


def test_detect_django():
    files, _ = collect(FIXTURE)
    adapter = detect(FIXTURE, files)
    assert adapter.name == "django"
    assert adapter.settings_module == "tasktrack.settings"
    assert adapter.db_files == ["db.sqlite3"]


def test_detect_rejects_non_django(tmp_path):
    (tmp_path / "app.py").write_text("print('hi')")
    files, _ = collect(tmp_path)
    with pytest.raises(SystemExit):
        detect(tmp_path, files)


def test_build_produces_selfcontained_html(tmp_path):
    out = tmp_path / "demo.html"
    build(FIXTURE, out, quiet=True)
    html = out.read_text()
    assert "<!DOCTYPE html>" in html
    for placeholder in ("__FILES_JSON__", "__BOOT_PY__", "__TITLE__",
                        "__PYODIDE_PACKAGES__", "__PIP_INSTALL__"):
        assert placeholder not in html, f"unreplaced: {placeholder}"
    m = re.search(r"const FILES = (\{.*?\});\n", html, re.S)
    payload = json.loads(m.group(1))
    assert "db.sqlite3" in payload
    assert "sqlite3" in html and "tzdata" in html
    assert "DJANGO_ALLOW_ASYNC_UNSAFE" in html
