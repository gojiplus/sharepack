// E2E: replay the emitted artifact's exact boot + request cycle headlessly.
// Usage: node replay.mjs path/to/demo.html [tasktrack|flaskapp|fastapiapp]
import { loadPyodide } from "pyodide";
import { readFileSync } from "fs";

const html = readFileSync(process.argv[2], "utf8");
const fixture = process.argv[3] || "tasktrack";
const FILES = JSON.parse(html.match(/const FILES = (\{.*?\});\n/s)[1]);
const APP_GLOBALS = JSON.parse(html.match(/const APP_GLOBALS = (\{.*?\});\n/s)[1]);
const PKGS = JSON.parse(html.match(/const PYODIDE_PACKAGES = (\[.*?\]);\n/s)[1]);
const PIP = JSON.parse(html.match(/const PIP_INSTALL = (\[.*?\]);\n/s)[1]);
const BOOT_PY = html.match(/const BOOT_PY = `\n([\s\S]*?)`;/)[1];

const py = await loadPyodide();
await py.loadPackage(PKGS);
const micropip = py.pyimport("micropip");
for (const req of PIP) await micropip.install(req);
py.globals.set("FILES_JSON", JSON.stringify(FILES));
for (const [k, v] of Object.entries(APP_GLOBALS)) py.globals.set(k, v);
await py.runPythonAsync(BOOT_PY);
const handle = py.globals.get("handle");

let failed = false;
const req = async (m, p, f) =>
  JSON.parse(await handle(m, p, JSON.stringify(f || {})));
const text = r => (r.b64 ? atob(r.body) : r.body);
const check = (label, r, cond) => {
  const ok = cond(r);
  console.log(`${label} -> ${r.status} ${ok ? "OK" : "FAIL"}`);
  if (!ok) {
    console.log(String(r.body).slice(0, 800));
    failed = true;
  }
};

const CHECKS = {
  async tasktrack() {
    check("GET /", await req("GET", "/"), r =>
      r.status === 200 && r.body.includes("Fieldnotes"));
    check("POST / (create)",
      await req("POST", "/", {title: "e2e row", priority: "3", notes: ""}),
      r => r.status === 200 && r.body.includes("e2e row"));
    check("GET /task/1/", await req("GET", "/task/1/"), r =>
      r.status === 200 && r.body.includes("back to ledger"));
    check("GET /task/1/toggle/", await req("GET", "/task/1/toggle/"), r =>
      r.status === 200 && r.body.includes("Fieldnotes"));
    check("GET /static/tasks/extra.css",
      await req("GET", "/static/tasks/extra.css"),
      r => r.status === 200 && r.ctype.startsWith("text/css") &&
           text(r).includes("fieldnotes-extra"));
    check("GET / (query data)", await req("GET", "/", {q: "ledger"}), r =>
      r.status === 200 && r.body.includes("Fieldnotes"));
    check("POST / (multi-value)",
      await req("POST", "/",
        {title: "e2e multi", priority: "1", notes: "", tags: ["a", "b"]}),
      r => r.status === 200 && r.body.includes("e2e multi"));
  },

  async flaskapp() {
    check("GET /", await req("GET", "/"), r =>
      r.status === 200 && r.body.includes("Clipnotes"));
    check("POST / (create + flash)",
      await req("POST", "/", {title: "e2e clip", body: "from the replay"}),
      r => r.status === 200 && r.body.includes("e2e clip") &&
           r.body.includes("saved"));
    check("GET /clip/1", await req("GET", "/clip/1"), r =>
      r.status === 200 && r.body.includes("back to clips"));
    check("GET /about", await req("GET", "/about"), r =>
      r.status === 200 && r.body.includes("About"));
    check("GET /static/style.css", await req("GET", "/static/style.css"), r =>
      r.status === 200 && r.ctype.startsWith("text/css") &&
      text(r).includes("clipnotes-style"));
    check("GET / (query data)", await req("GET", "/", {q: "clip"}), r =>
      r.status === 200 && r.body.includes("Clipnotes"));
    check("POST / (multi-value)",
      await req("POST", "/",
        {title: "e2e multi clip", body: "x", tags: ["a", "b"]}),
      r => r.status === 200 && r.body.includes("e2e multi clip"));
  },

  async fastapiapp() {
    check("GET /", await req("GET", "/"), r =>
      r.status === 200 && r.body.includes("Pulseboard"));
    check("POST /add (303 follow)",
      await req("POST", "/add", {name: "e2e signal", state: "up"}),
      r => r.status === 200 && r.path === "/" && r.body.includes("e2e signal"));
    check("GET /item/1", await req("GET", "/item/1"), r =>
      r.status === 200 && r.body.includes("back to board"));
    check("GET /api/items", await req("GET", "/api/items"), r =>
      r.status === 200 && r.ctype.startsWith("application/json") &&
      Array.isArray(JSON.parse(r.body)));
    check("GET /static/style.css", await req("GET", "/static/style.css"), r =>
      r.status === 200 && r.ctype.startsWith("text/css") &&
      text(r).includes("pulseboard-style"));
    check("GET / (query data)", await req("GET", "/", {q: "pulse"}), r =>
      r.status === 200 && r.body.includes("Pulseboard"));
  },
};

if (!CHECKS[fixture]) {
  console.error(`unknown fixture "${fixture}"`);
  process.exit(2);
}
await CHECKS[fixture]();
if (failed) process.exit(1);
console.log("E2E PASS");
