/* The interpreter runs off the UI thread; Stop terminates even an infinite loop. */
let runtime;

async function loadRuntime() {
  const { loadPyodide } = await import("https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs");
  const py = await loadPyodide();
  const response = await fetch(new URL("sicpfuf.zip", self.location.href));
  if (!response.ok) throw new Error("Could not download the interpreter. Reload and try again.");
  py.unpackArchive(await response.arrayBuffer(), "zip");
  py.runPython("from sicpfuf.xray.playground import trace\nimport json");
  return py;
}

self.onmessage = async ({ data }) => {
  try {
    self.postMessage({ type: "status", message: "Loading Python… The first run may take a little while." });
    if (!runtime) runtime = loadRuntime().catch(error => { runtime = null; throw error; });
    const py = await runtime;
    self.postMessage({ type: "status", message: "Tracing your program…" });
    py.globals.set("lab_source", data.source);
    py.globals.set("lab_chapter", data.chapter);
    py.globals.set("lab_mode", data.mode || "environment");
    const result = py.runPython("json.dumps(trace(lab_source, lab_chapter, lab_mode))");
    self.postMessage({ type: "result", trace: JSON.parse(result) });
  } catch (error) {
    self.postMessage({ type: "error", message: "Could not run the program: " + error.message });
  }
};
