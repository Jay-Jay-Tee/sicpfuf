/* Run the shipped worker against real Pyodide, with local files replacing only
 * HTTP transport. This exercises WebAssembly Python, zip extraction, imports,
 * message handling, and repeated runs without depending on CDN availability.
 *
 * node --experimental-vm-modules tests/website_worker.mjs /path/to/pyodide.mjs site
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import vm from "node:vm";

const runtimeURL = pathToFileURL(resolve(process.argv[2] || "node_modules/pyodide/pyodide.mjs")).href;
const site = resolve(process.argv[3] || "site");
const source = readFileSync(resolve(site, "assets/stepper/worker.js"), "utf8");
const examples = JSON.parse(readFileSync(resolve(site, "assets/stepper/examples.json"), "utf8"));
const runtimeVersion = JSON.parse(readFileSync(new URL("package.json", runtimeURL), "utf8")).version;
assert.ok(source.includes(`/v${runtimeVersion}/`), "Test the same Pyodide version that the website loads");

const messages = [];
let runtimeLoads = 0, archiveFetches = 0;
const self = {
  location: { href: "https://example.test/sicpfuf/assets/stepper/worker.js" },
  postMessage: message => messages.push(message),
};
const context = vm.createContext({
  self, URL,
  fetch: async url => {
    assert.equal(String(url), "https://example.test/sicpfuf/assets/stepper/sicpfuf.zip");
    archiveFetches++;
    const bytes = readFileSync(resolve(site, "assets/stepper/sicpfuf.zip"));
    return { ok: true, arrayBuffer: async () => new Uint8Array(bytes).buffer };
  },
});
const worker = new vm.SourceTextModule(source, {
  context,
  importModuleDynamically: async url => {
    assert.equal(url, `https://cdn.jsdelivr.net/pyodide/v${runtimeVersion}/full/pyodide.mjs`);
    runtimeLoads++;
    return import(runtimeURL);
  },
});
await worker.link(() => { throw new Error("Unexpected static import"); });
await worker.evaluate();

async function run(source, chapter = 3, mode = "environment", typed = false, stdin = "") {
  messages.length = 0;
  await self.onmessage({ data: { source, chapter, mode, typed, stdin } });
  const final = messages.at(-1);
  assert.equal(final.type, "result", final.message);
  return final.trace;
}

for (const example of examples) {
  const result = await run(example.source, example.chapter, example.mode || "environment", Boolean(example.typed));
  // Compare the entire browser history with the build's CPython history.
  assert.deepEqual(JSON.parse(JSON.stringify(result)), example.trace, example.title);
}
const scopeProbes = JSON.parse(readFileSync(new URL('./conformance/substitution-scope.json', import.meta.url), 'utf8'));
for (const entry of scopeProbes.cases) {
  const result = await run(entry.source, 2, 'substitution');
  assert.equal(result.error, null, entry.id);
  assert.equal(result.steps.at(-1).output, entry.expected.substitution_output, entry.id);
}
assert.equal((await run("value = 21\nprint(value * 2)\n" )).steps.at(-1).output, "42\n");
assert.equal((await run("print(1 + 2)\n", 1)).steps.at(-1).output, "3\n");
assert.equal((await run('a = 1j ** math_inf\nprint(is_complex(a), a != a)\n', 1)).steps.at(-1).output, 'True True\n');
assert.equal((await run('print(2j ** 2000, 2j ** -2000)\n', 1)).steps.at(-1).output, '(inf-infj) 0j\n');
assert.ok((await run("xs = [1, 2]\n", 1)).error, "chapter 1 must reject lists");
assert.match((await run("print(value)\n")).error, /value/); // each run starts fresh
const failure = await run("print(7)\nx = 1 / 0\n");
assert.match(failure.error, /ZeroDivisionError/);
assert.equal(failure.steps.at(-1).output, "7\n");
assert.match((await run("while True:\n    pass\n")).error, /400 steps/);
assert.equal((await run("print(123)\n")).steps.at(-1).output, "123\n");
assert.equal((await run("print((2 + 3) * 4)\n", 1, "substitution")).steps.at(-1).output, "20\n");
assert.ok((await run("x = 1\n", 3, "substitution")).error);
assert.equal((await run('print(input("Name: "))\n', 2, "environment", false, "Ada\n")).steps.at(-1).output, "Name: Ada\n");
const typedError = await run('print("must not run")\nx: int = "wrong"\n', 4, "environment", true);
assert.match(typedError.error, /StaticTypeError/);
assert.equal(typedError.steps.at(-1).output, "");
assert.equal(runtimeLoads, 1, "reuse the runtime after the first custom run");
assert.equal(archiveFetches, 1, "unpack the interpreter only once");
console.log("Real Pyodide worker checks passed: all example histories match CPython; edits, chapter rules, errors, limits, and runtime reuse work.");
