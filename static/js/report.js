// Report edit mode.
//   - Apply any saved section order on load (for everyone viewing the report).
//   - In edit mode: edit narrative text, add/remove text boxes in the executive
//     summary and section overviews, add/remove/reprioritise recommendations,
//     and move whole sections up/down. Save persists everything to the store.
(function () {
  var article = document.querySelector(".report");

  // --- apply saved section order (runs for all viewers) ------------------
  (function applyOrder() {
    var el = document.getElementById("section-order");
    if (!el || !article) return;
    var order;
    try { order = JSON.parse(el.textContent); } catch (e) { return; }
    if (!order || !order.length) return;
    var footer = article.querySelector(".report-foot");
    order.forEach(function (id) {
      var sec = article.querySelector('[data-section="' + id + '"]');
      if (sec) article.insertBefore(sec, footer);
    });
  })();

  var bar = document.getElementById("actionbar");
  var btn = document.getElementById("edit-btn");
  if (!bar || !btn) return; // editing only on saved reports

  var reportId = bar.dataset.reportId;
  var status = document.getElementById("save-status");
  var recList = document.getElementById("rec-list");
  var recAdd = document.getElementById("rec-add");
  var hlList = document.getElementById("highlight-list");
  var hlAdd = document.getElementById("highlight-add");
  var PRIORITIES = ["High", "Medium", "Low"];
  var editing = false;

  function setStatus(t) { if (status) status.textContent = t; }
  function editableEls() { return Array.prototype.slice.call(document.querySelectorAll(".ed-block, .hl-title, .hl-detail")); }
  function recItems() { return recList ? Array.prototype.slice.call(recList.querySelectorAll(".rec-item")) : []; }
  function hlItems() { return hlList ? Array.prototype.slice.call(hlList.querySelectorAll(".highlight")) : []; }
  function sections() { return Array.prototype.slice.call(article.querySelectorAll("[data-section]")); }

  function toggleRec(li, on) {
    var t = li.querySelector(".rec-title");
    var d = li.querySelector(".rec-detail");
    if (on) { t.setAttribute("contenteditable", "true"); d.setAttribute("contenteditable", "true"); }
    else { t.removeAttribute("contenteditable"); d.removeAttribute("contenteditable"); }
  }
  function setPriority(li, prio) {
    li.dataset.priority = prio;
    var badge = li.querySelector("[data-prio-badge]");
    if (badge) {
      badge.textContent = prio;
      badge.className = "prio prio-" + prio.toLowerCase();
      badge.title = editing ? "Click to change priority" : "";
    }
  }

  // section up/down tools, injected only in edit mode
  function addSectionTools() {
    sections().forEach(function (sec) {
      if (sec.querySelector(":scope > .section-tools")) return;
      var tools = document.createElement("div");
      tools.className = "section-tools no-print";
      tools.innerHTML =
        '<button type="button" data-move="up" aria-label="Move section up">▲</button>' +
        '<button type="button" data-move="down" aria-label="Move section down">▼</button>';
      sec.insertBefore(tools, sec.firstChild);
    });
  }
  function removeSectionTools() {
    article.querySelectorAll(".section-tools").forEach(function (t) { t.remove(); });
  }

  function enterEdit() {
    editing = true;
    document.body.classList.add("editing");
    bar.classList.add("sticky");
    editableEls().forEach(function (el) { el.setAttribute("contenteditable", "true"); });
    recItems().forEach(function (li) { toggleRec(li, true); setPriority(li, li.dataset.priority || "Medium"); });
    addSectionTools();
    btn.textContent = "Save report";
    btn.classList.remove("ghost");
    setStatus("Editing — make your changes");
  }

  function exitEdit() {
    editing = false;
    document.body.classList.remove("editing");
    bar.classList.remove("sticky");
    editableEls().forEach(function (el) { el.removeAttribute("contenteditable"); });
    recItems().forEach(function (li) { toggleRec(li, false); setPriority(li, li.dataset.priority || "Medium"); });
    removeSectionTools();
    btn.textContent = "Edit";
    btn.classList.add("ghost");
  }

  function collect() {
    var edits = { section_insights: {} };

    // highlights (full list)
    edits.highlights = hlItems().map(function (h) {
      return {
        title: (h.querySelector(".hl-title").innerText || "").trim(),
        detail: (h.querySelector(".hl-detail").innerText || "").trim(),
      };
    }).filter(function (h) { return h.title || h.detail; });

    // text-box groups: executive summary + section overviews
    document.querySelectorAll(".block-group").forEach(function (g) {
      var texts = Array.prototype.slice.call(g.querySelectorAll(".ed-block"))
        .map(function (el) { return (el.innerText || "").trim(); })
        .filter(Boolean);
      var key = g.dataset.group;
      if (key === "executive_summary") edits.executive_summary = texts;
      else if (key.indexOf("section_insights.") === 0) edits.section_insights[key.slice(17)] = texts;
    });

    // recommendations (full list)
    edits.recommendations = recItems().map(function (li) {
      return {
        priority: li.dataset.priority || "Medium",
        title: (li.querySelector(".rec-title").innerText || "").trim(),
        detail: (li.querySelector(".rec-detail").innerText || "").trim(),
      };
    }).filter(function (r) { return r.title || r.detail; });

    // section order
    edits.section_order = sections().map(function (s) { return s.dataset.section; });
    return edits;
  }

  function save() {
    btn.disabled = true;
    setStatus("Saving…");
    fetch("/reports/" + reportId + "/narrative", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collect()),
    })
      .then(function (r) { if (!r.ok) throw new Error("save failed"); return r.json(); })
      .then(function () { exitEdit(); setStatus("Saved ✓"); })
      .catch(function () { setStatus("Couldn't save — try again"); })
      .finally(function () { btn.disabled = false; });
  }

  function newTextBlock() {
    var wrap = document.createElement("div");
    wrap.className = "text-block";
    wrap.innerHTML =
      '<p class="insight ed-block" contenteditable="true"></p>' +
      '<button type="button" class="block-remove no-print" aria-label="Remove text box">✕</button>';
    return wrap;
  }

  // add / remove text boxes inside any group
  document.querySelectorAll(".block-group").forEach(function (g) {
    g.addEventListener("click", function (e) {
      if (!editing) return;
      if (e.target.closest(".block-add")) {
        var block = newTextBlock();
        g.insertBefore(block, g.querySelector(".block-add"));
        block.querySelector(".ed-block").focus();
      } else if (e.target.closest(".block-remove")) {
        e.target.closest(".text-block").remove();
      }
    });
  });

  // highlights: add / remove
  if (hlAdd) {
    hlAdd.addEventListener("click", function () {
      if (!editing) return;
      var div = document.createElement("div");
      div.className = "highlight";
      div.innerHTML =
        '<strong class="hl-title" contenteditable="true"></strong>' +
        '<span class="hl-detail" contenteditable="true"></span>' +
        '<button type="button" class="hl-remove no-print" aria-label="Remove highlight">✕</button>';
      hlList.appendChild(div);
      div.querySelector(".hl-title").focus();
    });
  }
  if (hlList) {
    hlList.addEventListener("click", function (e) {
      if (!editing) return;
      var remove = e.target.closest(".hl-remove");
      if (remove) remove.closest(".highlight").remove();
    });
  }

  // recommendations: add / remove / cycle priority
  if (recAdd) {
    recAdd.addEventListener("click", function () {
      if (!editing) return;
      var li = document.createElement("li");
      li.className = "rec-item";
      li.dataset.priority = "Medium";
      li.innerHTML =
        '<span class="prio prio-medium" data-prio-badge>Medium</span>' +
        '<div class="rec-body"><strong class="rec-title"></strong><p class="rec-detail"></p></div>' +
        '<button type="button" class="rec-remove no-print" aria-label="Remove recommendation">✕</button>';
      recList.appendChild(li);
      toggleRec(li, true);
      setPriority(li, "Medium");
      li.querySelector(".rec-title").focus();
    });
  }
  if (recList) {
    recList.addEventListener("click", function (e) {
      if (!editing) return;
      var remove = e.target.closest(".rec-remove");
      if (remove) { remove.closest(".rec-item").remove(); return; }
      var badge = e.target.closest("[data-prio-badge]");
      if (badge) {
        var li = badge.closest(".rec-item");
        var i = PRIORITIES.indexOf(li.dataset.priority || "Medium");
        setPriority(li, PRIORITIES[(i + 1) % PRIORITIES.length]);
      }
    });
  }

  // move sections up / down
  article.addEventListener("click", function (e) {
    var moveBtn = e.target.closest("[data-move]");
    if (!moveBtn || !editing) return;
    var sec = moveBtn.closest("[data-section]");
    var dir = moveBtn.dataset.move;
    if (dir === "up") {
      var prev = sec.previousElementSibling;
      while (prev && !prev.hasAttribute("data-section")) prev = prev.previousElementSibling;
      if (prev) sec.parentNode.insertBefore(sec, prev);
    } else {
      var next = sec.nextElementSibling;
      while (next && !next.hasAttribute("data-section")) next = next.nextElementSibling;
      if (next) sec.parentNode.insertBefore(next, sec);
    }
    sec.scrollIntoView({ block: "nearest" });
  });

  btn.addEventListener("click", function () { if (editing) save(); else enterEdit(); });
  window.addEventListener("beforeunload", function (e) {
    if (editing) { e.preventDefault(); e.returnValue = ""; }
  });
})();
