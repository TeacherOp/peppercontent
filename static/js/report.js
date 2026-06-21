// Report edit mode: toggle the Claude-written narrative into editable fields,
// make the action bar sticky while editing, and save changes back to the store.
// Recommendations can also be added, removed, and re-prioritised.
(function () {
  var bar = document.getElementById("actionbar");
  var btn = document.getElementById("edit-btn");
  if (!bar || !btn) return; // only on saved reports

  var reportId = bar.dataset.reportId;
  var status = document.getElementById("save-status");
  var proseFields = Array.prototype.slice.call(document.querySelectorAll("[data-edit]"));
  var recList = document.getElementById("rec-list");
  var recAdd = document.getElementById("rec-add");
  var PRIORITIES = ["High", "Medium", "Low"];
  var editing = false;

  function setStatus(t) { if (status) status.textContent = t; }
  function recItems() {
    return recList ? Array.prototype.slice.call(recList.querySelectorAll(".rec-item")) : [];
  }

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

  function enterEdit() {
    editing = true;
    document.body.classList.add("editing");
    bar.classList.add("sticky");
    proseFields.forEach(function (el) { el.setAttribute("contenteditable", "true"); });
    recItems().forEach(function (li) { toggleRec(li, true); setPriority(li, li.dataset.priority || "Medium"); });
    btn.textContent = "Save report";
    btn.classList.remove("ghost");
    setStatus("Editing — make your changes");
    if (proseFields[0]) proseFields[0].focus();
  }

  function exitEdit() {
    editing = false;
    document.body.classList.remove("editing");
    bar.classList.remove("sticky");
    proseFields.forEach(function (el) { el.removeAttribute("contenteditable"); });
    recItems().forEach(function (li) { toggleRec(li, false); setPriority(li, li.dataset.priority || "Medium"); });
    btn.textContent = "Edit";
    btn.classList.add("ghost");
  }

  function collect() {
    var edits = {};
    proseFields.forEach(function (el) { edits[el.dataset.edit] = (el.innerText || "").trim(); });
    edits.recommendations = recItems().map(function (li) {
      return {
        priority: li.dataset.priority || "Medium",
        title: (li.querySelector(".rec-title").innerText || "").trim(),
        detail: (li.querySelector(".rec-detail").innerText || "").trim(),
      };
    }).filter(function (r) { return r.title || r.detail; });
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

  // Add a new (empty) recommendation in edit mode.
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

  // Remove a recommendation, or cycle its priority by clicking the badge.
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

  btn.addEventListener("click", function () { if (editing) save(); else enterEdit(); });

  window.addEventListener("beforeunload", function (e) {
    if (editing) { e.preventDefault(); e.returnValue = ""; }
  });
})();
