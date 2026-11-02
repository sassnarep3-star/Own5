// Own5 dashboard: client-side table filtering. No external dependencies.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.table-tools input[data-filter]').forEach(function (input) {
    var target = document.getElementById(input.getAttribute('data-filter'));
    if (!target) return;
    var count = input.parentElement.querySelector('.count');
    var rows = Array.prototype.slice.call(target.querySelectorAll('tbody tr'));
    var update = function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        tr.style.display = hit ? '' : 'none';
        if (hit) shown++;
      });
      if (count) count.textContent = shown + ' / ' + rows.length + ' rows';
    };
    input.addEventListener('input', update);
    update();
  });
  // mark active nav link
  var path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav.main a').forEach(function (a) {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
});
