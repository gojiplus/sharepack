"""Assemble the single-file HTML artifact."""

import base64
import json
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from .adapters import detect
from .collect import CollectionResult, SkippedFile, collect
from .errors import ProjectError

PYODIDE_VERSION = "0.26.4"
SIZE_WARN_BYTES = 20_000_000


@dataclass(frozen=True)
class BuildResult:
    """Everything a build produced, for reporting or programmatic use.

    Attributes:
        out: Path of the written HTML file.
        adapter_name: Name of the detected framework adapter.
        n_files: Number of files bundled.
        size_bytes: Size of the written HTML file in bytes.
        scrubbed: Messages describing secret scrubbing that took place.
        skipped: Files that were not bundled, with reasons.
        warnings: Compatibility and size warnings.
        db_files: Relative paths of bundled database files.
        db_bytes: Total size of bundled database files in bytes.
    """

    out: Path
    adapter_name: str
    n_files: int
    size_bytes: int
    scrubbed: list[str]
    skipped: list[SkippedFile]
    warnings: list[str]
    db_files: list[str]
    db_bytes: int


def _size_warnings(collection: CollectionResult) -> list[str]:
    """Warn when the bundled payload is uncomfortably large."""
    if collection.total_bytes <= SIZE_WARN_BYTES:
        return []
    total_mb = collection.total_bytes / 1e6
    msg = (
        f"payload is {total_mb:.0f} MB before base64 encoding "
        "(the HTML file will be ~33% larger)"
    )
    if collection.db_bytes > collection.total_bytes / 2:
        msg += (
            f"; database files account for {collection.db_bytes / 1e6:.0f} MB "
            "— consider sharing a trimmed copy of the database"
        )
    return [msg]


def build(
    project: Path,
    out: Path,
    *,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
    settings_module: str | None = None,
    pyodide_version: str = PYODIDE_VERSION,
    pip_pin: str | None = None,
) -> BuildResult:
    """Bundle a project into a single self-contained HTML file.

    Args:
        project: Project root directory (for Django: contains manage.py).
        out: Path of the HTML file to write.
        include: Glob patterns forcing extra files into the bundle.
        exclude: Glob patterns keeping files out of the bundle.
        settings_module: Explicit Django settings module, bypassing
            detection from manage.py.
        pyodide_version: Pyodide release loaded from the CDN at view time.
        pip_pin: Override for the framework's pip requirement string.

    Returns:
        A report of what was built.

    Raises:
        ProjectError: If ``project`` does not exist or is not a directory.

    Note:
        A ``DetectionError`` propagates from framework detection when no
        supported framework is found in ``project``.
    """
    project = Path(project)
    out = Path(out)
    if not project.is_dir():
        raise ProjectError(f"project path is not a directory: {project}")
    collection = collect(project, include=include, exclude=exclude)
    adapter = detect(project, collection.files, settings_module=settings_module)

    payload = {
        rel: base64.b64encode(data).decode() for rel, data in collection.files.items()
    }
    template = (resources.files("sharepack") / "template.html").read_text(
        encoding="utf-8"
    )

    html = template.replace("__TITLE__", project.resolve().name)
    html = html.replace("__PYODIDE_VERSION__", pyodide_version)
    html = html.replace("__FILES_JSON__", json.dumps(payload))
    for key, value in adapter.template_context(pip_pin=pip_pin).items():
        html = html.replace(key, value)
    out.write_text(html, encoding="utf-8")

    return BuildResult(
        out=out,
        adapter_name=adapter.name,
        n_files=len(collection.files),
        size_bytes=out.stat().st_size,
        scrubbed=collection.scrubbed,
        skipped=collection.skipped,
        warnings=adapter.warnings + _size_warnings(collection),
        db_files=adapter.db_files,
        db_bytes=collection.db_bytes,
    )
