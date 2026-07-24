# sharepack

Turn a local Python web app into a **single HTML file** anyone can open.
No server, no tunnel, no deploy, no install on either side.

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

## What works today (v0.1)

Django projects that could, in principle, run on a laptop in airplane mode:

- `manage.py` at the project root
- SQLite (the `.sqlite3` file ships inside the bundle, demo-sized data)
- Pure-Python dependencies (Django itself qualifies)
- Synchronous request/response views, GET + POST forms

At build time sharepack strips `.env` files and credential-named files,
replaces your `SECRET_KEY` with a throwaway, prints exactly what it
scrubbed, and warns about dependencies that won't survive the trip
(psycopg2, mysqlclient, ...). At boot it patches `ALLOWED_HOSTS`,
`DEBUG`, and Django's async-context guard so you don't have to.

## What doesn't (yet or ever)

- **Ever (architecture):** outbound API calls from views, WebSockets,
  Celery/cron, Postgres/MySQL/Redis, shared state between viewers. Each
  recipient gets a private copy; writes persist across clicks, reset on
  reload.
- **Yet (roadmap):** Flask/FastAPI adapters, `/static/` routing, binary
  responses (images, downloads), file uploads, vendored offline runtime.

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
pip install -e . pytest
pytest                                    # build-side tests
sharepack tests/fixtures_tasktrack -o /tmp/demo.html
npm install pyodide && node tests/e2e/replay.mjs /tmp/demo.html   # runtime replay
```

The e2e test replays the emitted artifact's exact boot sequence and request
cycle headlessly in Node — it tests the actual product, not a mock.

## License

MIT
