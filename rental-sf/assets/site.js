// Client-side table filter. No dependencies; no network calls.
document.querySelectorAll('input[data-filter-target]').forEach(function (input) {
  var target = document.getElementById(input.getAttribute('data-filter-target'));
  if (!target) return;
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    target.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
});
// Stamp "last checked" where marked.
document.querySelectorAll('[data-retrieval-date]').forEach(function (el) {
  el.textContent = el.getAttribute('data-retrieval-date');
});
