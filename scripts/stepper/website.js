/* Website transport for the shared UI: instant examples, lazy browser Python. */
(function () {
  "use strict";
  const assets = new URL("./", document.currentScript.src);
  const examples = fetch(new URL("examples.json", assets)).then(response => {
    if (!response.ok) throw new Error("Could not load examples.");
    return response.json();
  });
  let worker = null, cancel = null;
  const result = trace => ({ ok: true, json: async () => trace });
  const failed = error => ({ steps: [], error });
  const status = message => window.dispatchEvent(new CustomEvent("sicpfuf:status", { detail: message }));

  function stop(message) {
    if (worker) worker.terminate();
    worker = null;
    if (cancel) cancel(failed(message));
  }

  async function execute(data) {
    const recorded = (await examples).find(example => example.trace && example.source === data.source &&
      example.chapter === data.chapter && (example.mode || "environment") === data.mode &&
      Boolean(example.typed) === data.typed && !data.stdin);
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
          status(message.message);
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
    try {
      const imported = JSON.parse(sessionStorage.getItem("sicpfuf-stepper-import"));
      sessionStorage.removeItem("sicpfuf-stepper-import");
      if (imported && typeof imported.source === "string" && imported.source.length < 100000 &&
          [1, 2, 3, 4].includes(imported.chapter)) {
        initial = { ...imported, title: "Textbook example", id: "imported" };
        const option = document.createElement("option");
        option.value = initial.id;
        option.textContent = initial.title;
        select.append(option);
      }
    } catch (_) { /* Examples remain available when browser storage is disabled. */ }
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
