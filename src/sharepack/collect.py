"""Walk a project directory, collect files, scrub secrets."""

import re
from pathlib import Path

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".hg",
    "venv",
    ".venv",
    "env",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
    "htmlcov",
    "dist",
    "build",
    ".eggs",
}
SKIP_FILES = {".env", ".env.local", ".env.production", ".env.development"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log"}
TEXT_EXT = {
    ".py",
    ".html",
    ".txt",
    ".css",
    ".js",
    ".json",
    ".md",
    ".cfg",
    ".ini",
    ".toml",
    ".yaml",
    ".yml",
}
DATA_EXT = {".sqlite3", ".db", ".sqlite"}

SECRET_KEY_RE = re.compile(r"""^(\s*SECRET_KEY\s*=\s*)(['"]).*?\2""", re.M)
CRED_NAME_RE = re.compile(r"(secret|token|password|credential|apikey|api_key)", re.I)


def collect(project: Path):
    """Return ({relative_path: bytes}, [scrub messages])."""
    files, scrubbed = {}, []
    for p in sorted(project.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = str(p.relative_to(project))
        if p.name in SKIP_FILES or (
            CRED_NAME_RE.search(p.name) and p.suffix not in {".py", ".html"}
        ):
            scrubbed.append(f"{rel} (excluded)")
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        if p.suffix.lower() not in TEXT_EXT | DATA_EXT:
            continue
        data = p.read_bytes()
        if p.name == "settings.py":
            text = data.decode("utf-8", "replace")
            if SECRET_KEY_RE.search(text):
                text = SECRET_KEY_RE.sub(
                    r"\1'sharepack-throwaway-key-not-a-secret'", text
                )
                data = text.encode()
                scrubbed.append(f"{rel} (SECRET_KEY replaced)")
        files[rel] = data
    return files, scrubbed
