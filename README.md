# sharepack

[![PyPI](https://img.shields.io/pypi/v/sharepack)](https://pypi.org/project/sharepack/)
[![CI](https://github.com/gojiplus/sharepack/actions/workflows/ci.yml/badge.svg)](https://github.com/gojiplus/sharepack/actions/workflows/ci.yml)
[![Docs](https://github.com/gojiplus/sharepack/actions/workflows/docs.yml/badge.svg)](https://gojiplus.github.io/sharepack/)
[![Python](https://img.shields.io/pypi/pyversions/sharepack)](https://pypi.org/project/sharepack/)

Turn a local Python web app into a **single HTML file** anyone can open.
No server, no tunnel, no deploy, no install on either side.

**[Try the live demo](https://gojiplus.github.io/sharepack/demo.html)** — a
Django app running entirely in your browser tab — then read the
**[docs](https://gojiplus.github.io/sharepack/)**.

```bash
pip install sharepack
sharepack /path/to/your/django/project -o demo.html
```

Send `demo.html` over Slack or email. The recipient double-clicks it.
Python boots in their browser (via [Pyodide](https://pyodide.org)/WebAssembly),
your app runs against a snapshot of your SQLite data, and every click and
form submit is handled entirely inside their tab. Nothing runs on your
machine after the build; nothing installs on theirs.

## Why

The existing ways to show someone your local app all have a catch:

| Approach | Catch |
|---|---|
| ngrok / tunnels | your laptop must stay up; exposes a live server; blocked in many enterprises |
| Railway / Render | repo, config, account; overkill for "look at this" |
| Screen recording | viewer can't touch it |
| "Just clone and run it" | recipient is non-technical |

sharepack converts *running code* into *static content*. The host (email,
Slack, a file share) only ever moves bytes. The recipient executes the app
in the same browser sandbox as any website they visit.

## What works today

Django projects that could, in principle, run on a laptop in airplane mode:

- `manage.py` at the project root (or pass `--settings-module`)
- SQLite (the `.sqlite3` file ships inside the bundle, demo-sized data)
- Pure-Python dependencies (Django itself qualifies)
- Synchronous request/response views, GET + POST forms (multi-value
  fields included)
- `/static/` files — stylesheets, images, fonts — served from the bundle
- Non-HTML responses: JSON pretty-prints, images display, binary
  downloads get a download link

At build time sharepack strips `.env` files and credential-named files,
replaces your `SECRET_KEY` with a throwaway, prints exactly what it
scrubbed and skipped (`--dry-run` shows the full list before you build),
and warns about dependencies that won't survive the trip (psycopg2,
mysqlclient, ...) and about payloads too big to email. At boot it patches
`ALLOWED_HOSTS`, `DEBUG`, and Django's async-context guard so you don't
have to.

## What doesn't (yet or ever)

- **Ever (architecture):** outbound API calls from views, WebSockets,
  Celery/cron, Postgres/MySQL/Redis, shared state between viewers. Each
  recipient gets a private copy; writes persist across clicks, reset on
  reload.
- **Yet (roadmap):** Flask/FastAPI adapters, file uploads, CSS `url(...)`
  rewriting inside stylesheets, vendored offline runtime.

The viewer needs internet on first load: the Pyodide runtime (~10 MB) and
the Django wheel come from public CDNs and are cached by the browser.

## How it works

1. **Collect:** walk the project, keep code + SQLite, scrub secrets.
2. **Detect:** find the framework (adapter architecture; Django today).
3. **Encode:** base64 every file into one JSON payload.
4. **Emit:** splice payload + boot script into an HTML template.

On open, the page loads Pyodide, installs Django via micropip, writes your
files into the WASM virtual filesystem, and routes every link click and
form submit through `django.test.Client` — Django's own request machinery,
repurposed as the transport. The app renders in an iframe. There is no
port, no socket, and no server anywhere.

Prior art this stands on: [WordPress Playground](https://wordpress.github.io/wordpress-playground/)
(the pattern), [stlite](https://github.com/whitphx/stlite) (same idea for
Streamlit), [django_webassembly](https://github.com/m-butterfield/django_webassembly)
(proof of concept this productizes).

## Development

```bash
uv sync --all-groups
uv run pytest
uv run sharepack tests/fixtures_tasktrack -o demo.html --open
npm ci --prefix tests/e2e && node tests/e2e/replay.mjs demo.html
```

The e2e test replays the emitted artifact's exact boot sequence and request
cycle headlessly in Node — it tests the actual product, not a mock. Docs:
`uv run sphinx-build -W -b html docs _site`.

## License

MIT
