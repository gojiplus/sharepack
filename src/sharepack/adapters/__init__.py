"""Framework adapters. Each adapter knows how to detect a framework and
supply the template context that boots it inside Pyodide."""
from pathlib import Path

from .django import DjangoAdapter

ADAPTERS = [DjangoAdapter]


def detect(project: Path, files: dict):
    """Return the first adapter that recognizes the project, or raise."""
    for cls in ADAPTERS:
        adapter = cls.detect(project, files)
        if adapter is not None:
            return adapter
    raise SystemExit(
        f"error: no supported framework found in {project}. "
        "sharepack v0.1 supports Django projects (manage.py at the root)."
    )
