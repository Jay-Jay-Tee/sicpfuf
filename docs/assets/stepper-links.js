/* Send a textbook program to the website stepper, preserving the project URL. */
(function () {
  "use strict";
  const destination = new URL("../playground/", document.currentScript.src);
  // The textbook and embedded UI may have separate storage in an editor tab.
  // Carry an import through both the iframe and the full-tab link instead.
  if (new URLSearchParams(location.hash.slice(1)).has("program")) {
    for (const node of document.querySelectorAll("iframe.stepper-frame, a.stepper-fullscreen")) {
      const property = node.tagName === "IFRAME" ? "src" : "href";
      const url = new URL(node.getAttribute(property), location.href);
      url.hash = location.hash;
      node[property] = url.href;
    }
  }
  document.querySelectorAll(".md-content .highlight").forEach(block => {
    const code = block.querySelector("code"), title = block.querySelector(".filename");
    const chapter = title && title.textContent.match(/§([1-4])/);
    if (!code || !chapter || /--with|--out/.test(title.textContent) || /from (rune|curve|sound) import/.test(code.textContent)) return;
    const program = {
      source: code.textContent, chapter: Number(chapter[1]),
      mode: /--subst/.test(title.textContent) ? "substitution" : "environment",
      typed: /--typed/.test(title.textContent)
    };
    const link = document.createElement("a");
    const url = new URL(destination.href);
    url.hash = new URLSearchParams({ program: JSON.stringify(program) }).toString();
    link.href = url.href;
    link.className = "stepper-explore";
    link.textContent = "Explore step by step →";
    link.addEventListener("click", () => {
      try {
        sessionStorage.setItem("sicpfuf-stepper-import", JSON.stringify(program));
      } catch (_) { /* The stepper also works without browser storage. */ }
    });
    block.append(link);
  });
})();
