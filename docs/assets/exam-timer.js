// Exam mode: a countdown clock for the mock papers.
// A page opts in with  <div id="exam-timer" data-minutes="120"></div>.
// While the clock runs, the solution toggles (details.solution) are hidden.
(function () {
  var tick = null;

  function setup() {
    if (tick) { clearInterval(tick); tick = null; }
    document.body.classList.remove("exam-running");
    var box = document.getElementById("exam-timer");
    if (!box || box.dataset.ready) { return; }
    box.dataset.ready = "1";
    var minutes = parseInt(box.dataset.minutes || "120", 10);
    var key = "sicpfuf-exam:" + location.pathname;
    var endsAt = parseInt(sessionStorage.getItem(key) || "0", 10);

    box.innerHTML = '<span class="time"></span>' +
      '<button type="button" data-act="start">Start ' + minutes + ' min</button>' +
      '<button type="button" data-act="stop">Stop and show solutions</button>' +
      '<span class="note"></span>';
    var time = box.querySelector(".time");
    var note = box.querySelector(".note");

    function show() {
      var running = endsAt > 0;
      document.body.classList.toggle("exam-running", running);
      var left = running ? Math.round((endsAt - Date.now()) / 1000) : minutes * 60;
      var late = left < 0;
      var s = Math.abs(left);
      time.textContent = (late ? "+" : "") + Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2);
      box.classList.toggle("late", late);
      note.textContent = !running ? "Solutions are visible. Start the clock to hide them."
        : late ? "Time is up. Finish your sentence, then stop the clock."
        : "Solutions are hidden while the clock runs.";
    }

    box.addEventListener("click", function (e) {
      var act = e.target && e.target.dataset ? e.target.dataset.act : null;
      if (act === "start") { endsAt = Date.now() + minutes * 60000; sessionStorage.setItem(key, String(endsAt)); }
      if (act === "stop") { endsAt = 0; sessionStorage.removeItem(key); }
      show();
    });
    show();
    tick = setInterval(show, 1000);
  }

  if (window.document$ && window.document$.subscribe) { window.document$.subscribe(setup); }
  else { document.addEventListener("DOMContentLoaded", setup); }
})();
