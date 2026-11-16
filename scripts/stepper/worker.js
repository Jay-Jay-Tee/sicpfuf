/* Keep Python off the UI thread. Terminating this worker stops a custom run. */
let runtime;

async function loadRuntime() {
  const { loadPyodide } = await import("https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs");
  const py = await loadPyodide();
  const response = await fetch(new URL("sicpfuf.zip", self.location.href));
  if (!response.ok) throw new Error("Could not download sicpfuf. Reload and try again.");
  py.unpackArchive(await response.arrayBuffer(), "zip");
  py.runPython("import io, json, sys\nfrom sicpfuf.xray.playground import trace");
  return py;
}

self.onmessage = async ({ data }) => {
  try {
    self.postMessage({ type: "status", message: runtime ? "Tracing…" : "Loading Python… The first custom run takes a little longer." });
    if (!runtime) runtime = loadRuntime().catch(error => { runtime = null; throw error; });
    const py = await runtime;
    self.postMessage({ type: "status", message: "Tracing your program…" });
    py.globals.set("stepper_request", JSON.stringify(data));
    const result = py.runPython(`
request = json.loads(stepper_request)
previous_stdin = sys.stdin
try:
    sys.stdin = io.StringIO(request.get("stdin", ""))
    max_steps = request.get("max_steps", 400)
    if type(max_steps) is not int or not 2 <= max_steps <= 5000:
        raise ValueError("Max steps must be an integer between 2 and 5000.")
    result = trace(request["source"], request["chapter"], request["mode"],
                   typed=request.get("typed", False), max_steps=max_steps)
finally:
    sys.stdin = previous_stdin
json.dumps(result)
`);
    self.postMessage({ type: "result", trace: JSON.parse(result) });
  } catch (error) {
    self.postMessage({ type: "error", message: "Could not run the program: " + error.message });
  }
};
