# Quickstart

## Install

```bash
pip install sharepack
```

sharepack has no runtime dependencies — it is a build tool that emits one
HTML file. Python 3.11+.

## Bundle your Django project

From anywhere, point sharepack at the directory containing `manage.py`:

```bash
sharepack /path/to/your/project -o demo.html
```

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

## A complete worked example

The repository ships a small Django app — *Fieldnotes*, a task ledger with a
pre-seeded SQLite database — used by the test suite. It is also the app
behind the <a href="demo.html">live demo</a> on this site.

```bash
git clone https://github.com/gojiplus/sharepack
cd sharepack
pip install -e .
sharepack tests/fixtures_tasktrack -o demo.html --open
```

Your browser opens a page that boots Python (~10 MB download on first load,
then cached), installs Django, and renders the task list. Add a task, toggle
it, delete it — every interaction runs inside your tab. Reload the page and
the data resets to the snapshot.

## What your project needs

- `manage.py` at the project root (or pass `--settings-module` explicitly)
- SQLite, if it uses a database — the `.sqlite3` file ships inside the bundle
- Pure-Python dependencies (Django itself qualifies)
- Synchronous request/response views; GET and POST forms both work

See {doc}`limitations` for what does not travel.
