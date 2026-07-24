"""Typed exceptions raised by the sharepack library."""


class SharepackError(Exception):
    """Base class for all sharepack errors."""


class ProjectError(SharepackError):
    """The project path is missing or not a directory."""


class DetectionError(SharepackError):
    """No supported framework could be detected in the project."""
