# sharepack

Turn a local Python web app into a **single HTML file** anyone can open.
No server, no tunnel, no deploy, no install on either side.

```bash
pip install sharepack
sharepack /path/to/your/django/project -o demo.html
```

Send `demo.html` over Slack or email. The recipient double-clicks it. Python
boots in their browser via [Pyodide](https://pyodide.org) (WebAssembly), your
app runs against a snapshot of your SQLite data, and every click and form
submit is handled entirely inside their tab.

<p><strong><a href="demo.html">▶ Open the live demo</a></strong> — a Django
task ledger running entirely in your browser, built from the example app that
ships in sharepack's test suite.</p>

## Why

The existing ways to show someone your local app all have a catch:

| Approach | Catch |
|---|---|
| ngrok / tunnels | your laptop must stay up; exposes a live server |
| Railway / Render | repo, config, account; overkill for "look at this" |
| Screen recording | viewer can't touch it |
| "Just clone and run it" | recipient is non-technical |

sharepack converts *running code* into *static content*. The host (email,
Slack, a file share) only ever moves bytes. The recipient executes the app in
the same browser sandbox as any website they visit.

```{toctree}
:maxdepth: 2

quickstart
how-it-works
cli
api
limitations
changelog
```
