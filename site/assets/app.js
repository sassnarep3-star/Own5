(function () {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.overlay');
  const menu = document.querySelector('.menu-btn');
  function closeNav() { if (sidebar) sidebar.classList.remove('open'); if (overlay) overlay.classList.remove('show'); }
  if (menu) menu.addEventListener('click', function () { sidebar.classList.toggle('open'); overlay.classList.toggle('show'); });
  if (overlay) overlay.addEventListener('click', closeNav);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });
  document.querySelectorAll('[data-table-search]').forEach(function (input) {
    const card = input.closest('.table-card');
    const rows = Array.from(card.querySelectorAll('tbody tr'));
    const count = card.querySelector('.table-count');
    function update() {
      const query = input.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach(function (row) {
        const show = !query || row.textContent.toLowerCase().includes(query);
        row.hidden = !show;
        if (show) visible++;
      });
      if (count) count.textContent = visible + ' of ' + rows.length + ' rows';
    }
    input.addEventListener('input', update);
    update();
  });
})();
