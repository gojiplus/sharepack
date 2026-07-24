# Limitations & FAQ

## Architectural — will not work, by design

The whole app runs inside the recipient's browser tab. Anything that needs
the outside world, or another process, does not travel:

- **Outbound network calls from views** (payment APIs, external services).
- **WebSockets, Celery, cron** — there is no second process.
- **Postgres / MySQL / Redis** — only the bundled SQLite snapshot exists.
- **Shared state between viewers** — each recipient gets a private copy;
  writes persist across clicks and reset on reload.
- **Compiled dependencies** not built for WASM (psycopg2, mysqlclient, …).
  The build warns when it spots these in `requirements.txt`.

## Current gaps — may improve in future releases

- **File uploads** — file inputs are ignored on submit.
- **CSS `url(...)` references** — stylesheets are served and `<link>`,
  `<img>`, and `<script>` static references are rewritten, but URLs *inside*
  CSS files (background images, font faces) are not yet rewritten.
- **Browser history** — the back button navigates the outer page, not the
  app; routing happens inside a single iframe.
- **Only Django** — the adapter registry is designed for more frameworks
  (Flask and FastAPI are natural next steps), but Django is the only adapter
  today.

## FAQ

**Does the viewer need to install anything?**
No. A browser and internet on first load: the Pyodide runtime (~10 MB) and
the Django wheel come from public CDNs and are cached by the browser.

**Is my data safe to share?**
The file contains your code and your SQLite snapshot, readable by anyone
who has it. The scrubber removes `.env` files, credential-named files, and
`SECRET_KEY`, and reports everything it did — but you are shipping your
data. Run `--dry-run` and look before you send.

**Why does the demo say CSRF is disabled?**
Form posts inside the artifact go through Django's test client with CSRF
enforcement off and `DEBUG = True`, so the demo is friction-free and errors
are readable. The artifact is a demo, not a deployment.

**The artifact loads Pyodide from a CDN — what about integrity?**
The `<script>` tag carries no Subresource Integrity hash: the Pyodide
version is configurable at build time (`--pyodide-version`), and Pyodide
itself fetches further assets (the WASM binary, wheels) dynamically, which
SRI cannot cover. If your threat model requires it, pin a version, add an
`integrity` attribute to the emitted HTML, and host the runtime yourself.

**How big can my app be?**
Every bundled byte becomes ~1.33 bytes of base64 in the HTML. sharepack
warns when the payload exceeds 20 MB — a 50 MB dev database makes a ~67 MB
HTML file that mail servers will bounce. Share a trimmed database.
