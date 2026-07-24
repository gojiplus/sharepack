from pathlib import Path

import pytest

from sharepack.adapters import detect
from sharepack.collect import collect
from sharepack.errors import DetectionError

FIXTURE = Path(__file__).parent / "fixtures_tasktrack"


def test_detect_django():
    result = collect(FIXTURE)
    adapter = detect(FIXTURE, result.files)
    assert adapter.name == "django"
    assert adapter.settings_module == "tasktrack.settings"
    assert adapter.db_files == ["db.sqlite3"]


def test_static_url_normalized_from_relative_setting():
    result = collect(FIXTURE)
    adapter = detect(FIXTURE, result.files)
    assert adapter.static_url == "/static/"


def test_detect_rejects_non_django(tmp_path):
    (tmp_path / "app.py").write_text("print('hi')")
    result = collect(tmp_path)
    with pytest.raises(DetectionError, match="no supported framework"):
        detect(tmp_path, result.files)


def test_detect_error_mentions_settings_module_flag(tmp_path):
    (tmp_path / "manage.py").write_text("# no settings reference here")
    result = collect(tmp_path)
    with pytest.raises(DetectionError, match="--settings-module"):
        detect(tmp_path, result.files)


def test_settings_module_override_skips_detection(tmp_path):
    (tmp_path / "app.py").write_text("x = 1")
    result = collect(tmp_path)
    adapter = detect(tmp_path, result.files, settings_module="conf.settings")
    assert adapter.name == "django"
    assert adapter.settings_module == "conf.settings"
