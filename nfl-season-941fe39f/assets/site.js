// Minimal site behaviour: requirement filter and table row search. No dependencies.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.filters').forEach(function (box) {
    var target = document.getElementById(box.getAttribute('data-filter-for'));
    if (!target) return;
    box.querySelectorAll('button.f').forEach(function (btn) {
      btn.addEventListener('click', function () {
        box.querySelectorAll('button.f').forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on');
        var k = btn.getAttribute('data-k');
        target.querySelectorAll('tbody tr').forEach(function (tr) {
          tr.style.display = (k === 'all' || tr.getAttribute('data-s') === k) ? '' : 'none';
        });
      });
    });
  });
});
