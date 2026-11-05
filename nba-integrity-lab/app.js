/* Optional local filtering. All tables remain readable without JavaScript. */
(() => {
  'use strict';
  document.querySelectorAll('[data-search]').forEach((input) => {
    const table = document.getElementById(input.dataset.search);
    const empty = document.querySelector(`[data-empty="${input.dataset.search}"]`);
    if (!table) return;
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const filter = () => {
      const query = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const show = row.textContent.toLocaleLowerCase().includes(query);
        row.hidden = !show;
        if (show) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
    };
    input.addEventListener('input', filter);
  });
})();
