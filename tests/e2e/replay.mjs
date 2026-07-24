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

const checks = [
  ["GET", "/", {}, "Fieldnotes"],
  ["POST", "/", {title:"e2e row", priority:"3", notes:""}, "e2e row"],
  ["GET", "/task/1/", {}, "back to ledger"],
  ["GET", "/task/1/toggle/", {}, "Fieldnotes"],
];
for (const [m, p, f, expect] of checks) {
  const r = JSON.parse(handle(m, p, JSON.stringify(f)));
  const ok = r.status === 200 && r.body.includes(expect);
  console.log(`${m} ${p} -> ${r.status} ${ok ? "OK" : "FAIL"}`);
  if (!ok) { console.log(r.body.slice(0, 800)); process.exit(1); }
}
console.log("E2E PASS");
