/* Environment lab, with precomputed examples and lazy browser Python for edits. */
(function () {
  "use strict";
  const scriptURL = new URL(document.currentScript.src);
  const assets = new URL("./", scriptURL);
  let dispose = () => {};

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function addExploreButtons() {
    document.querySelectorAll(".md-content .highlight").forEach(block => {
      const code = block.querySelector("code");
      const title = block.querySelector(".filename");
      const chapter = title && title.textContent.match(/§([1-4])/);
      if (!code || !chapter || block.querySelector(".lab-explore")) return;
      // These examples need external files, typed mode, or a graphics/audio viewer.
      if (/--with|--typed/.test(title.textContent) || /from (rune|curve|sound) import/.test(code.textContent)) return;
      const button = element("button", "Explore step by step", "lab-explore");
      button.type = "button";
      button.addEventListener("click", () => {
        try {
          sessionStorage.setItem("sicpfuf-lab-import", JSON.stringify({
            source: code.textContent, chapter: Number(chapter[1]),
            mode: /--subst/.test(title.textContent) ? "substitution" : "environment"
          }));
        } catch (_) { /* The lab still opens when browser storage is unavailable. */ }
        location.href = new URL("../playground/", assets).href;
      });
      block.append(button);
    });
  }

  async function setup() {
    dispose();
    addExploreButtons();
    const box = document.getElementById("environment-lab");
    if (!box) return;
    let alive = true, worker = null, timer = null, timeout = null;
    let examples = [], history = null, position = 0, busy = false, selected = null;
    let untouched = true;
    let mode = "environment", zoom = null;
    const drafts = {};
    const stopPlayback = () => {
      clearInterval(timer);
      timer = null;
      play.textContent = "▶ Play";
    };
    dispose = () => {
      alive = false;
      clearInterval(timer);
      clearTimeout(timeout);
      if (worker) worker.terminate();
    };
    box.replaceChildren();
    const modes = element("div", undefined, "lab-toolbar lab-modes");
    modes.setAttribute("aria-label", "Execution model");
    const environmentMode = element("button", "E-stepper · environments");
    const substitutionMode = element("button", "Stepper · substitution");
    modes.append(environmentMode, substitutionMode);
    const toolbar = element("div", undefined, "lab-toolbar");
    const exampleLabel = element("label", "Explore ");
    const select = element("select");
    select.setAttribute("aria-label", "Example program");
    const placeholder = element("option", "Choose an example");
    placeholder.value = "";
    select.append(placeholder);
    exampleLabel.append(select);
    const chapterLabel = element("label", "Language ");
    const chapter = element("select");
    chapter.setAttribute("aria-label", "Python chapter");
    [1, 2, 3, 4].forEach(n => {
      const option = element("option", "Python §" + n);
      option.value = n;
      chapter.append(option);
    });
    chapter.value = "3";
    chapterLabel.append(chapter);
    toolbar.append(exampleLabel, chapterLabel);
    const hint = element("p", "Loading examples…", "lab-hint");
    const columns = element("div", undefined, "lab-columns");
    const editorPanel = element("section", undefined, "lab-panel");
    const editorLabel = element("label", "Your program", "lab-heading");
    editorLabel.htmlFor = "lab-editor";
    const editor = element("textarea", undefined, "lab-editor");
    editor.id = "lab-editor";
    editor.spellcheck = false;
    editor.setAttribute("autocapitalize", "off");
    editor.setAttribute("autocorrect", "off");
    editor.setAttribute("aria-describedby", "lab-editor-help");
    const editorHelp = element("p", "Tab inserts four spaces. Ctrl / ⌘ + Enter runs your code.", "lab-small");
    editorHelp.id = "lab-editor-help";
    const runbar = element("div", undefined, "lab-toolbar");
    const run = element("button", "Run code", "lab-primary");
    const stop = element("button", "Stop");
    const reset = element("button", "Reset example");
    stop.disabled = true;
    runbar.append(run, stop, reset);
    const status = element("p", "Loading examples…", "lab-small");
    status.setAttribute("role", "status");
    const outputTitle = element("h3", "Output so far");
    const output = element("pre", "", "lab-output");
    const error = element("pre", "", "lab-error");
    error.setAttribute("role", "alert");
    error.hidden = true;
    const editorShell = element("div", undefined, "lab-editor-shell");
    const gutter = element("pre", "1", "lab-gutter");
    gutter.setAttribute("aria-hidden", "true");
    editorShell.append(gutter, editor);
    editorPanel.append(editorLabel, editorShell, editorHelp, runbar, status, outputTitle, output, error);
    const diagramPanel = element("section", undefined, "lab-panel");
    const diagramHeading = element("h2", "Environment diagram", "lab-heading");
    diagramPanel.append(diagramHeading);
    const controls = element("div", undefined, "lab-toolbar");
    const first = element("button", "↤ Start");
    const previous = element("button", "← Back");
    const play = element("button", "▶ Play");
    const next = element("button", "Next →");
    const last = element("button", "End ↦");
    const speed = element("select");
    speed.setAttribute("aria-label", "Playback speed");
    [[2000, "0.5×"], [1000, "1×"], [500, "2×"]].forEach(([value, label]) => {
      const option = element("option", label);
      option.value = value;
      speed.append(option);
    });
    speed.value = "1000";
    controls.append(first, previous, play, next, last, speed);
    const slider = element("input");
    slider.type = "range";
    slider.min = "0";
    slider.value = "0";
    slider.setAttribute("aria-label", "Execution step");
    slider.className = "lab-slider";
    const counter = element("p", "", "lab-small");
    const event = element("p", "Choose an example to begin.", "lab-event");
    event.setAttribute("aria-live", "polite");
    const frames = element("div", undefined, "lab-frames");
    const functions = element("div", undefined, "lab-functions");
    const data = element("div", undefined, "lab-data");
    const diagramTools = element("div", undefined, "lab-toolbar lab-zoom");
    const zoomOut = element("button", "−");
    zoomOut.setAttribute("aria-label", "Zoom out");
    const fit = element("button", "Fit diagram");
    const zoomIn = element("button", "+");
    zoomIn.setAttribute("aria-label", "Zoom in");
    diagramTools.append(zoomOut, fit, zoomIn);
    const diagram = element("div", undefined, "lab-diagram");
    diagram.setAttribute("aria-label", "Interactive environment diagram");
    const legend = element("p", "Arrows point to enclosing environments. The green outline marks the current frame. Click a frame or function to inspect it.", "lab-small");
    const reduction = element("div", undefined, "lab-reduction");
    const priorTerm = element("pre", "", "lab-prior-term");
    const currentTerm = element("pre", "", "lab-current-term");
    reduction.append(element("h3", "Previous expression"), priorTerm,
      element("h3", "Current expression"), currentTerm,
      element("p", "Highlighted text changed in this step. Arguments reduce from left to right before a function is applied.", "lab-small"));
    const inspector = element("details", undefined, "lab-inspector");
    inspector.append(element("summary", "Inspect bindings and closures"), frames, functions);
    const timeline = element("details", undefined, "lab-timeline");
    const events = element("ol");
    timeline.append(element("summary", "Execution history"), events);
    diagramPanel.append(controls, slider, counter, event, diagramTools, diagram, legend, reduction, inspector, data, timeline);
    columns.append(editorPanel, diagramPanel);
    box.append(modes, toolbar, hint, columns);
    box.querySelectorAll("button").forEach(button => { button.type = "button"; });

    function highlightLine() {
      const step = history && history.steps[position];
      if (!step || !step.line) { editor.style.backgroundImage = "none"; return; }
      const style = getComputedStyle(editor);
      const top = parseFloat(style.paddingTop) + (step.line - 1) * parseFloat(style.lineHeight) - editor.scrollTop;
      const bottom = top + parseFloat(style.lineHeight);
      editor.style.backgroundImage = `linear-gradient(to bottom, transparent ${top}px, var(--lab-highlight) ${top}px, var(--lab-highlight) ${bottom}px, transparent ${bottom}px)`;
    }

    function numberLines() {
      gutter.textContent = editor.value.split("\n").map((_, i) => i + 1).join("\n");
      gutter.scrollTop = editor.scrollTop;
    }

    function populateExamples() {
      select.replaceChildren(placeholder);
      examples.filter(e => (e.mode || "environment") === mode).forEach(example => {
        const option = element("option", example.title);
        option.value = example.id;
        select.append(option);
      });
      select.value = selected && (selected.mode || "environment") === mode ? selected.id : "";
    }

    function syncMode() {
      box.dataset.mode = mode;
      environmentMode.setAttribute("aria-pressed", String(mode === "environment"));
      substitutionMode.setAttribute("aria-pressed", String(mode === "substitution"));
      diagramHeading.textContent = mode === "environment" ? "Environment diagram" : "Expression reductions";
      Array.from(chapter.options).forEach(option => { option.disabled = mode === "substitution" && Number(option.value) > 2; });
      populateExamples();
    }

    function switchMode(nextMode) {
      if (busy || nextMode === mode) return;
      stopPlayback();
      if (editor.value || selected) drafts[mode] = {
        source: editor.value, chapter: chapter.value, history, position, selected,
        hint: hint.textContent, status: status.textContent
      };
      mode = nextMode;
      syncMode();
      if (drafts[mode]) {
        const draft = drafts[mode];
        editor.value = draft.source;
        chapter.value = draft.chapter;
        history = draft.history;
        position = draft.position;
        selected = draft.selected;
        hint.textContent = draft.hint;
        status.textContent = draft.status;
        select.value = selected ? selected.id : "";
        numberLines();
        render();
      } else {
        const example = examples.find(e => (e.mode || "environment") === mode);
        if (example) useExample(example);
        else {
          selected = null;
          editor.value = "";
          chapter.value = mode === "substitution" ? "1" : "3";
          invalidate();
        }
      }
    }

    function focusFrame(id) {
      inspector.open = true;
      frames.querySelectorAll(".lab-frame").forEach(frame => {
        frame.classList.toggle("lab-selected", frame.dataset.frame === id);
        if (frame.dataset.frame === id) {
          frame.focus({ preventScroll: true });
          frame.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      });
    }

    function focusFunction(id) {
      inspector.open = true;
      const target = Array.from(functions.children).find(f => f.dataset.function === id);
      if (target) {
        target.focus({ preventScroll: true });
        target.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    }

    function resizeDiagram() {
      const picture = diagram.querySelector("svg");
      if (!picture) return;
      picture.style.width = zoom === null ? "100%" : Math.round(Number(picture.getAttribute("width")) * zoom) + "px";
      picture.style.height = "auto";
      fit.textContent = zoom === null ? "Fit diagram" : Math.round(zoom * 100) + "% · Fit";
    }

    function drawDiagram(step) {
      diagram.replaceChildren();
      if (!step || !step.diagram) {
        diagram.append(element("p", "Run or step through a program to see its environment.", "lab-small"));
        return;
      }
      const parsed = new DOMParser().parseFromString(step.diagram, "image/svg+xml");
      const picture = document.importNode(parsed.documentElement, true);
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = step.message;
      picture.prepend(title);
      picture.setAttribute("aria-label", step.message);
      diagram.append(picture);
      resizeDiagram();
    }

    function drawReduction(step, old) {
      const before = old && old.expression || "";
      const after = step && step.expression || "";
      priorTerm.textContent = before || "No earlier expression.";
      currentTerm.replaceChildren();
      if (!after) { currentTerm.textContent = "Step forward to reduce an expression."; return; }
      let start = 0, end = 0;
      while (start < before.length && start < after.length && before[start] === after[start]) start++;
      while (end < before.length - start && end < after.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
      currentTerm.append(document.createTextNode(after.slice(0, start)));
      if (start < after.length - end) currentTerm.append(element("mark", after.slice(start, after.length - end)));
      currentTerm.append(document.createTextNode(after.slice(after.length - end)));
    }

    function frameLink(id) {
      const button = element("button", "↗ " + id, "lab-link");
      button.type = "button";
      button.addEventListener("click", () => focusFrame(id));
      return button;
    }

    function render() {
      const steps = history ? history.steps : [];
      const step = steps[position];
      [first, previous].forEach(b => { b.disabled = !step || position === 0; });
      next.disabled = !step || position === steps.length - 1;
      last.disabled = next.disabled;
      play.disabled = !step || steps.length < 2;
      slider.disabled = !step;
      slider.max = Math.max(0, steps.length - 1);
      slider.value = position;
      frames.replaceChildren();
      functions.replaceChildren();
      data.replaceChildren();
      counter.textContent = step ? `Step ${position + 1} of ${steps.length}` + (step.line ? ` · line ${step.line}` : "") : "";
      event.textContent = step ? step.message : "Edit your program, then press Run code.";
      output.textContent = step && step.output ? step.output : "No output yet.";
      error.hidden = !(history && history.error);
      error.textContent = history && history.error || "";
      const environment = mode === "environment";
      diagram.hidden = diagramTools.hidden = legend.hidden = inspector.hidden = !environment;
      reduction.hidden = environment;
      [zoomOut, zoomIn, fit].forEach(button => { button.disabled = !step || !step.diagram; });
      events.replaceChildren();
      steps.forEach((entry, index) => {
        const li = element("li");
        const button = element("button", `${index + 1}. ${entry.message}`);
        button.type = "button";
        if (index === position) button.setAttribute("aria-current", "step");
        button.addEventListener("click", () => { stopPlayback(); move(index); });
        li.append(button);
        events.append(li);
      });
      highlightLine();
      drawDiagram(step);
      const old = position > 0 ? steps[position - 1] : null;
      drawReduction(step, old);
      if (!step) return;
      step.frames.forEach(frame => {
        const card = element("div", undefined, "lab-frame" + (frame.current ? " lab-current" : ""));
        card.tabIndex = -1;
        card.dataset.frame = frame.id;
        const header = element("div", undefined, "lab-frame-title");
        header.append(element("strong", frame.id));
        if (frame.current) header.append(element("span", "current", "lab-badge"));
        card.append(header, element("div", frame.call, "lab-small"));
        const parent = element("p", "Enclosing: ", "lab-small");
        if (frame.parent === "built-ins env") parent.append(element("span", frame.parent));
        else parent.append(frameLink(frame.parent));
        card.append(parent);
        const table = element("table");
        table.setAttribute("aria-label", "Bindings in " + frame.id);
        const body = element("tbody");
        frame.bindings.forEach(binding => {
          const row = element("tr");
          const was = old && old.frames.find(f => f.id === frame.id);
          const previousValue = was && was.bindings.find(b => b.name === binding.name);
          if (!previousValue || previousValue.value !== binding.value) {
            row.className = "lab-changed";
            row.title = previousValue ? "Previously: " + previousValue.value : "New binding";
          }
          const name = element("th", binding.name);
          name.scope = "row";
          const value = element("td");
          if (binding.function) {
            const button = element("button", binding.value, "lab-link");
            button.type = "button";
            button.addEventListener("click", () => focusFunction(binding.function));
            value.append(button);
          } else value.append(element("code", binding.value));
          row.append(name, value);
          body.append(row);
        });
        table.append(body);
        card.append(frame.bindings.length ? table : element("p", "No bindings yet.", "lab-small"));
        frames.append(card);
      });
      if (step.functions.length) functions.append(element("h3", "Function objects"));
      step.functions.forEach(fn => {
        const card = element("div", undefined, "lab-function");
        card.dataset.function = fn.id;
        card.tabIndex = -1;
        card.append(element("strong", fn.id + " (" + fn.params.join(", ") + ")"),
          element("code", "line " + fn.line + ": " + fn.source));
        const saved = element("span", "Remembers ");
        saved.append(frameLink(fn.env));
        card.append(saved);
        functions.append(card);
      });
      if (step.data.length) data.append(element("h3", "Pairs and lists"));
      step.data.forEach(item => {
        const figure = element("figure");
        const image = element("img");
        image.alt = "Box-and-pointer diagram of " + item.label;
        image.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(item.svg);
        figure.append(element("figcaption", item.label), image);
        data.append(figure);
      });
    }

    function setBusy(value) {
      busy = value;
      run.disabled = reset.disabled = select.disabled = chapter.disabled = editor.disabled = value;
      stop.disabled = !value;
      environmentMode.disabled = substitutionMode.disabled = value;
    }

    function useExample(example) {
      if (!example) return;
      stopPlayback();
      selected = example;
      select.value = example.id;
      editor.value = example.source;
      editor.scrollTop = 0;
      numberLines();
      chapter.value = example.chapter;
      hint.textContent = example.hint;
      history = example.trace;
      position = 0;
      status.textContent = example.trace
        ? "Example ready. Step through it or edit and run your own version."
        : "Book example ready. Run code to trace it.";
      render();
    }

    function invalidate() {
      untouched = false;
      stopPlayback();
      history = null;
      position = 0;
      status.textContent = "Code changed. Run code to trace this version.";
      numberLines();
      render();
    }

    function move(target) {
      if (!history) return;
      position = Math.max(0, Math.min(history.steps.length - 1, target));
      if (position === history.steps.length - 1) stopPlayback();
      const line = history.steps[position].line;
      const height = parseFloat(getComputedStyle(editor).lineHeight);
      const top = (line - 1) * height;
      if (line && (top < editor.scrollTop || top + height * 2 > editor.scrollTop + editor.clientHeight)) {
        editor.scrollTop = Math.max(0, top - height * 3);
      }
      render();
    }

    function stopWorker(message) {
      if (worker) worker.terminate();
      worker = null;
      clearTimeout(timeout);
      setBusy(false);
      status.textContent = message;
    }

    function runCode() {
      if (busy) return;
      untouched = false;
      stopPlayback();
      const cached = examples.find(e => e.source === editor.value && e.chapter === Number(chapter.value) && (e.mode || "environment") === mode);
      if (cached) { useExample(cached); return; }
      history = null;
      render();
      setBusy(true);
      status.textContent = "Loading Python…";
      try {
        if (!worker) {
          worker = new Worker(new URL("playground-worker.js", assets), { type: "module" });
          worker.onmessage = ({ data }) => {
            if (!alive) return;
            if (data.type === "status") { status.textContent = data.message; return; }
            clearTimeout(timeout);
            setBusy(false);
            if (data.type === "error") {
              stopWorker(data.message);
              return;
            }
            history = data.trace;
            position = 0;
            status.textContent = history.error ? "Program stopped. Inspect the trace and the error below." : "Trace ready. Step forward to follow execution.";
            render();
          };
          worker.onerror = () => stopWorker("Python could not load. Check your connection, then try Run code again. The examples still work.");
        }
        worker.postMessage({ source: editor.value, chapter: Number(chapter.value), mode });
        timeout = setTimeout(() => stopWorker("Run stopped after 90 seconds. Check your connection or try a smaller program."), 90000);
      } catch (error) { stopWorker("Could not start Python: " + error.message); }
    }

    select.addEventListener("change", () => useExample(examples.find(e => e.id === select.value)));
    environmentMode.addEventListener("click", () => switchMode("environment"));
    substitutionMode.addEventListener("click", () => switchMode("substitution"));
    reset.addEventListener("click", () => { if (selected) useExample(selected); });
    chapter.addEventListener("change", invalidate);
    editor.addEventListener("input", invalidate);
    editor.addEventListener("scroll", () => { gutter.scrollTop = editor.scrollTop; highlightLine(); });
    editor.addEventListener("keydown", e => {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = editor.selectionStart, end = editor.selectionEnd;
        editor.setRangeText("    ", start, end, "end");
        invalidate();
      }
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runCode(); }
    });
    run.addEventListener("click", runCode);
    stop.addEventListener("click", () => stopWorker("Stopped. Edit your code or run again."));
    first.addEventListener("click", () => { stopPlayback(); move(0); });
    previous.addEventListener("click", () => { stopPlayback(); move(position - 1); });
    next.addEventListener("click", () => { stopPlayback(); move(position + 1); });
    last.addEventListener("click", () => { stopPlayback(); if (history) move(history.steps.length - 1); });
    diagram.addEventListener("click", e => {
      const frame = e.target.closest("[data-frame]");
      const fn = e.target.closest("[data-function]");
      if (frame) focusFrame(frame.dataset.frame);
      else if (fn) focusFunction(fn.dataset.function);
    });
    diagram.addEventListener("keydown", e => {
      if ((e.key === "Enter" || e.key === " ") && e.target.closest("[data-frame], [data-function]")) {
        e.preventDefault();
        e.target.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      }
    });
    zoomIn.addEventListener("click", () => { zoom = Math.min(3, (zoom === null ? .75 : zoom) + .25); resizeDiagram(); });
    zoomOut.addEventListener("click", () => { zoom = Math.max(.25, (zoom === null ? .75 : zoom) - .25); resizeDiagram(); });
    fit.addEventListener("click", () => { zoom = null; resizeDiagram(); });
    speed.addEventListener("change", () => {
      if (timer) { stopPlayback(); play.click(); }
    });
    slider.addEventListener("input", () => { stopPlayback(); move(Number(slider.value)); });
    play.addEventListener("click", () => {
      if (timer) { stopPlayback(); return; }
      if (position === history.steps.length - 1) move(0);
      play.textContent = "Ⅱ Pause";
      timer = setInterval(() => move(position + 1), Number(speed.value));
    });
    // Restore a book example before waiting for any network request.
    try {
      const imported = JSON.parse(sessionStorage.getItem("sicpfuf-lab-import") || "null");
      if (imported && typeof imported.source === "string") {
        sessionStorage.removeItem("sicpfuf-lab-import");
        mode = imported.mode === "substitution" ? "substitution" : "environment";
        useExample({
          id: "", source: imported.source,
          mode,
          chapter: [1, 2, 3, 4].includes(imported.chapter) ? imported.chapter : 3,
          hint: "This program came from the book. Predict what happens, then run it and follow the bindings.",
          trace: null
        });
        untouched = false;
      }
    } catch (_) { /* Storage is optional. */ }
    syncMode();
    render();
    try {
      const response = await fetch(new URL("playground-traces.json", assets));
      if (!response.ok) throw new Error("Examples could not load");
      examples = await response.json();
      if (!alive) return;
      populateExamples();
      // A slow examples request must not replace code the reader has started editing.
      if (untouched && !busy) useExample(examples.find(e => (e.mode || "environment") === mode));
      else if (!selected) hint.textContent = "Run your code to follow its bindings, or choose an example above.";
    } catch (_) {
      if (!alive) return;
      hint.textContent = "Examples could not load. You can still write code and press Run code.";
      if (untouched && !busy) status.textContent = "Ready for your code.";
    }
  }

  if (window.document$ && window.document$.subscribe) window.document$.subscribe(setup);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", setup);
  else setup();
})();
