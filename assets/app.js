'use strict';
// Progressive enhancement only. Every finding and link is present without JavaScript.
const tables = document.querySelectorAll('table');
for (const table of tables) {
  const search = document.querySelector(`[data-search="${table.id}"]`);
  const filter = document.querySelector(`[data-filter="${table.id}"]`);
  const count = document.querySelector(`[data-count="${table.id}"]`);
  const rows = [...table.tBodies[0].rows];
  function update() {
    const term = (search?.value || '').trim().toLocaleLowerCase();
    const category = filter?.value || '';
    let visible = 0;
    for (const row of rows) {
      const matchesSearch = row.textContent.toLocaleLowerCase().includes(term);
      const matchesCategory = !category || [...row.cells].some(cell => cell.textContent.trim() === category || [...cell.querySelectorAll('.badge')].some(b => b.textContent === category));
      row.hidden = !(matchesSearch && matchesCategory);
      if (!row.hidden) visible++;
    }
    count.textContent = `${visible} of ${rows.length} entries`;
    count.setAttribute('aria-live', 'polite');
    table.closest('.table-panel').querySelector('.empty').hidden = visible !== 0;
  }
  search?.addEventListener('input', update);
  filter?.addEventListener('change', update);
  document.querySelector(`[data-export="${table.id}"]`)?.addEventListener('click', () => {
    // Export filtered rows, actual source URLs, and empty cells (never substitute zero).
    const quote = value => {
      // Prevent spreadsheet formula execution in any future untrusted text fields.
      const safe = /^[=+@\-\t\r]/.test(value) ? `'${value}` : value;
      return `"${safe.replaceAll('"', '""')}"`;
    };
    const lines = [table.tHead.rows[0], ...rows.filter(row => !row.hidden)].map(row =>
      [...row.cells].map(cell => {
        const links = [...cell.querySelectorAll('a')];
        const value = links.length ? links.map(a => `${a.textContent.trim()} ${a.href}`).join('; ') : cell.textContent.trim().replace(/\s+/g, ' ');
        return quote(value);
      }).join(',')
    );
    const blob = new Blob(['\uFEFF' + lines.join('\r\n')], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `own5-${table.id}-2026-11-02.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
