"""sharepack: turn a local Python web app into a single shareable HTML file."""

from importlib.metadata import PackageNotFoundError, version

from .build import BuildResult, build
from .collect import CollectionResult, SkippedFile, collect
from .errors import DetectionError, ProjectError, SharepackError

try:
    __version__ = version("sharepack")
except PackageNotFoundError:  # pragma: no cover - not installed
    __version__ = "0.0.0"

__all__ = [
    "BuildResult",
    "CollectionResult",
    "DetectionError",
    "ProjectError",
    "SharepackError",
    "SkippedFile",
    "__version__",
    "build",
    "collect",
]
