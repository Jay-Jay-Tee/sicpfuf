(function () {
  "use strict";
  const get = id => document.getElementById(id);
  const code = get("code"), mode = get("mode"), chapter = get("chapter"), slider = get("position");
  let history = null, index = 0, timer = null, running = false;

  function pause() {
    clearInterval(timer);
    timer = null;
    get("play").textContent = "Play";
  }

  function lines() {
    get("gutter").textContent = code.value.split("\n").map((_, i) => i + 1).join("\n");
    get("gutter").scrollTop = code.scrollTop;
    const step = history && history.steps[index];
    const top = step && step.line ? 12 + (step.line - 1) * 21 - code.scrollTop : -100;
    code.style.backgroundImage = top < -21 ? "none" : `linear-gradient(transparent ${top}px, var(--highlight) ${top}px, var(--highlight) ${top + 21}px, transparent ${top + 21}px)`;
  }

  function render() {
    const steps = history ? history.steps : [], step = steps[index];
    get("back").disabled = !step || index === 0;
    get("next").disabled = !step || index === steps.length - 1;
    get("play").disabled = !step || steps.length < 2;
    slider.disabled = !step;
    slider.max = Math.max(0, steps.length - 1);
    slider.value = index;
    get("count").textContent = step ? `${index + 1} / ${steps.length}` : "0 / 0";
    get("output").textContent = step && step.output || "No output yet.";
    get("error").textContent = history && history.error || "";
    get("error").hidden = !(history && history.error);
    get("message").textContent = step ? (step.line ? `Line ${step.line} · ` : "") + step.message : "Edit the code, then Run.";
    get("inspection").hidden = true;
    const environment = mode.value === "environment";
    get("diagram").hidden = !environment;
    get("reduction").hidden = environment;
    get("diagram").replaceChildren();
    if (environment && step && step.diagram) {
      const parsed = new DOMParser().parseFromString(step.diagram, "image/svg+xml");
      const picture = document.importNode(parsed.documentElement, true);
      picture.setAttribute("aria-label", step.message);
      get("diagram").append(picture);
    }
    const before = index > 0 && steps[index - 1].expression || "";
    const after = step && step.expression || "";
    get("before").textContent = before || "—";
    get("after").replaceChildren();
    if (after) {
      let start = 0, end = 0;
      while (start < before.length && start < after.length && before[start] === after[start]) start++;
      while (end < before.length - start && end < after.length - start && before[before.length - end - 1] === after[after.length - end - 1]) end++;
      const mark = document.createElement("mark");
      mark.textContent = after.slice(start, after.length - end);
      get("after").append(document.createTextNode(after.slice(0, start)), mark, document.createTextNode(after.slice(after.length - end)));
    } else get("after").textContent = "Step forward to see the expression.";
    lines();
  }

  function invalidate() {
    pause();
    history = null;
    index = 0;
    render();
  }

  function move(next) {
    if (!history) return;
    index = Math.max(0, Math.min(history.steps.length - 1, next));
    if (index === history.steps.length - 1) pause();
    const line = history.steps[index].line;
    if (line && ((line - 1) * 21 < code.scrollTop || line * 21 > code.scrollTop + code.clientHeight - 24)) code.scrollTop = Math.max(0, (line - 3) * 21);
    render();
  }

  async function run() {
    if (running) return;
    running = true;
    invalidate();
    [code, mode, chapter, get("run")].forEach(el => { el.disabled = true; });
    get("message").textContent = "Tracing…";
    try {
      const response = await fetch("/api/trace", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: code.value, chapter: Number(chapter.value), mode: mode.value })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not run the program.");
      history = result;
      render();
    } catch (error) {
      get("message").textContent = "Could not trace the program. Is sicpfuf still running?";
      get("error").hidden = false;
      get("error").textContent = error.message;
    } finally {
      running = false;
      [code, mode, chapter, get("run")].forEach(el => { el.disabled = false; });
    }
  }

  get("run").addEventListener("click", run);
  get("back").addEventListener("click", () => { pause(); move(index - 1); });
  get("next").addEventListener("click", () => { pause(); move(index + 1); });
  slider.addEventListener("input", () => { pause(); move(Number(slider.value)); });
  get("play").addEventListener("click", () => {
    if (timer) { pause(); return; }
    if (index === history.steps.length - 1) move(0);
    get("play").textContent = "Pause";
    timer = setInterval(() => move(index + 1), 900);
  });
  code.addEventListener("input", invalidate);
  code.addEventListener("scroll", lines);
  code.addEventListener("keydown", event => {
    if (event.key === "Tab") {
      event.preventDefault();
      code.setRangeText("    ", code.selectionStart, code.selectionEnd, "end");
      invalidate();
    }
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); run(); }
  });
  mode.addEventListener("change", () => {
    const substitution = mode.value === "substitution";
    Array.from(chapter.options).forEach(option => { option.disabled = substitution && Number(option.value) > 2; });
    if (substitution && Number(chapter.value) > 2) chapter.value = "2";
    invalidate();
  });
  chapter.addEventListener("change", invalidate);
  get("diagram").addEventListener("click", event => {
    const frame = event.target.closest("[data-frame]"), fn = event.target.closest("[data-function]");
    const step = history && history.steps[index];
    if (!step) return;
    let text = "";
    if (frame) {
      const entry = step.frames.find(f => f.id === frame.dataset.frame);
      if (entry) text = `${entry.id} · ${entry.call}\nEnclosing: ${entry.parent}\n\n` + entry.bindings.map(b => b.name + " = " + b.value).join("\n");
    } else if (fn) {
      const entry = step.functions.find(f => f.id === fn.dataset.function);
      if (entry) text = `${entry.id} (${entry.params.join(", ")})\n${entry.source}\nRemembers: ${entry.env}`;
    }
    get("inspection").textContent = text;
    get("inspection").hidden = !text;
  });
  get("diagram").addEventListener("keydown", event => {
    if ((event.key === "Enter" || event.key === " ") && event.target.closest("[data-frame], [data-function]")) {
      event.preventDefault();
      event.target.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }
  });
  window.addEventListener("pagehide", pause);
  render();
  [code, mode, chapter, get("run")].forEach(el => { el.disabled = true; });
  fetch("/api/session").then(response => {
    if (!response.ok) throw new Error("Could not load the program.");
    return response.json();
  }).then(session => {
    code.value = session.source;
    mode.value = session.mode;
    chapter.value = session.chapter;
    get("filename").textContent = session.filename;
    mode.dispatchEvent(new Event("change"));
    run();
  }).catch(error => {
    [code, mode, chapter, get("run")].forEach(el => { el.disabled = false; });
    get("message").textContent = error.message + " Start sicpfuf --ui again.";
  });
})();
