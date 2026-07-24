"""Walk a project directory, collect files, scrub secrets."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatch
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
STATIC_EXT = {
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".map",
    ".webmanifest",
    ".avif",
}
BUNDLED_EXT = TEXT_EXT | DATA_EXT | STATIC_EXT

SECRET_KEY_RE = re.compile(r"""^(\s*SECRET_KEY\s*=\s*)(['"]).*?\2""", re.M)
CRED_NAME_RE = re.compile(r"(secret|token|password|credential|apikey|api_key)", re.I)


@dataclass(frozen=True)
class SkippedFile:
    """A file that was not bundled, and why."""

    path: str
    reason: str


@dataclass(frozen=True)
class CollectionResult:
    """Everything the collect pass learned about a project.

    Attributes:
        files: Bundled file contents keyed by relative path.
        scrubbed: Messages describing secret scrubbing that took place.
        skipped: Files that were not bundled, with reasons.
    """

    files: dict[str, bytes] = field(default_factory=dict)
    scrubbed: list[str] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        """Total size of all bundled files in bytes."""
        return sum(len(data) for data in self.files.values())

    @property
    def db_bytes(self) -> int:
        """Total size of bundled database files in bytes."""
        return sum(
            len(data)
            for rel, data in self.files.items()
            if Path(rel).suffix.lower() in DATA_EXT
        )


def _matches(rel: str, patterns: Sequence[str]) -> str | None:
    """Return the first glob pattern matching the relative path, if any."""
    for pattern in patterns:
        if fnmatch(rel, pattern):
            return pattern
    return None


def collect(
    project: Path,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> CollectionResult:
    """Collect a project's files for bundling, scrubbing secrets.

    Args:
        project: Project root directory to walk.
        include: Glob patterns (against posix relative paths) that force
            files into the bundle even if their extension is not bundled
            by default. Secret exclusions still apply.
        exclude: Glob patterns that keep files out of the bundle; they
            take precedence over everything else.

    Returns:
        The bundled files plus scrub and skip diagnostics.
    """
    result = CollectionResult()
    for p in sorted(project.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(project).as_posix()
        excluded_by = _matches(rel, exclude)
        if excluded_by:
            result.skipped.append(SkippedFile(rel, f"excluded by '{excluded_by}'"))
            continue
        if p.name in SKIP_FILES:
            result.scrubbed.append(f"{rel} (excluded)")
            result.skipped.append(SkippedFile(rel, ".env file"))
            continue
        if CRED_NAME_RE.search(p.name) and p.suffix not in {".py", ".html"}:
            result.scrubbed.append(f"{rel} (excluded)")
            result.skipped.append(SkippedFile(rel, "credential-named file"))
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        if p.suffix.lower() not in BUNDLED_EXT and not _matches(rel, include):
            result.skipped.append(
                SkippedFile(
                    rel,
                    f"extension '{p.suffix or p.name}' not bundled "
                    "(use --include to force)",
                )
            )
            continue
        data = p.read_bytes()
        if p.name == "settings.py":
            text = data.decode("utf-8", "replace")
            if SECRET_KEY_RE.search(text):
                text = SECRET_KEY_RE.sub(
                    r"\1'sharepack-throwaway-key-not-a-secret'", text
                )
                data = text.encode()
                result.scrubbed.append(f"{rel} (SECRET_KEY replaced)")
        result.files[rel] = data
    return result
