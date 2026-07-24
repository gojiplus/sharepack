"""Framework adapters.

Each adapter knows how to detect a framework and supply the template
context that boots it inside Pyodide.
"""

from pathlib import Path

from ..errors import DetectionError
from .django import DjangoAdapter
from .fastapi import FastAPIAdapter
from .flask import FlaskAdapter

AnyAdapter = DjangoAdapter | FlaskAdapter | FastAPIAdapter

ADAPTERS: list[type[AnyAdapter]] = [DjangoAdapter, FlaskAdapter, FastAPIAdapter]


def detect(
    project: Path,
    files: dict[str, bytes],
    settings_module: str | None = None,
    app_spec: str | None = None,
) -> AnyAdapter:
    """Return the first adapter that recognizes the project, or raise.

    Args:
        project: Project root directory.
        files: Collected project files keyed by relative path.
        settings_module: Explicit Django settings module, bypassing
            detection from manage.py.
        app_spec: Explicit ``module:variable`` locating a Flask or
            FastAPI app, bypassing entry-module scanning.

    Returns:
        The adapter instance for the detected framework.

    Raises:
        DetectionError: If no adapter recognizes the project.
    """
    for cls in ADAPTERS:
        adapter = cls.detect(
            project, files, settings_module=settings_module, app_spec=app_spec
        )
        if adapter is not None:
            return adapter
    if "manage.py" in files:
        raise DetectionError(
            f"manage.py found in {project} but no settings module could be "
            "detected from it. Pass --settings-module (e.g. "
            "--settings-module myproject.settings)."
        )
    raise DetectionError(
        f"no supported framework found in {project}. sharepack supports "
        "Django (manage.py at the project root, or --settings-module), "
        "Flask, and FastAPI (an entry module like app.py or main.py that "
        "instantiates the app, or --app module:variable)."
    )
