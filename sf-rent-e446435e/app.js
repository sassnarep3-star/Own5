"use strict";
document.querySelectorAll("input[data-search]").forEach(function (input) {
  var id = input.getAttribute("data-search");
  var table = document.getElementById(id);
  if (!table) return;
  var count = document.querySelector('[data-count="' + id + '"]');
  var empty = table.closest("section").querySelector(".empty");
  var total = table.querySelectorAll("tbody tr").length;
  input.addEventListener("input", function () {
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    table.querySelectorAll("tbody tr").forEach(function (tr) {
      var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
      tr.hidden = !hit;
      if (hit) shown++;
    });
    if (count) count.textContent = shown + " of " + total + " entries";
    if (empty) empty.hidden = shown !== 0;
  });
});
document.querySelectorAll("select[data-filter]").forEach(function (sel) {
  var id = sel.getAttribute("data-filter");
  var table = document.getElementById(id);
  if (!table) return;
  sel.addEventListener("change", function () {
    var v = sel.value;
    table.querySelectorAll("tbody tr").forEach(function (tr) {
      tr.hidden = !!v && tr.getAttribute("data-sev") !== v;
    });
  });
});
document.querySelectorAll("button[data-export]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var table = document.getElementById(btn.getAttribute("data-export"));
    if (!table) return;
    var lines = [];
    table.querySelectorAll("tr").forEach(function (tr) {
      if (tr.hidden) return;
      var cells = [];
      tr.querySelectorAll("th,td").forEach(function (c) {
        cells.push('"' + c.textContent.trim().replace(/"/g, '""') + '"');
      });
      lines.push(cells.join(","));
    });
    var blob = new Blob([lines.join("\n")], { type: "text/csv" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = btn.getAttribute("data-export") + ".csv";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });
});
