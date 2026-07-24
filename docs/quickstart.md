# Quickstart

## Install

```bash
pip install sharepack
```

sharepack has no runtime dependencies — it is a build tool that emits one
HTML file. Python 3.11+.

## Bundle your project

Point sharepack at your project root — it detects Django, Flask, or FastAPI:

```bash
sharepack /path/to/your/project -o demo.html
```

- **Django**: the directory containing `manage.py`. If your settings module
  can't be read out of `manage.py`, pass `--settings-module myproj.settings`.
- **Flask / FastAPI**: an entry module at the root (`app.py`, `main.py`,
  `wsgi.py`, …) that instantiates the app. If detection fails — a factory
  pattern, an unusual filename — pass `--app module:variable` (the same
  syntax gunicorn and uvicorn use).

The report tells you exactly what happened:

```text
sharepack: 20 files bundled (1 database file) -> demo.html (0.2 MB)
  framework       : django
  scrubbed        : tasktrack/settings.py (SECRET_KEY replaced)
  viewer needs    : a browser + internet on first load (CDN runtime)
  does not travel : outbound API calls, file uploads, compiled deps
```

Open the result yourself before sending it:

```bash
sharepack /path/to/your/project -o demo.html --open
```

## Preview before you build

`--dry-run` lists every file that would be bundled, everything that was
scrubbed, and every file that was skipped (with the reason) — without
writing anything:

```bash
sharepack /path/to/your/project --dry-run
```

If something you need was skipped (say, a `.csv` your view reads), force it
in with a glob:

```bash
sharepack /path/to/your/project --include "data/*.csv" -o demo.html
```

And keep things out the same way:

```bash
sharepack /path/to/your/project --exclude "docs/*" -o demo.html
```

## Complete worked examples

The repository ships one fixture app per framework, used by the test suite
and behind the live demos on this site:

```bash
git clone https://github.com/gojiplus/sharepack
cd sharepack
pip install -e .
sharepack tests/fixtures_tasktrack  -o demo.html --open          # Django
sharepack tests/fixtures_flaskapp   -o flask-demo.html --open    # Flask
sharepack tests/fixtures_fastapiapp -o fastapi-demo.html --open  # FastAPI
```

Your browser opens a page that boots Python (~10 MB download on first load,
then cached), installs the framework, and renders the app. Add a row, follow
links, submit forms — every interaction runs inside your tab. Reload the
page and the data resets to the snapshot.

## What your project needs

- A recognizable entry point: `manage.py` (Django) or an entry module that
  instantiates the app (Flask/FastAPI) — or the matching override flag
- SQLite, if it uses a database — the `.sqlite3` file ships inside the bundle
- Pure-Python dependencies (Django, Flask, and FastAPI all qualify)
- Request/response views; GET and POST forms both work. FastAPI endpoints
  should prefer `async def` — sync `def` endpoints run, but execute inline
  on the event loop (there are no threads in WebAssembly)

See {doc}`limitations` for what does not travel.
