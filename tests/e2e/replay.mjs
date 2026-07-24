// E2E: replay the emitted artifact's exact boot + request cycle headlessly.
// Usage: node replay.mjs path/to/demo.html
import { loadPyodide } from "pyodide";
import { readFileSync } from "fs";

const html = readFileSync(process.argv[2], "utf8");
const FILES = JSON.parse(html.match(/const FILES = (\{.*?\});\n/s)[1]);
const APP_GLOBALS = JSON.parse(html.match(/const APP_GLOBALS = (\{.*?\});\n/s)[1]);
const PKGS = JSON.parse(html.match(/const PYODIDE_PACKAGES = (\[.*?\]);\n/s)[1]);
const PIP = JSON.parse(html.match(/const PIP_INSTALL = (".*?");\n/s)[1]);
const BOOT_PY = html.match(/const BOOT_PY = `\n([\s\S]*?)`;/)[1];

const py = await loadPyodide();
await py.loadPackage(PKGS);
await py.pyimport("micropip").install(PIP);
py.globals.set("FILES_JSON", JSON.stringify(FILES));
for (const [k, v] of Object.entries(APP_GLOBALS)) py.globals.set(k, v);
await py.runPythonAsync(BOOT_PY);
const handle = py.globals.get("handle");

let failed = false;
function check(label, r, cond) {
  const ok = cond(r);
  console.log(`${label} -> ${r.status} ${ok ? "OK" : "FAIL"}`);
  if (!ok) {
    console.log(String(r.body).slice(0, 800));
    failed = true;
  }
}

const req = (m, p, f) => JSON.parse(handle(m, p, JSON.stringify(f || {})));

check("GET /", req("GET", "/", {}), r =>
  r.status === 200 && r.body.includes("Fieldnotes"));
check("POST / (create)", req("POST", "/", {title: "e2e row", priority: "3", notes: ""}), r =>
  r.status === 200 && r.body.includes("e2e row"));
check("GET /task/1/", req("GET", "/task/1/", {}), r =>
  r.status === 200 && r.body.includes("back to ledger"));
check("GET /task/1/toggle/", req("GET", "/task/1/toggle/", {}), r =>
  r.status === 200 && r.body.includes("Fieldnotes"));

// static file serving: base64 body, css content type, real content
check("GET /static/tasks/extra.css", req("GET", "/static/tasks/extra.css", {}), r =>
  r.status === 200 && r.b64 === true && r.ctype.startsWith("text/css") &&
  atob(r.body).includes("fieldnotes-extra"));

// GET form data must reach the view as query params without breaking it
check("GET / (query data)", req("GET", "/", {q: "ledger"}), r =>
  r.status === 200 && r.body.includes("Fieldnotes"));

// multi-value POST fields (checkbox groups / multi-selects) must encode
check("POST / (multi-value)", req("POST", "/", {title: "e2e multi", priority: "1", notes: "", tags: ["a", "b"]}), r =>
  r.status === 200 && r.body.includes("e2e multi"));

if (failed) process.exit(1);
console.log("E2E PASS");
