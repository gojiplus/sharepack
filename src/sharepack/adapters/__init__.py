"""Framework adapters.

Each adapter knows how to detect a framework and supply the template
context that boots it inside Pyodide.
"""

from pathlib import Path

from ..errors import DetectionError
from .django import DjangoAdapter

ADAPTERS = [DjangoAdapter]


def detect(
    project: Path,
    files: dict[str, bytes],
    settings_module: str | None = None,
) -> DjangoAdapter:
    """Return the first adapter that recognizes the project, or raise.

    Args:
        project: Project root directory.
        files: Collected project files keyed by relative path.
        settings_module: Explicit Django settings module, bypassing
            detection from manage.py.

    Returns:
        The adapter instance for the detected framework.

    Raises:
        DetectionError: If no adapter recognizes the project.
    """
    for cls in ADAPTERS:
        adapter = cls.detect(project, files, settings_module=settings_module)
        if adapter is not None:
            return adapter
    if "manage.py" in files:
        raise DetectionError(
            f"manage.py found in {project} but no settings module could be "
            "detected from it. Pass --settings-module (e.g. "
            "--settings-module myproject.settings)."
        )
    raise DetectionError(
        f"no supported framework found in {project}. sharepack currently "
        "supports Django projects (manage.py at the project root)."
    )
