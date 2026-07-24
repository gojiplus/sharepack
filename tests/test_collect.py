from pathlib import Path

from sharepack.collect import collect

FIXTURE = Path(__file__).parent / "fixtures_tasktrack"


def test_collect_includes_code_db_and_static():
    result = collect(FIXTURE)
    assert "manage.py" in result.files
    assert "db.sqlite3" in result.files
    assert any(f.endswith("list.html") for f in result.files)
    assert "tasks/static/tasks/extra.css" in result.files


def test_collect_scrubs_secret_key():
    result = collect(FIXTURE)
    settings = result.files["tasktrack/settings.py"].decode()
    assert "sharepack-throwaway-key-not-a-secret" in settings
    assert any("SECRET_KEY replaced" in s for s in result.scrubbed)


def test_collect_skips_pycache(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.py").write_text("cached")
    (tmp_path / "app.py").write_text("real")
    result = collect(tmp_path)
    assert list(result.files) == ["app.py"]


def test_collect_excludes_env_and_credential_files(tmp_path):
    (tmp_path / ".env").write_text("SECRET=1")
    (tmp_path / "aws_credentials.json").write_text("{}")
    (tmp_path / "app.py").write_text("ok")
    result = collect(tmp_path)
    assert list(result.files) == ["app.py"]
    assert len(result.scrubbed) == 2
    reasons = {s.path: s.reason for s in result.skipped}
    assert reasons[".env"] == ".env file"
    assert reasons["aws_credentials.json"] == "credential-named file"


def test_unbundled_extension_recorded_with_reason(tmp_path):
    (tmp_path / "app.py").write_text("ok")
    (tmp_path / "notes.xyz").write_text("mystery")
    result = collect(tmp_path)
    assert "notes.xyz" not in result.files
    skipped = {s.path: s.reason for s in result.skipped}
    assert "--include" in skipped["notes.xyz"]
    assert "'.xyz'" in skipped["notes.xyz"]


def test_include_forces_file_in(tmp_path):
    (tmp_path / "data.xyz").write_text("payload")
    result = collect(tmp_path, include=["*.xyz"])
    assert "data.xyz" in result.files


def test_exclude_wins_over_default_bundling(tmp_path):
    (tmp_path / "app.py").write_text("ok")
    (tmp_path / "secret_math.py").write_text("x = 1")
    result = collect(tmp_path, exclude=["secret_*.py"])
    assert list(result.files) == ["app.py"]
    assert any(
        s.path == "secret_math.py" and "secret_*.py" in s.reason for s in result.skipped
    )


def test_static_extensions_bundled_by_default(tmp_path):
    (tmp_path / "logo.png").write_bytes(b"\x89PNG fake")
    (tmp_path / "font.woff2").write_bytes(b"wOF2 fake")
    result = collect(tmp_path)
    assert set(result.files) == {"logo.png", "font.woff2"}


def test_size_properties(tmp_path):
    (tmp_path / "app.py").write_bytes(b"x" * 100)
    (tmp_path / "db.sqlite3").write_bytes(b"y" * 300)
    result = collect(tmp_path)
    assert result.total_bytes == 400
    assert result.db_bytes == 300
