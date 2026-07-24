from pathlib import Path

import pytest

from sharepack.adapters import detect
from sharepack.collect import collect
from sharepack.errors import DetectionError

FIXTURES = Path(__file__).parent
DJANGO_FIXTURE = FIXTURES / "fixtures_tasktrack"
FLASK_FIXTURE = FIXTURES / "fixtures_flaskapp"
FASTAPI_FIXTURE = FIXTURES / "fixtures_fastapiapp"


def test_detect_django():
    result = collect(DJANGO_FIXTURE)
    adapter = detect(DJANGO_FIXTURE, result.files)
    assert adapter.name == "django"
    assert adapter.settings_module == "tasktrack.settings"
    assert adapter.db_files == ["db.sqlite3"]
    assert adapter.describe == "settings: tasktrack.settings"


def test_static_url_normalized_from_relative_setting():
    result = collect(DJANGO_FIXTURE)
    adapter = detect(DJANGO_FIXTURE, result.files)
    assert adapter.static_url == "/static/"


def test_detect_flask_fixture():
    result = collect(FLASK_FIXTURE)
    adapter = detect(FLASK_FIXTURE, result.files)
    assert adapter.name == "flask"
    assert adapter.describe == "app: app:app"
    assert adapter.db_files == ["clips.sqlite3"]


def test_detect_fastapi_fixture():
    result = collect(FASTAPI_FIXTURE)
    adapter = detect(FASTAPI_FIXTURE, result.files)
    assert adapter.name == "fastapi"
    assert adapter.describe == "app: main:app"
    assert any("async def" in w for w in adapter.warnings)


def test_django_wins_over_flask_looking_files(tmp_path):
    (tmp_path / "manage.py").write_text(
        'import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")'
    )
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    result = collect(tmp_path)
    assert detect(tmp_path, result.files).name == "django"


def test_flask_detected_from_entry_module(tmp_path):
    (tmp_path / "app.py").write_text("from flask import Flask\nmyapp = Flask(__name__)")
    result = collect(tmp_path)
    adapter = detect(tmp_path, result.files)
    assert adapter.name == "flask"
    assert adapter.app_spec == "app:myapp"


def test_fastapi_detected_from_entry_module(tmp_path):
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napi = FastAPI()")
    result = collect(tmp_path)
    adapter = detect(tmp_path, result.files)
    assert adapter.name == "fastapi"
    assert adapter.app_spec == "main:api"


def test_app_spec_override_flask(tmp_path):
    (tmp_path / "serve.py").write_text(
        "from flask import Flask\napplication = Flask(__name__)"
    )
    result = collect(tmp_path)
    adapter = detect(tmp_path, result.files, app_spec="serve:application")
    assert adapter.name == "flask"
    assert adapter.app_spec == "serve:application"


def test_app_spec_override_requires_marker(tmp_path):
    (tmp_path / "serve.py").write_text("x = 1")
    result = collect(tmp_path)
    with pytest.raises(DetectionError):
        detect(tmp_path, result.files, app_spec="serve:app")


def test_requirements_alone_do_not_trigger_flask(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask\n")
    (tmp_path / "worker.py").write_text("x = 1")
    result = collect(tmp_path)
    with pytest.raises(DetectionError):
        detect(tmp_path, result.files)


def test_detect_rejects_unrecognized_project(tmp_path):
    (tmp_path / "script.py").write_text("print('hi')")
    result = collect(tmp_path)
    with pytest.raises(DetectionError, match="no supported framework") as exc:
        detect(tmp_path, result.files)
    msg = str(exc.value)
    assert "Django" in msg
    assert "Flask" in msg
    assert "FastAPI" in msg
    assert "--app" in msg


def test_detect_error_mentions_settings_module_flag(tmp_path):
    (tmp_path / "manage.py").write_text("# no settings reference here")
    result = collect(tmp_path)
    with pytest.raises(DetectionError, match="--settings-module"):
        detect(tmp_path, result.files)


def test_settings_module_override_skips_detection(tmp_path):
    (tmp_path / "app_module.py").write_text("x = 1")
    result = collect(tmp_path)
    adapter = detect(tmp_path, result.files, settings_module="conf.settings")
    assert adapter.name == "django"
    assert adapter.settings_module == "conf.settings"
