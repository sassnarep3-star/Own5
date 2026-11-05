(function () {
  "use strict";
  function filter(input) {
    var table = document.getElementById(input.getAttribute("data-search"));
    if (!table || !table.tBodies.length) return;
    var q = input.value.trim().toLowerCase();
    var rows = table.tBodies[0].rows;
    var visible = 0;
    for (var i = 0; i < rows.length; i++) {
      var show = !q || rows[i].textContent.toLowerCase().indexOf(q) !== -1;
      rows[i].hidden = !show;
      if (show) visible++;
    }
    var count = document.querySelector('[data-count="' + input.getAttribute("data-search") + '"]');
    if (count) count.textContent = visible + " / " + rows.length + " rows";
  }
  document.addEventListener("input", function (ev) {
    if (ev.target && ev.target.matches && ev.target.matches("input[data-search]")) filter(ev.target);
  });
})();
