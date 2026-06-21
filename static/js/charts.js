// Renders the three report charts from the JSON embedded by report.html.
(function () {
  var el = document.getElementById("chart-data");
  if (!el || typeof Chart === "undefined") return;
  var data = JSON.parse(el.textContent);

  var INK = "#1a1f2e";
  var ACCENT = "#5b6cff";
  var BRAND = "#16a36a";
  var PALETTE = ["#5b6cff", "#16a36a", "#f0a500", "#d64545", "#8b5cf6", "#0ea5e9"];

  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
  Chart.defaults.color = "#6b7280";

  function bar(id, labels, values, color) {
    var ctx = document.getElementById(id);
    if (!ctx) return;
    new Chart(ctx, {
      type: "bar",
      data: { labels: labels, datasets: [{ data: values, backgroundColor: color, borderRadius: 6 }] },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: "#eef0f3" } }, x: { grid: { display: false } } },
        maintainAspectRatio: false,
      },
    });
  }

  // Visibility by engine
  bar("enginesChart", data.engines.labels, data.engines.values, ACCENT);

  // Share of voice — client highlighted, competitors muted
  var sovCtx = document.getElementById("sovChart");
  if (sovCtx) {
    var colors = data.sov.labels.map(function (_, i) { return i === 0 ? BRAND : "#c7ccd6"; });
    new Chart(sovCtx, {
      type: "bar",
      data: {
        labels: data.sov.labels,
        datasets: [{ data: data.sov.values.map(function (v) { return +(v * 100).toFixed(1); }), backgroundColor: colors, borderRadius: 6 }],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.parsed.x + "% share of voice"; } } } },
        scales: { x: { beginAtZero: true, grid: { color: "#eef0f3" }, ticks: { callback: function (v) { return v + "%"; } } }, y: { grid: { display: false } } },
        maintainAspectRatio: false,
      },
    });
  }

  // Sessions by channel
  var chCtx = document.getElementById("channelChart");
  if (chCtx) {
    new Chart(chCtx, {
      type: "doughnut",
      data: { labels: data.channels.labels, datasets: [{ data: data.channels.values, backgroundColor: PALETTE }] },
      options: { plugins: { legend: { position: "right", labels: { boxWidth: 12 } } }, maintainAspectRatio: false },
    });
  }
})();

function approve(btn) {
  btn.textContent = "Sent to client ✓";
  btn.disabled = true;
  btn.style.background = "#0e7a4f";
}
