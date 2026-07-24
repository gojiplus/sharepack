# sharepack

Turn a local Python web app into a **single HTML file** anyone can open.
No server, no tunnel, no deploy, no install on either side.

```bash
pip install sharepack
sharepack /path/to/your/project -o demo.html
```

Works with **Django, Flask, and FastAPI**. Send `demo.html` over Slack or
email. The recipient double-clicks it. Python boots in their browser via
[Pyodide](https://pyodide.org) (WebAssembly), your app runs against a
snapshot of your SQLite data, and every click and form submit is handled
entirely inside their tab.

<p><strong>Live demos</strong> — each built from a fixture app in sharepack's
test suite, running entirely in your browser:</p>
<ul>
<li><a href="demo.html">▶ Fieldnotes</a> — a Django task ledger</li>
<li><a href="flask-demo.html">▶ Clipnotes</a> — a Flask snippet ledger</li>
<li><a href="fastapi-demo.html">▶ Pulseboard</a> — a FastAPI status board with a JSON API</li>
</ul>

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
