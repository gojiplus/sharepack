# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Django project → single self-contained `demo.html` running on Pyodide in the
  recipient's browser (collect → detect → encode → emit pipeline).
- Secret scrubbing: `.env` and credential-named files excluded, `SECRET_KEY`
  replaced with a throwaway value.
- `/static/` file serving inside the demo (stylesheets, images, fonts).
- Content-type-aware rendering: HTML, JSON, plain text, images, and binary
  downloads all display correctly.
- CLI: `--version`, `--open`, `--dry-run`, `--include`/`--exclude`,
  `--settings-module`, `--pyodide-version`, `--django-pin`.
- Typed exceptions (`SharepackError`, `ProjectError`, `DetectionError`) for
  programmatic use.
- Collection diagnostics: skipped files reported with reasons; size warning
  for payloads over 20 MB.
- Sphinx/furo documentation with a live demo published to GitHub Pages.
