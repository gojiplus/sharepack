import webbrowser
from pathlib import Path

import pytest

from sharepack import __version__
from sharepack.cli import main

FIXTURE = Path(__file__).parent / "fixtures_tasktrack"


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert f"sharepack {__version__}" in capsys.readouterr().out


def test_build_report_printed(tmp_path, capsys):
    out = tmp_path / "demo.html"
    main([str(FIXTURE), "-o", str(out)])
    report = capsys.readouterr().out
    assert "files bundled" in report
    assert "framework       : django" in report
    assert out.exists()


def test_quiet_suppresses_report(tmp_path, capsys):
    out = tmp_path / "demo.html"
    main([str(FIXTURE), "-o", str(out), "-q"])
    assert capsys.readouterr().out == ""
    assert out.exists()


def test_dry_run_writes_nothing(tmp_path, capsys):
    out = tmp_path / "demo.html"
    main([str(FIXTURE), "-o", str(out), "--dry-run"])
    output = capsys.readouterr().out
    assert "would bundle" in output
    assert "manage.py" in output
    assert not out.exists()


def test_dry_run_lists_skipped_files(tmp_path, capsys):
    (tmp_path / "manage.py").write_text(
        'import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")'
    )
    (tmp_path / "video.mp4").write_bytes(b"fake")
    main([str(tmp_path), "--dry-run"])
    output = capsys.readouterr().out
    assert "skipped: video.mp4" in output
    assert "--include" in output


def test_non_django_project_exits_1(tmp_path, capsys):
    (tmp_path / "app.py").write_text("x = 1")
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path), "-o", str(tmp_path / "demo.html")])
    assert exc.value.code == 1
    assert "no supported framework" in capsys.readouterr().err


def test_missing_path_exits_1(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "nope"), "-o", str(tmp_path / "demo.html")])
    assert exc.value.code == 1
    assert "not a directory" in capsys.readouterr().err


def test_open_flag_opens_browser(tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url))
    out = tmp_path / "demo.html"
    main([str(FIXTURE), "-o", str(out), "-q", "--open"])
    assert len(opened) == 1
    assert opened[0].startswith("file://")
    assert opened[0].endswith("demo.html")
