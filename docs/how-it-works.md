# How it works

sharepack is a four-stage build pipeline plus a small browser runtime.

## The pipeline

1. **Collect** — walk the project directory. Source, templates, config,
   static assets (images, fonts, stylesheets), and SQLite databases are kept;
   caches, virtualenvs, logs, and VCS directories are ignored. Secrets are
   scrubbed (below). Everything kept is read as bytes.
2. **Detect** — find the framework. The Django adapter looks for `manage.py`
   and reads the settings module out of it (`--settings-module` overrides
   this). It also parses `STATIC_URL`, spots incompatible dependencies in
   `requirements.txt`, and warns about non-SQLite database backends.
3. **Encode** — base64 every file into one JSON payload.
4. **Emit** — splice the payload, a Python boot script, and framework
   metadata into an HTML template. The output is one self-contained file.

## What gets scrubbed and skipped

At build time, before anything is embedded:

- `.env`, `.env.local`, `.env.production`, `.env.development` are excluded.
- Files whose *names* look credential-like (`secret`, `token`, `password`,
  `credential`, `apikey`, `api_key`) are excluded, unless they are `.py` or
  `.html` source files.
- `SECRET_KEY = "..."` in `settings.py` is replaced with a throwaway value.
- Files with extensions sharepack doesn't recognize are skipped **and
  reported** — run `--dry-run` to see the full list with reasons, and use
  `--include`/`--exclude` globs to adjust.

Every scrub and skip is printed in the build report. Nothing is silently
dropped.

## The browser runtime

When the recipient opens the file:

1. The page loads the Pyodide runtime (~10 MB, cached by the browser) from
   the jsDelivr CDN and installs Django with micropip from PyPI. This is the
   only time the network is used.
2. The boot script writes every bundled file into the WASM virtual
   filesystem at `/app/`, calls `django.setup()`, and creates a
   `django.test.Client` — Django's own request machinery, repurposed as the
   transport.
3. Every link click and form submit is intercepted in JavaScript and routed
   through that client. The response HTML is rendered into an iframe.
   There is no port, no socket, and no server anywhere.

### Static files

References to `STATIC_URL` paths in rendered HTML (`<link href="/static/…">`,
`<img src="/static/…">`, script tags) are resolved through Django's
staticfiles finders inside the WASM filesystem, converted to blob URLs, and
rewritten before the page is displayed. Stylesheets, images, and fonts work
without `collectstatic`.

### Content types

Responses are dispatched on their content type: HTML renders normally, JSON
pretty-prints, plain text renders as text, images display, and anything
binary becomes a download link.

## Honest caveats

The artifact is a **demo**, not a deployment:

- CSRF checks are disabled and `DEBUG = True` is forced at boot, so form
  posts work and errors are readable. Never treat the bundle as a hardened
  build of your app.
- Anyone who has the file has your bundled code and data. The scrubber
  removes obvious secrets, but review `--dry-run` output before sharing
  something sensitive.
- Each recipient gets a private copy. Writes persist across clicks but reset
  on reload; viewers never see each other's changes.

## Prior art

[WordPress Playground](https://wordpress.github.io/wordpress-playground/)
(the pattern), [stlite](https://github.com/whitphx/stlite) (same idea for
Streamlit), and
[django_webassembly](https://github.com/m-butterfield/django_webassembly)
(the proof of concept this productizes).
