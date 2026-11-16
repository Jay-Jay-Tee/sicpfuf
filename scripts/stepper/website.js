/* Website transport for the shared UI: instant examples, lazy browser Python. */
(function () {
  "use strict";
  const assets = new URL("./", document.currentScript.src);
  const examples = fetch(new URL("examples.json", assets)).then(response => {
    if (!response.ok) throw new Error("Could not load examples.");
    return response.json();
  });
  let worker = null, cancel = null, epoch = 0, queue = Promise.resolve();
  const result = trace => ({ ok: true, json: async () => trace });
  const failed = error => ({ steps: [], error });
  const status = message => window.dispatchEvent(new CustomEvent("sicpfuf:status", { detail: message }));

  function importedProgram() {
    // Prefer a self-contained link. A fresh tab, reload or storage-disabled
    // embedded browser must receive the same code as the original click.
    const fragments = [location.hash];
    try { if (parent !== window) fragments.push(parent.location.hash); } catch (_) { /* Cross-origin host. */ }
    for (const fragment of fragments) {
      try {
        const encoded = new URLSearchParams(fragment.slice(1)).get("program");
        if (encoded !== null) return JSON.parse(encoded);
      } catch (_) { /* A malformed link can still use a legacy import. */ }
    }
    try { return JSON.parse(sessionStorage.getItem("sicpfuf-stepper-import")); }
    catch (_) { return null; }
  }

  function stop(message) {
    epoch++;
    if (worker) worker.terminate();
    worker = null;
    if (cancel) cancel(failed(message));
  }

  function execute(data) {
    const version = epoch;
    const task = queue.then(() => version === epoch ? executeNow(data) : failed('Run stopped.'));
    queue = task.catch(() => {});
    return task;
  }

  async function executeNow(data) {
    const recorded = !data.validate_only && (await examples).find(example => example.trace && example.source === data.source &&
      example.chapter === data.chapter && (example.mode || "environment") === data.mode &&
      Boolean(example.typed) === data.typed && !data.stdin &&
      (data.max_steps || 400) >= example.trace.steps.length);
    if (recorded) return recorded.trace;
    const cold = !worker;
    if (!worker) worker = new Worker(new URL("worker.js", assets), { type: "module" });
    return new Promise(resolve => {
      let timeout;
      const finish = trace => { clearTimeout(timeout); cancel = null; resolve(trace); };
      cancel = finish;
      const deadline = milliseconds => {
        clearTimeout(timeout);
        timeout = setTimeout(() => stop("Run timed out. Try again with a smaller program."), milliseconds);
      };
      worker.onmessage = ({ data: message }) => {
        if (message.type === "status") {
          if (!data.validate_only) status(message.message);
          if (message.message === "Tracing your program…") deadline(10000);
        } else if (message.type === "result") finish(message.trace);
        else if (message.type === "error") stop(message.message);
      };
      worker.onerror = () => stop("Could not load browser Python. Check your connection and try Run again.");
      deadline(cold ? 60000 : 10000);
      worker.postMessage(data);
    });
  }

  window.sicpfufRequest = async (path, options) => {
    if (path === '/api/validate') return result(await execute({ ...JSON.parse(options.body), validate_only: true }));
    if (path === "/api/trace") return result(await execute(JSON.parse(options.body)));
    if (path !== "/api/session") throw new Error("Unknown stepper request.");
    const entries = await examples;
    const select = document.getElementById("example");
    for (const entry of entries) {
      const option = document.createElement("option");
      option.value = entry.id;
      option.textContent = entry.title;
      select.append(option);
    }
    let initial = entries[0];
    const imported = importedProgram();
    try {
      sessionStorage.removeItem("sicpfuf-stepper-import");
    } catch (_) { /* URL imports work even when storage is unavailable. */ }
    if (imported && typeof imported.source === "string" && imported.source.length < 100000 &&
        [1, 2, 3, 4].includes(imported.chapter) &&
        (imported.mode === "environment" || imported.mode === "substitution")) {
      initial = { source: imported.source, chapter: imported.chapter, mode: imported.mode,
        typed: Boolean(imported.typed), title: "Textbook example", id: "imported" };
      const option = document.createElement("option");
      option.value = initial.id;
      option.textContent = initial.title;
      select.append(option);
    }
    select.value = initial.id;
    select.addEventListener("change", () => {
      const entry = entries.find(example => example.id === select.value) || initial;
      window.dispatchEvent(new CustomEvent("sicpfuf:example", { detail: entry }));
    });
    return result(initial);
  };
  document.getElementById("stop").addEventListener("click", () => stop("Run stopped. You can edit the code and run again."));
  window.addEventListener("pagehide", () => stop("Session closed."));

  // The embedded UI follows the book's theme, including its manual theme switch.
  try {
    if (parent !== window) {
      const sync = () => {
        document.documentElement.dataset.theme = parent.document.body.dataset.mdColorScheme === "slate" ? "dark" : "light";
      };
      sync();
      const observer = new MutationObserver(sync);
      observer.observe(parent.document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
      window.addEventListener("pagehide", () => observer.disconnect());
    }
  } catch (_) { /* A directly opened UI uses the system theme. */ }
})();
