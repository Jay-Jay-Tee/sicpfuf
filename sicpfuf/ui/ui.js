(function () {
  "use strict";
  const get = id => document.getElementById(id);
  const request = (path, options) => window.sicpfufRequest ? window.sicpfufRequest(path, options) : fetch(path, options);
  const code = get("code"), mode = get("mode"), chapter = get("chapter"), slider = get("position");
  let history = null, index = 0, timer = null, running = false, zoom = null;
  let syntaxSource = null;
  let programView = false;
  let pan = null, dragged = false;
  const bindingText = binding => binding.objectId ? binding.objectId + (binding.function ? "" : " " + binding.value) : binding.value;
  const keywords = new Set("and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try type while with yield".split(" "));

  // Colour only: the actual parser and type checker remain in Python. All source
  // enters the DOM as text nodes, including strings that look like HTML.
  function highlight() {
    if (syntaxSource === code.value) return;
    syntaxSource = code.value;
    const tokens = /#[^\n]*|"""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$)|"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?|\b\d+(?:\.\d*)?(?:[eE][+-]?\d+)?j?\b|\b[A-Za-z_]\w*\b/g;
    const fragment = document.createDocumentFragment();
    let end = 0;
    for (const match of code.value.matchAll(tokens)) {
      fragment.append(document.createTextNode(code.value.slice(end, match.index)));
      const word = match[0], span = document.createElement("span");
      span.className = "tok-" + (word[0] === "#" ? "comment" : /^["']/.test(word) ? "string" : /^\d/.test(word) ? "number" : keywords.has(word) ? "keyword" : "name");
      span.textContent = word;
      fragment.append(span);
      end = match.index + word.length;
    }
    fragment.append(document.createTextNode(code.value.slice(end) + "\n"));
    get("syntax").replaceChildren(fragment);
  }

  function state(text, value = "") {
    get("run-state").textContent = text;
    get("run-state").dataset.state = value;
  }

  function sizeDiagram() {
    const picture = get("diagram").querySelector("svg");
    if (!picture) return;
    const [, , naturalWidth, naturalHeight] = picture.getAttribute("viewBox").split(/\s+/).map(Number);
    const available = get("diagram").clientWidth - 40;
    const height = get("diagram").clientHeight;
    const scale = zoom === null ? Math.min(1, Math.max(160, available) / naturalWidth,
      height > 80 ? (height - 40) / naturalHeight : 1) : zoom;
    picture.style.width = `${naturalWidth * scale}px`;
    picture.style.height = `${naturalHeight * scale}px`;
    get("zoom-fit").textContent = zoom === null ? "Fit" : Math.round(zoom * 100) + "%";
  }

  function clearSelection() {
    get("inspection").hidden = get("inspection-panel").hidden = true;
    get("diagram").querySelectorAll(".selected, .pointer-trace, .pointer-trace-incoming, .pointer-muted, .pointer-related").forEach(node => {
      node.classList.remove("selected", "pointer-trace", "pointer-trace-incoming", "pointer-muted", "pointer-related");
    });
  }

  function tracePointers(node) {
    const key = node.dataset.nodeId, related = new Set([key]);
    get("diagram").querySelectorAll("path[data-source][data-target]").forEach(edge => {
      const outgoing = edge.dataset.source === key, incoming = edge.dataset.target === key;
      edge.classList.toggle("pointer-trace", outgoing);
      edge.classList.toggle("pointer-trace-incoming", incoming && !outgoing);
      edge.classList.toggle("pointer-muted", !outgoing && !incoming);
      if (outgoing || incoming) { related.add(edge.dataset.source); related.add(edge.dataset.target); }
    });
    get("diagram").querySelectorAll("[data-node-id]").forEach(item => item.classList.toggle("pointer-related", related.has(item.dataset.nodeId)));
  }

  function zoomDiagram(value, focusX, focusY) {
    const canvas = get("diagram"), picture = canvas.querySelector("svg");
    if (!picture) return;
    const naturalWidth = Number(picture.getAttribute("viewBox").split(/\s+/)[2]);
    const previousScale = parseFloat(picture.style.width) / naturalWidth;
    const rect = picture.getBoundingClientRect(), viewport = canvas.getBoundingClientRect();
    const x = focusX === undefined ? canvas.clientWidth / 2 : focusX;
    const y = focusY === undefined ? canvas.clientHeight / 2 : focusY;
    const worldX = (viewport.left + x - rect.left) / previousScale;
    const worldY = (viewport.top + y - rect.top) / previousScale;
    zoom = Math.max(.15, Math.min(3, value));
    sizeDiagram();
    const updated = picture.getBoundingClientRect();
    canvas.scrollLeft += updated.left + worldX * zoom - viewport.left - x;
    canvas.scrollTop += updated.top + worldY * zoom - viewport.top - y;
  }

  function pause() {
    clearInterval(timer);
    timer = null;
    get("play").textContent = "Play";
  }

  function controls(disabled) {
    [code, mode, chapter, get("stdin"), get("run")].forEach(el => { el.disabled = disabled; });
    if (get("example")) get("example").disabled = disabled;
    if (get("stop")) get("stop").disabled = !disabled;
    get("typed").disabled = disabled || chapter.value !== "4" || mode.value !== "environment";
  }

  function lines() {
    highlight();
    const step = history && history.steps[index];
    get("gutter").replaceChildren(...code.value.split("\n").map((_, i) => {
      const line = document.createElement("span");
      line.textContent = i + 1;
      if (step && step.line === i + 1) line.className = "active";
      return line;
    }));
    get("gutter").scrollTop = code.scrollTop;
    get("highlight").scrollTop = code.scrollTop;
    get("highlight").scrollLeft = code.scrollLeft;
    const top = step && step.line ? 16 + (step.line - 1) * 21 - code.scrollTop : -100;
    get("highlight").style.backgroundImage = top < -21 ? "none" : `linear-gradient(transparent ${top}px, var(--highlight) ${top}px, var(--highlight) ${top + 21}px, transparent ${top + 21}px)`;
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
    get("inspection-panel").hidden = true;
    const environment = mode.value === "environment";
    get("model-title").textContent = environment ? "Environment model" : "Substitution model";
    get("event-kind").textContent = !step ? "READY" : history.error && index === steps.length - 1 ? "STOPPED" : index === 0 ? "START" : index === steps.length - 1 ? "FINISHED" : step.phase === "beforeMarker" ? "BEFORE" : step.phase === "afterMarker" ? "AFTER" : "STEP";
    get("frame-panel").hidden = !environment;
    get("diagram-toolbar").hidden = !environment;
    get("frame-panel").parentElement.classList.toggle("substitution", !environment);
    const current = step && step.frames.find(frame => frame.current);
    get("frame-name").textContent = current ? current.id : "—";
    get("frame-call").textContent = current ? current.call : "No active frame";
    get("frame-parent").textContent = current ? "Enclosing → " + current.parent : "";
    get("bindings").replaceChildren();
    if (current) for (const binding of current.bindings) {
      const row = document.createElement("div"), name = document.createElement("dt"), value = document.createElement("dd");
      name.textContent = binding.name;
      value.textContent = bindingText(binding);
      row.append(name, value);
      get("bindings").append(row);
    }
    get("frame-hint").textContent = current && current.bindings.length ? "Select a frame or closure to inspect it." : "No bindings in this frame yet.";
    get("diagram").hidden = !environment || programView;
    get("diagram-help").hidden = !environment || programView;
    get("program-view").hidden = !environment || !programView;
    get("zoom-controls").hidden = programView;
    const programText = step && step.program || "Run your code to see its reductions.";
    get("remaining-program").replaceChildren();
    if (step && step.focus) {
      const [start, end] = step.focus, mark = document.createElement("mark"), characters = Array.from(programText);
      mark.className = step.phase === "beforeMarker" ? "before-reduction" : "after-reduction";
      mark.textContent = characters.slice(start, end).join("");
      get("remaining-program").append(document.createTextNode(characters.slice(0, start).join("")), mark, document.createTextNode(characters.slice(end).join("")));
    } else get("remaining-program").textContent = programText;
    get("program-phase").textContent = step && step.phase === "beforeMarker" ? "Before reduction" : step && step.phase === "afterMarker" ? "After reduction" : "";
    get("reduction").hidden = environment;
    get("diagram").replaceChildren();
    if (environment && step && step.diagram) {
      const parsed = new DOMParser().parseFromString(step.diagram, "image/svg+xml");
      const picture = document.importNode(parsed.documentElement, true);
      picture.setAttribute("aria-label", step.message);
      if (current) Array.from(picture.querySelectorAll("[data-frame]")).filter(node => node.dataset.frame === current.id).forEach(node => { node.dataset.current = "true"; });
      get("diagram").append(picture);
      sizeDiagram();
    } else if (environment) {
      const empty = document.createElement("div");
      empty.className = "empty-diagram";
      empty.textContent = "Run your code to explore its environment.";
      get("diagram").append(empty);
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
    state("Edited · run again");
    render();
  }

  function move(next) {
    if (!history || !history.steps.length) return;
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
    controls(true);
    get("message").textContent = "Tracing…";
    get("run").textContent = "Running…";
    state("Tracing…", "tracing");
    try {
      const response = await request("/api/trace", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: code.value, chapter: Number(chapter.value), mode: mode.value, stdin: get("stdin").value, typed: get("typed").checked })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not run the program.");
      history = result;
      index = result.error ? Math.max(0, result.steps.length - 1) : 0;
      render();
      state(result.error ? "Stopped" : "Trace ready", result.error ? "error" : "");
    } catch (error) {
      get("message").textContent = "Could not trace the program.";
      get("error").hidden = false;
      get("error").textContent = error.message;
      state("Disconnected", "error");
    } finally {
      running = false;
      controls(false);
      get("run").textContent = "Run";
    }
  }

  get("run").addEventListener("click", run);
  for (const [id, showProgram] of [["view-diagram", false], ["view-program", true]]) {
    get(id).addEventListener("click", () => {
      programView = showProgram;
      get("view-diagram").setAttribute("aria-pressed", String(!programView));
      get("view-program").setAttribute("aria-pressed", String(programView));
      render();
    });
  }
  get("back").addEventListener("click", () => { pause(); move(index - 1); });
  get("next").addEventListener("click", () => { pause(); move(index + 1); });
  slider.addEventListener("input", () => { pause(); move(Number(slider.value)); });
  function play() {
    if (timer) { pause(); return; }
    if (!history || history.steps.length < 2) return;
    if (index === history.steps.length - 1) move(0);
    get("play").textContent = "Pause";
    timer = setInterval(() => move(index + 1), Number(get("speed").value));
  }
  get("play").addEventListener("click", play);
  get("speed").addEventListener("change", () => { if (timer) { pause(); play(); } });
  get("zoom-fit").addEventListener("click", () => {
    zoom = null; sizeDiagram();
    get("diagram").scrollTop = get("diagram").scrollLeft = 0;
  });
  get("zoom-actual").addEventListener("click", () => zoomDiagram(1));
  for (const [id, factor] of [["zoom-in", 1.25], ["zoom-out", .8]]) get(id).addEventListener("click", () => {
    const picture = get("diagram").querySelector("svg");
    if (!picture) return;
    const naturalWidth = Number(picture.getAttribute("viewBox").split(/\s+/)[2]);
    zoomDiagram((parseFloat(picture.style.width) / naturalWidth) * factor);
  });
  window.addEventListener("resize", sizeDiagram);
  document.addEventListener("keydown", event => {
    if (event.defaultPrevented || /^(TEXTAREA|INPUT|SELECT)$/.test(event.target.tagName) || event.target.closest('[role="button"]')) return;
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); run(); }
    else if (event.key === "ArrowRight") { event.preventDefault(); pause(); move(index + 1); }
    else if (event.key === "ArrowLeft") { event.preventDefault(); pause(); move(index - 1); }
    else if (event.key === " " && event.target.tagName !== "BUTTON") { event.preventDefault(); play(); }
  });
  code.addEventListener("input", invalidate);
  get("stdin").addEventListener("input", invalidate);
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
    if (substitution || chapter.value !== "4") get("typed").checked = false;
    controls(false);
    invalidate();
  });
  chapter.addEventListener("change", () => {
    if (chapter.value !== "4") get("typed").checked = false;
    controls(false);
    invalidate();
  });
  get("typed").addEventListener("change", invalidate);
  get("diagram").addEventListener("click", event => {
    if (dragged) { dragged = false; return; }
    const frame = event.target.closest("[data-frame]"), fn = event.target.closest("[data-function]"), object = event.target.closest("[data-object]"), builtins = event.target.closest("[data-builtins]");
    const step = history && history.steps[index];
    if (!step) return;
    let text = "";
    if (builtins) {
      text = "Built-ins · pre-declared names\n\nBuilt-in functions and the chapter's library names are available through this enclosing environment. Its bindings are collapsed here.\n\nGlobal points here; each call frame points to its lexical parent.";
    } else if (frame) {
      const entry = step.frames.find(f => f.id === frame.dataset.frame);
      if (entry) text = `${entry.id} · ${entry.call}\n${entry.reachable === false ? "Unreachable · retained for inspection\n" : ""}Enclosing: ${entry.parent}\n\n` + entry.bindings.map(b => b.name + " = " + bindingText(b)).join("\n");
    } else if (fn) {
      const entry = step.functions.find(f => f.id === fn.dataset.function);
      if (entry) text = `${entry.objectId || entry.id} (${entry.params.join(", ")})\n${entry.reachable === false ? "Unreachable · retained for inspection\n" : ""}${entry.source}\nRemembers: ${entry.env}`;
    } else if (object) {
      const entry = step.store && step.store.heap.find(item => item.id === object.dataset.object);
      if (entry) text = `${entry.id} · list\n${entry.isGarbage ? "Unreachable · retained for inspection\n" : ""}` + entry.elements.map((item, i) => `${i}: ${item.objectId || item.display || item.name || "(unassigned)"}`).join("\n");
    }
    clearSelection();
    get("inspection").textContent = text;
    get("inspection").hidden = !text;
    get("inspection-panel").hidden = !text;
    if (text) {
      const node = frame || fn || object || builtins;
      node.classList.add("selected");
      tracePointers(node);
    }
  });
  get("clear-inspection").addEventListener("click", clearSelection);
  get("diagram").addEventListener("dblclick", event => {
    const node = event.target.closest("[data-bounds]");
    if (!node) return;
    const [x, y, width, height] = node.dataset.bounds.split(",").map(Number);
    const canvas = get("diagram");
    zoom = Math.min(2, Math.max(.6, Math.min((canvas.clientWidth - 80) / width, (canvas.clientHeight - 80) / height)));
    sizeDiagram();
    canvas.scrollLeft = Math.max(0, 20 + (x + width / 2) * zoom - canvas.clientWidth / 2);
    canvas.scrollTop = Math.max(0, 20 + (y + height / 2) * zoom - canvas.clientHeight / 2);
  });
  get("diagram").addEventListener("wheel", event => {
    if (!event.ctrlKey && !event.metaKey) return;
    const picture = get("diagram").querySelector("svg");
    if (!picture) return;
    event.preventDefault();
    const naturalWidth = Number(picture.getAttribute("viewBox").split(/\s+/)[2]);
    const bounds = get("diagram").getBoundingClientRect();
    zoomDiagram(parseFloat(picture.style.width) / naturalWidth * Math.exp(-event.deltaY * .003),
      event.clientX - bounds.left, event.clientY - bounds.top);
  }, { passive: false });
  get("diagram").addEventListener("pointerdown", event => {
    if (event.button !== 0 || event.target.closest("[role=button]")) return;
    const canvas = get("diagram");
    pan = { x: event.clientX, y: event.clientY, left: canvas.scrollLeft, top: canvas.scrollTop };
    dragged = false;
    if (canvas.setPointerCapture) canvas.setPointerCapture(event.pointerId);
  });
  get("diagram").addEventListener("pointermove", event => {
    if (!pan) return;
    const dx = event.clientX - pan.x, dy = event.clientY - pan.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) dragged = true;
    if (!dragged) return;
    get("diagram").classList.add("panning");
    get("diagram").scrollLeft = pan.left - dx;
    get("diagram").scrollTop = pan.top - dy;
  });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) get("diagram").addEventListener(name, () => {
    pan = null; get("diagram").classList.remove("panning");
  });
  get("diagram").addEventListener("keydown", event => {
    if (event.key === "Escape") { event.preventDefault(); clearSelection(); }
    if ((event.key === "Enter" || event.key === " ") && event.target.closest("[data-frame], [data-function], [data-object], [data-builtins]")) {
      event.preventDefault();
      event.target.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }
  });
  window.addEventListener("pagehide", pause);
  window.addEventListener("sicpfuf:status", event => {
    if (running) { get("message").textContent = event.detail; state(event.detail, "tracing"); }
  });
  function loadSession(session) {
    code.value = session.source;
    mode.value = session.mode || "environment";
    chapter.value = session.chapter;
    get("typed").checked = Boolean(session.typed);
    get("filename").textContent = session.filename || session.title || "Untitled";
    mode.dispatchEvent(new Event("change"));
    return run();
  }
  window.addEventListener("sicpfuf:example", event => { if (!running) loadSession(event.detail); });
  render();
  controls(true);
  request("/api/session").then(response => {
    if (!response.ok) throw new Error("Could not load the program.");
    return response.json();
  }).then(loadSession).catch(error => {
    controls(false);
    get("message").textContent = error.message + " Reload to try again.";
  });
})();
