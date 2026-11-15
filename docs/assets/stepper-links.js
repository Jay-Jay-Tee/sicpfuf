/* Send a textbook program to the website stepper, preserving the project URL. */
(function () {
  "use strict";
  const destination = new URL("../playground/", document.currentScript.src);
  document.querySelectorAll(".md-content .highlight").forEach(block => {
    const code = block.querySelector("code"), title = block.querySelector(".filename");
    const chapter = title && title.textContent.match(/§([1-4])/);
    if (!code || !chapter || /--with|--out/.test(title.textContent) || /from (rune|curve|sound) import/.test(code.textContent)) return;
    const link = document.createElement("a");
    link.href = destination.href;
    link.className = "stepper-explore";
    link.textContent = "Explore step by step →";
    link.addEventListener("click", () => {
      try {
        sessionStorage.setItem("sicpfuf-stepper-import", JSON.stringify({
          source: code.textContent, chapter: Number(chapter[1]),
          mode: /--subst/.test(title.textContent) ? "substitution" : "environment",
          typed: /--typed/.test(title.textContent)
        }));
      } catch (_) { /* The stepper also works without browser storage. */ }
    });
    block.append(link);
  });
})();
